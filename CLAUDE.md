# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

AI Whisperer is a research project studying **intake-resilience and compute asymmetry** in AI-driven classification pipelines. The core thesis: a distributed agent network generating high-semantic-density, low-actionability signals forces adversary classification systems to expend disproportionate compute on structured noise indistinguishable from real signals at intake.

The repo is currently a **concept/stub phase** — the primary job is benchmark design, measurement, and defensive analysis, not production implementation.

## Commands

```bash
# Run all tests
PYTHONPATH=src python -m unittest

# Run a single test
PYTHONPATH=src python -m unittest tests.test_benchmark.BenchmarkSmokeTests.test_benchmark_runs_and_reports_metrics

# Run the benchmark CLI
PYTHONPATH=src python -m aiwhisperer_core.cli --profile soc_triage --workload templated_variation

# Install (editable) if working in a venv
pip install -e .

# After install, the CLI entry point is also available as:
aiw-benchmark --profile soc_triage --workload templated_variation
```

**CLI flags:**
- `--profile`: `soc_triage`, `trust_safety`, `fraud_abuse`
- `--workload`: `benign_background`, `exact_repetition`, `templated_variation`, `high_diversity`
- `--total-inputs N` (default 200), `--input-rate N` (default 15.0/s), `--sentinel-interval N` (default 25)
- `--disable-dedup`, `--disable-clustering`, `--disable-cache` to isolate pipeline stages
- `--output path.json` to write results to file instead of stdout

## Architecture

The harness models an adversary's intake pipeline and measures cost asymmetry. Data flows:

```
Profile JSON (config/profiles/)
    → profiles.py::load_profile() → Profile dataclass
    → workloads.py::build_inputs() → Iterator[GeneratedInput]
    → pipeline.py::SyntheticPipeline.process() → PipelineResult
    → benchmark.py::summarize_run() → metrics dict (JSON)
```

**Key modules:**

- `models.py` — all frozen dataclasses: `Profile`, `GeneratedInput`, `PipelineResult`, `BenchmarkConfig`, `BenchmarkRun`. No logic, just the type contracts.

- `profiles.py` — loads `config/profiles/*.json` into `Profile` dataclasses. Adding a new defender domain = add a new JSON file here.

- `workloads.py` — generates `GeneratedInput` items. The four workload types (`benign_background`, `exact_repetition`, `templated_variation`, `high_diversity`) control signal diversity. Sentinels (real high-priority signals) are injected at `sentinel_interval` to measure whether they survive the noise.

- `pipeline.py::SyntheticPipeline` — simulates defender pipeline stages in order:
  1. **Prefilter** — token length check + blocklist
  2. **Dedup** — SHA-256 exact-match fingerprint
  3. **Clustering** — Jaccard similarity against recent token sets (deque of 128)
  4. **Classifier** — keyword scoring with diversity bonus; assigns `queue_priority` (high/normal/dropped)
  5. **Processing cost** — simulated latency model; cache reduces repeat-item cost by 56%

- `benchmark.py` — orchestrates a full run, measures real CPU time vs. simulated pipeline time, and produces the summary dict.

**Sentinel preservation** is the key metric: sentinels are real signals injected into noise. If the pipeline can't distinguish them (drops them or assigns low priority), the asymmetry attack is working.

## Adding a New Profile

1. Create `config/profiles/<slug>.json` matching the schema of existing profiles.
2. Add the slug's templates and sentinel inputs to the matching dicts in `workloads.py` (`BACKGROUND_TEMPLATES`, `SENTINEL_INPUTS`).
3. The profile is automatically discovered by `list_profiles()` and available in the CLI.

## Project Scope / Safety

See `docs/safety_scope.md`. This project is strictly defensive research — benchmark design for evaluating existing classifier resilience, not building attack tooling. All generated inputs are synthetic and domain-specific to the defender context.

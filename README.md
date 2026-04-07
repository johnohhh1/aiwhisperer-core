# AI Whisperer — Adversarial Attention Saturation Framework

<p align="center">
  <img src="https://img.shields.io/badge/status-research%20%2F%20active-brightgreen?style=flat-square" alt="Status" />
  <img src="https://img.shields.io/badge/python-%3E%3D3.11-blue?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/dependencies-stdlib%20only-success?style=flat-square" alt="Dependencies" />
  <img src="https://img.shields.io/badge/tests-34%20passing-brightgreen?style=flat-square&logo=github-actions&logoColor=white" alt="Tests" />
  <img src="https://img.shields.io/badge/experiments-27%20completed-informational?style=flat-square" alt="Experiments" />
  <img src="https://img.shields.io/badge/profiles-5%20domains-orange?style=flat-square" alt="Profiles" />
  <img src="https://img.shields.io/badge/license-research%20only-lightgrey?style=flat-square" alt="License" />
</p>

<p align="center">
  <em>To dismiss a signal as distraction, you must first attend to it.</em>
</p>

---

AI Whisperer is a defensive security research project measuring **intake-resilience and compute asymmetry** in AI-driven classification pipelines. The core claim: generating a high-semantic-density, low-actionability input is structurally cheaper than classifying it. This project tests whether that asymmetry is real, measurable, and domain-transferable — and what defenders can do about it.

> **Posture:** Test the claim. Discard weak assumptions early. Produce defender-oriented guidance. No vague theorizing without measurement.

---

## Core Thesis

```
Any classification pipeline has a mandatory intake stage.
That stage is the attack surface.

Generation cost << Classification cost
         ↓
Asymmetry exists at intake by construction
         ↓
Can cheap defenses (dedup, clustering, caching) close the gap?
         ↓
That's what the benchmark measures.
```

The effectiveness depends entirely on whether inputs can be generated with sufficient diversity to defeat deduplication and clustering defenses. Three strategies are evaluated in increasing order of complexity:

| Strategy | Workload | Defense Defeated |
|---|---|---|
| Fixed-template substitution | `benign_background` | None (collapsed by dedup) |
| Template + phrase variation | `templated_variation` | Partial dedup |
| Multi-family vocabulary mixing | `high_diversity` | Dedup + partial clustering |
| *(Planned)* Reservoir ESN generator | — | Clustering at scale |

---

## Defender Domains

The thesis is tested across five defensive contexts rather than a single threat framing:

| Profile | Domain | `false_negative_cost` |
|---|---|---|
| `soc_triage` | SOC / threat-intel triage pipelines | 0.7 |
| `trust_safety` | Trust & safety moderation queues | 1.0 |
| `fraud_abuse` | Fraud and abuse detection | 0.5 |
| `mass_surveillance` | Population-monitoring pipelines | 0.9 |
| `auto_targeting` | Automated targeting / prioritization | 1.0 |

---

## Key Properties

| Property | What it means |
|---|---|
| **Discovery is not defeat** | The generator contains no sensitive material by design |
| **Intake cost asymmetry** | Generating an input is cheaper than classifying it |
| **Diversity defeats deduplication** | Varied inputs cannot be collapsed by hash-based caching |
| **The intake invariant** | No input can be dismissed without first being processed |

---

## Quickstart

```bash
# Install
pip install -e .

# Run tests (34 passing)
PYTHONPATH=src python -m unittest

# Single benchmark run → JSON
PYTHONPATH=src python -m aiwhisperer_core.cli \
  --profile soc_triage --workload templated_variation \
  --total-inputs 200 --sentinel-interval 25 \
  --output results/run.json

# Repeat 5× with aggregated mean/stdev
PYTHONPATH=src python -m aiwhisperer_core.cli \
  --profile soc_triage --workload high_diversity --repeat 5

# Batch runs from manifest
PYTHONPATH=src python -m aiwhisperer_core.cli \
  --manifest config/example_manifest.json

# CSV sweep output
PYTHONPATH=src python -m aiwhisperer_core.cli \
  --profile fraud_abuse --workload mixed \
  --output-csv results/sweep.csv

# Isolate defenses
PYTHONPATH=src python -m aiwhisperer_core.cli \
  --profile soc_triage --workload exact_repetition \
  --disable-dedup --disable-clustering --disable-cache
```

**Workloads:** `benign_background` · `exact_repetition` · `templated_variation` · `high_diversity` · `mixed`

---

## Pipeline Architecture

```
Profile JSON ──→ load_profile()
                      │
                      ▼
Workload type ──→ build_inputs() ──→ GeneratedInput stream
                                           │
                                           ▼
                              ┌────────────────────────┐
                              │    SyntheticPipeline    │
                              │  ① intake              │
                              │  ② prefilter           │
                              │  ③ dedup (SHA-256)     │
                              │  ④ clustering (Jaccard)│
                              │  ⑤ classifier          │
                              └────────────────────────┘
                                           │
                                           ▼
                              PipelineResult (per item)
                                           │
                                           ▼
                              summarize_run() ──→ JSON summary
```

Per-stage timing, p50/p95/max for queue depth and classifier score, and sentinel false-negative drift by load tercile are all reported in the summary output.

---

## Research Status

First sweep complete: 27 experiments across dedup on/off, clustering on/off, and workload diversity gradient.

**Key findings so far:**

- ✅ Clear 3–4× processing cost gradient from `benign_background` → `high_diversity`
- ✅ Dedup collapses `exact_repetition` to near-zero cost (98.7% hit rate)
- ✅ Clustering degrades under `high_diversity` but doesn't fully fail
- ⚠️ Prefilter never rejects inputs — blocklists need tuning
- ⚠️ Sentinel preservation is uniformly 1.0 — score boost too strong, needs noise floor
- ⚠️ Cost model doesn't reflect dedup/cache early-exit savings yet

Full findings: [`docs/research_findings.md`](docs/research_findings.md)

---

## Repo Structure

```
aiwhisperer-core/
├── src/aiwhisperer_core/   # Harness (stdlib only)
│   ├── pipeline.py         # SyntheticPipeline — 5-stage classifier model
│   ├── workloads.py        # Input generation (5 workload types)
│   ├── benchmark.py        # Orchestration, metrics, CSV, manifest
│   ├── profiles.py         # Profile loader
│   ├── cli.py              # Entry point
│   └── models.py           # Dataclasses
├── config/
│   ├── profiles/           # 5 domain profiles (JSON)
│   └── fixtures/           # Per-profile workload templates
├── results/                # Baseline + research experiment outputs
├── docs/                   # Whitepaper, glossary, benchmark spec, findings
├── architecture/           # Technical design docs
├── threat_model/           # Adversary modeling
└── tests/                  # 34 tests
```

---

## Authors

**JohnO** — initial concept, architecture framing

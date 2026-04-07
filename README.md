# AI Whisperer — Adversarial Attention Saturation Framework

> *To dismiss a signal as distraction, you must first attend to it.*

AI Whisperer is a research project on intake-resilience and compute asymmetry in
AI-driven classification pipelines.

## Project Posture
This repository is currently a research stub. The near-term job is not to "build the
system"; it is to test whether the claimed asymmetry exists in controlled settings,
document defensive implications, and discard weak assumptions early.

This repo is intended for:
- architectural analysis
- benchmark design in controlled environments
- defender countermeasure research
- practical intake-resilience evaluation

This repo is not intended for:
- vague theorizing without measurement
- architecture discussion without benchmarks
- one-domain assumptions presented as universal truth

## Core Thesis
Any classification pipeline has a mandatory intake stage. That stage is the attack surface.
A distributed agent network generating high-semantic-density, low-actionability inputs
forces the target system to expend compute and classification cycles on inputs that pass
initial intake filters without containing actionable content.

## Defender Domains
The thesis should be tested across multiple defensive settings rather than treated as a
single nation-state or military framing. Candidate domains include:
- SOC and threat-intel triage pipelines
- fraud and abuse detection systems
- trust-and-safety moderation queues
- mass surveillance or population-monitoring systems
- automated targeting or prioritization systems

## Key Properties
- **Discovery is not defeat** — the generator contains no sensitive material by design
- **Intake cost asymmetry** — generating an input is cheaper than classifying it
- **Diversity defeats deduplication** — varied inputs cannot be collapsed by hash-based caching
- **The intake invariant** — no input can be dismissed without first being processed

## The Diversity Generation Problem
The effectiveness of the asymmetry depends on whether inputs can be generated with
sufficient diversity to defeat deduplication and semantic clustering defenses. The
project evaluates three strategies in increasing order of complexity:
1. Fixed-template rendering with parameter substitution.
2. Templated variation with appended phrase fragments.
3. High-diversity generation combining multiple template families and vocabulary domains.

A reservoir-computing-inspired generator (echo state network plus learned motif decoder)
is a candidate architecture for strategy 3. Whether it adds value over strategy 2 is
an open question that the benchmark is designed to answer before the architecture is
implemented.

## Repo Structure
- `/src/aiwhisperer_core` — benchmark harness (stdlib only)
- `/config/profiles` — domain profile configs (`soc_triage`, `trust_safety`, `fraud_abuse`, `mass_surveillance`, `auto_targeting`)
- `/config/fixtures` — per-profile workload template fixtures
- `/results` — baseline and research experiment outputs (JSON)
- `/docs` — whitepaper, glossary, benchmark spec, research agenda, findings
- `/architecture` — technical design docs
- `/threat_model` — adversary modeling
- `/tests` — 34 smoke + integration tests

## Status
Harness functional. First research sweep complete (27 experiments across 5 profiles and 4 workload types). Whitepaper in draft. Key open gaps identified — see `docs/research_findings.md`.

## Harness Quickstart
```bash
# Install (editable)
pip install -e .

# Run tests
PYTHONPATH=src python -m unittest

# Single benchmark run
PYTHONPATH=src python -m aiwhisperer_core.cli \
  --profile soc_triage --workload templated_variation \
  --total-inputs 200 --sentinel-interval 25 --output results/run.json

# Repeated runs with aggregated stats
PYTHONPATH=src python -m aiwhisperer_core.cli \
  --profile soc_triage --workload high_diversity --repeat 5

# Batch runs via manifest
PYTHONPATH=src python -m aiwhisperer_core.cli --manifest config/example_manifest.json

# CSV output
PYTHONPATH=src python -m aiwhisperer_core.cli \
  --profile fraud_abuse --workload mixed --output-csv results/sweep.csv
```

**Profiles:** `soc_triage`, `trust_safety`, `fraud_abuse`, `mass_surveillance`, `auto_targeting`  
**Workloads:** `benign_background`, `exact_repetition`, `templated_variation`, `high_diversity`, `mixed`  
**Disable defenses:** `--disable-dedup`, `--disable-clustering`, `--disable-cache`

## Known Gaps (Next Priorities)
1. Prefilter never rejects inputs — blocklists need tuning so the prefilter stage produces variance.
2. Sentinel preservation is 1.0 in all conditions — the sentinel score boost guarantees survival; add a configurable noise floor or threshold jitter to stress-test it.
3. Simulated processing cost does not decrease on dedup/cache hits — fix the cost model so early-exit paths are reflected in timing.
4. Run at high input rates (`--input-rate 200+`) to generate queue backlog and make `sentinel_fn_by_load` meaningful.
5. Implement the reservoir-inspired generator and compare against `high_diversity` baseline.

## Authors
JohnO — initial concept, architecture framing

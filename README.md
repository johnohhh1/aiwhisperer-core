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
- `/docs` — whitepaper and theory
- `/docs/glossary.md` — canonical terms and working definitions
- `/docs/benchmark_spec.md` — benign evaluation harness definition
- `/docs/research_agenda.md` — concrete research plan and decision gates
- `/docs/next_paper_outline.md` — structure for expanding the whitepaper
- `/docs/safety_scope.md` — defensive-use boundaries for the project
- `/config/profiles` — domain profile configs for the synthetic benchmark
- `/src/aiwhisperer_core` — benchmark harness implementation
- `/tests` — smoke tests for the harness
- `/architecture` — technical design
- `/threat_model` — adversary modeling

## Status
Concept/stub phase. Whitepaper in progress. Benchmark harness functional.

## Harness Quickstart
```bash
python -m unittest
PYTHONPATH=src python -m aiwhisperer_core.cli --profile soc_triage --workload templated_variation
```

The initial harness is intentionally simple:
- stdlib only
- synthetic pipeline stages
- profile-driven workloads
- JSON summary output for experiment logging

## Immediate Priorities
1. Formalize terms and success metrics.
2. Build a benign evaluation harness to test cost asymmetry.
3. Compare the reservoir-layer idea against simpler diversity baselines.
4. Test the thesis across multiple defensive-domain abstractions.
5. Produce defender-oriented mitigation guidance alongside any prototype work.

## Authors
JohnO — initial concept, architecture framing

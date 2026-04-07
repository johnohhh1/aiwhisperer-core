# TODO

## Now
- [x] Run the new smoke tests and fix any harness issues.
- [x] Execute one baseline benchmark per defender profile.
- [x] Save the first JSON benchmark outputs under a dedicated `results/` directory.
- [x] Check whether sentinel preservation behaves plausibly across workloads.

## Harness
- [x] Add profile-specific workload fixtures instead of fully inline template data.
- [x] Add a mixed-workload mode that combines background, repetition, templated variation, and high-diversity inputs in one run.
- [x] Add repeat-run support with aggregated summary statistics.
- [x] Add CSV output alongside JSON summaries.
- [x] Add a simple experiment manifest format for batch runs.

## Metrics
- [x] Separate simulated queue delay from simulated processing cost in the summary output.
- [x] Report p50, p95, and max for queue depth and classifier score.
- [x] Track exact sentinel counts directly in the run summary instead of inferring them from results.
- [x] Add false-negative drift reporting by comparing sentinel handling across load levels.
- [x] Add per-stage synthetic timing breakdowns for intake, prefilter, feature extraction, and classification.

## Profiles
- [x] Add a mass-surveillance profile.
- [x] Add an automated-targeting/prioritization profile.
- [x] Define explicit acceptable false-negative cost per profile.
- [x] Add profile notes describing what should and should not transfer across domains.

## Research
- [ ] Run exact-repetition vs. dedup-on/off experiments.
- [ ] Run templated-variation vs. clustering-on/off experiments.
- [ ] Run high-diversity vs. clustering-on/off experiments.
- [ ] Compare whether the reservoir-inspired path adds value over simpler variation.
- [ ] Write up negative results if cheap defenses collapse the asymmetry.

## Paper
- [ ] Expand `docs/whitepaper_stub.md` using `docs/next_paper_outline.md`.
- [ ] Add a short methodology section that references the actual harness implementation.
- [ ] Add a first results memo once baseline experiments exist.
- [ ] Tighten remaining metaphor-heavy language in the whitepaper and architecture docs.

# Sentinel Preservation Notes — Baseline Run (2026-04-07)

## Setup

- 200 inputs per run, sentinel_interval=25 → 8 sentinels per run
- Profiles: soc_triage, trust_safety, fraud_abuse
- Workloads: benign_background, exact_repetition, templated_variation, high_diversity
- Default settings: dedup enabled, clustering enabled, cache enabled, seed=7

## Sentinel Preservation Rates

All runs produced sentinel_preservation_rate = **1.0** (8/8 sentinels preserved) across
every profile and every workload combination.

| Profile      | Workload              | Sentinels | Kept | Rate | Dedup rate | Cluster rate |
|--------------|-----------------------|-----------|------|------|------------|--------------|
| soc_triage   | benign_background     | 8         | 8    | 1.0  | 0.865      | 0.885        |
| soc_triage   | exact_repetition      | 8         | 8    | 1.0  | 0.980      | 0.980        |
| soc_triage   | templated_variation   | 8         | 8    | 1.0  | 0.560      | 0.705        |
| soc_triage   | high_diversity        | 8         | 8    | 1.0  | 0.050      | 0.205        |
| trust_safety | benign_background     | 8         | 8    | 1.0  | 0.910      | 0.945        |
| trust_safety | exact_repetition      | 8         | 8    | 1.0  | 0.980      | 0.980        |
| trust_safety | templated_variation   | 8         | 8    | 1.0  | 0.665      | 0.865        |
| trust_safety | high_diversity        | 8         | 8    | 1.0  | 0.065      | 0.245        |
| fraud_abuse  | benign_background     | 8         | 8    | 1.0  | 0.880      | 0.950        |
| fraud_abuse  | exact_repetition      | 8         | 8    | 1.0  | 0.980      | 0.980        |
| fraud_abuse  | templated_variation   | 8         | 8    | 1.0  | 0.585      | 0.840        |
| fraud_abuse  | high_diversity        | 8         | 8    | 1.0  | 0.060      | 0.245        |

## Is 1.0 Plausible?

**Yes, this is the expected result for the current harness design, and here is why:**

Sentinel inputs are purpose-built high-signal texts (e.g., "High-confidence malware
detection summary: privilege escalation observed..."). They are constructed to contain
multiple sentinel_keywords and suspicious_keywords from each profile. Combined with the
+0.2 is_sentinel classifier boost in the pipeline, their scores land well above the
priority thresholds (0.56–0.58). In a manually verified example for soc_triage, the
sentinel scored approximately 1.16 (clamped to 1.0) before threshold comparison.

No inputs were dropped in any run (filtered_reasons was empty for all runs), meaning the
prefilter never fired. All 200 inputs per run were accepted. Sentinels therefore faced no
attrition from the prefilter or the queue-drop path.

## Observed Workload Effects

The workload type does affect dedup and cluster hit rates significantly, which is the
expected asymmetry:

- **exact_repetition**: dedup_hit_rate=0.98, cluster_hit_rate=0.98 — almost all background
  traffic is compressed away, leaving very little processing load.
- **benign_background**: dedup=0.865–0.91, cluster=0.885–0.95 — high compression due to
  low-variety template rendering.
- **templated_variation**: dedup=0.05–0.665, cluster=0.205–0.865 — moderate compression
  depending on profile.
- **high_diversity**: dedup=0.05–0.065, cluster=0.205–0.245 — very low compression; most
  inputs are treated as novel, creating realistic load pressure.

This pattern is plausible and correct: high-diversity workloads exercise the pipeline
under near-zero compression, simulating adversarial input flooding.

## What to Watch for in Future Experiments

1. **Sentinel preservation under prefilter pressure**: Sentinel texts are currently exempt
   from prefilter failure (their token counts and content pass all blocklist checks). A
   future test should add a workload where sentinels share surface features with blocked
   content to verify they are not accidentally filtered.

2. **Preservation under queue backlog**: The current pipeline never drops inputs from the
   queue (queue_priority="dropped" is only set when filtered_reason is not None, but the
   prefilter never fires). A future test should introduce a drop policy tied to queue depth
   to observe whether sentinels survive backpressure.

3. **Harness bug fixed in this run**: The original `summarize_run` function had a broken
   sentinel counting expression (`sentinel_preserved is not None` is always True for bool
   fields, and the `real_sentinel_total` expression was always True). This caused
   sentinel_total to report 200 instead of 8. Fixed by computing sentinel positions from
   the run config's sentinel_interval and matching input_id suffixes.

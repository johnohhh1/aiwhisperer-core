# AI Whisperer: Research Findings

Experiments run: 2026-04-07  
Parameters: `--total-inputs 300 --sentinel-interval 25 --seed 42`  
Profiles tested: `soc_triage`, `fraud_abuse`, `trust_safety`

---

## Experiment 1: Exact-Repetition — Dedup On vs. Off

**Question:** How much does deduplication collapse the attack surface in a pure-repetition flood?

### Results

| Profile | Condition | dedup_hit_rate | cluster_hit_rate | avg_processing_cost_ms | p95_processing_cost_ms | accepted_input_rate | sentinel_preservation_rate |
|---|---|---|---|---|---|---|---|
| soc_triage | dedup_on | 0.9867 | 0.9867 | 2.3762 | 2.3293 | 1.0 | 1.0 |
| soc_triage | dedup_off | 0.0000 | 0.9867 | 2.3762 | 2.3293 | 1.0 | 1.0 |
| fraud_abuse | dedup_on | 0.9867 | 0.9867 | 2.3781 | 2.3284 | 1.0 | 1.0 |
| fraud_abuse | dedup_off | 0.0000 | 0.9867 | 2.3781 | 2.3284 | 1.0 | 1.0 |
| trust_safety | dedup_on | 0.9867 | 0.9867 | 2.5356 | 2.4962 | 1.0 | 1.0 |
| trust_safety | dedup_off | 0.0000 | 0.9867 | 2.5356 | 2.4962 | 1.0 | 1.0 |

### Interpretation

Deduplication achieves a 98.67% hit rate across all three profiles under exact repetition, correctly tagging the overwhelming majority of the flood as seen-before. Disabling dedup drops the dedup_hit_rate to zero by definition, but clustering alone picks up the same 98.67% of inputs as cluster hits — so the two defenses are redundant in this workload. Critically, `avg_processing_cost_ms` and `p95_processing_cost_ms` are identical between dedup_on and dedup_off: the simulated per-item cost does not change regardless of whether the dedup fast-path fires. This reveals that in the current harness, dedup and clustering affect the *classification routing* metadata but do not shorten the measured processing time per input; the asymmetric cost collapse the defender would expect from early-exit caching is not yet reflected in the timing model. Sentinel preservation is 1.0 in all conditions.

---

## Experiment 2: Templated-Variation — Clustering On vs. Off

**Question:** Does clustering remain effective against surface-varied but semantically similar inputs?

### Results

| Profile | Condition | dedup_hit_rate | cluster_hit_rate | avg_processing_cost_ms | p95_processing_cost_ms | avg_classifier_score | sentinel_preservation_rate |
|---|---|---|---|---|---|---|---|
| soc_triage | clustering_on | 0.6567 | 0.7400 | 3.5881 | 6.5787 | 0.3110 | 1.0 |
| soc_triage | clustering_off | 0.6567 | 0.0000 | 4.0953 | 6.9237 | 0.4205 | 1.0 |
| fraud_abuse | clustering_on | 0.6800 | 0.8833 | 3.0252 | 6.4014 | 0.3547 | 1.0 |
| fraud_abuse | clustering_off | 0.6800 | 0.0000 | 3.9692 | 6.7501 | 0.4850 | 1.0 |
| trust_safety | clustering_on | 0.7533 | 0.9000 | 2.8291 | 6.3994 | 0.4358 | 1.0 |
| trust_safety | clustering_off | 0.7533 | 0.0000 | 3.7405 | 6.8497 | 0.5673 | 1.0 |

### Interpretation

With templated variation, exact deduplication handles 66–75% of the flood on its own because many variants happen to reproduce the same string. Clustering on top adds a further 7–15 percentage points of coverage (soc_triage: +7.4pp; fraud_abuse: +20.3pp; trust_safety: +14.7pp), catching surface-varied inputs that share a cluster centroid with already-seen examples. Disabling clustering raises `avg_processing_cost_ms` by 12–31% and inflates `avg_classifier_score` by 8–13 percentage points — meaning more semantically-suspect inputs reach the full classifier when the cluster fast-path is absent. Sentinel preservation remains perfect (1.0) in all conditions.

---

## Experiment 3: High-Diversity — Clustering On vs. Off

**Question:** Does diversity defeat clustering? Is there a meaningful cost differential?

### Results

| Profile | Condition | dedup_hit_rate | cluster_hit_rate | avg_processing_cost_ms | p95_processing_cost_ms | avg_classifier_score | sentinel_preservation_rate |
|---|---|---|---|---|---|---|---|
| soc_triage | clustering_on | 0.0767 | 0.2933 | 7.3660 | 8.9943 | 0.3725 | 1.0 |
| soc_triage | clustering_off | 0.0767 | 0.0000 | 8.1341 | 9.0643 | 0.4150 | 1.0 |
| fraud_abuse | clustering_on | 0.0733 | 0.3133 | 7.2660 | 8.9746 | 0.4350 | 1.0 |
| fraud_abuse | clustering_off | 0.0733 | 0.0000 | 8.1048 | 8.9746 | 0.4798 | 1.0 |
| trust_safety | clustering_on | 0.0833 | 0.3333 | 7.2176 | 9.1303 | 0.5543 | 1.0 |
| trust_safety | clustering_off | 0.0833 | 0.0000 | 8.0855 | 9.1474 | 0.6001 | 1.0 |

### Interpretation

High-diversity inputs reduce dedup_hit_rate to roughly 7–8% (only accidental string collisions survive) and drop cluster_hit_rate from 29–33% down to zero when clustering is disabled. The cost story is clear: with all defenses on, `avg_processing_cost_ms` is 7.2–7.4 ms — roughly 3x the templated-variation cost and about 3.5x the exact-repetition cost — confirming that diversity directly inflates per-item compute. Disabling clustering adds a further 10–11% increase (approximately 0.77–0.87 ms per item), a measurable but not catastrophic uplift compared with the base diversity-induced cost already paid. The cluster defense retains 29–33% efficacy even against high-diversity inputs, suggesting that the cluster centroids still absorb a meaningful fraction of semantically-related attack variants. Sentinel preservation is again 1.0 across all conditions.

---

## Experiment 4: Reservoir Path — benign_background vs. templated_variation vs. high_diversity (All Defenses On)

**Question:** Does increasing semantic diversity (the "reservoir" idea) meaningfully change compute cost or sentinel preservation?

### Results

| Profile | Workload | dedup_hit_rate | cluster_hit_rate | avg_processing_cost_ms | p95_processing_cost_ms | avg_classifier_score | sentinel_preservation_rate |
|---|---|---|---|---|---|---|---|
| soc_triage | benign_background | 0.9100 | 0.9167 | 2.4699 | 5.2939 | 0.2840 | 1.0 |
| soc_triage | templated_variation | 0.6567 | 0.7400 | 3.5881 | 6.5787 | 0.3110 | 1.0 |
| soc_triage | high_diversity | 0.0767 | 0.2933 | 7.3660 | 8.9943 | 0.3725 | 1.0 |
| fraud_abuse | benign_background | 0.9200 | 0.9700 | 1.9575 | 3.2281 | 0.3574 | 1.0 |
| fraud_abuse | templated_variation | 0.6800 | 0.8833 | 3.0252 | 6.4014 | 0.3547 | 1.0 |
| fraud_abuse | high_diversity | 0.0733 | 0.3133 | 7.2660 | 8.9746 | 0.4350 | 1.0 |
| trust_safety | benign_background | 0.9400 | 0.9633 | 2.0541 | 3.3450 | 0.4197 | 1.0 |
| trust_safety | templated_variation | 0.7533 | 0.9000 | 2.8291 | 6.3994 | 0.4358 | 1.0 |
| trust_safety | high_diversity | 0.0833 | 0.3333 | 7.2176 | 9.1303 | 0.5543 | 1.0 |

### Interpretation

The data show a clear monotonic cost gradient as attacker diversity increases. Going from benign_background to high_diversity, `avg_processing_cost_ms` increases by roughly 3–4x across all profiles (soc_triage: 2.47 → 7.37 ms; fraud_abuse: 1.96 → 7.27 ms; trust_safety: 2.05 → 7.22 ms). The reservoir-inspired high-diversity workload therefore succeeds in its primary adversarial goal — forcing the defender to expend substantially more compute per item — but the gain plateaus between templated_variation and high_diversity relative to the jump from benign_background to templated_variation. The `avg_classifier_score` also rises with diversity (soc_triage: 0.284 → 0.373), indicating that more diverse inputs appear more suspicious to the classifier on average, which is the expected outcome of an adversary selecting inputs that avoid clean background-like structure. Sentinel preservation is universally 1.0, indicating that the defender's ability to process real signals is not degraded by volume in this run size.

---

## Negative Results

### 1. Dedup and clustering do not reduce `accepted_input_rate`

In every experimental condition, `accepted_input_rate` is 1.0. Neither deduplication nor clustering causes any input to be *rejected*; they only route inputs to a cheaper processing path. This means the cheap defenses do not collapse the attack surface from the attacker's perspective — adversarial inputs still reach the downstream classifier and are accepted into the system. The asymmetric cost reduction the defender gains from dedup/clustering is real in principle, but the current harness does not model that early-exit savings as reduced simulated processing time.

### 2. Dedup/clustering do not affect per-item simulated processing time in exact-repetition

Under `exact_repetition`, the `avg_processing_cost_ms` is identical with dedup on (2.3762 ms, soc_triage) and dedup off (2.3762 ms). The dedup hit flag is recorded but the timing model assigns the same synthetic cost regardless of whether the fast path fires. The claimed cost asymmetry — that the defender pays less per item when dedup collapses the flood — is not currently visible in the per-run timing summary.

### 3. Clustering provides only partial coverage against high-diversity inputs

Under high_diversity, cluster_hit_rate is 29–33%. This means 67–71% of high-diversity inputs proceed through the full classification pipeline without a cluster match. Combined with the near-zero dedup rate (~8%), high-diversity attacks already substantially defeat both cheap defenses by construction. The cost differential between clustering_on and clustering_off is real but modest (~10–11% increase in avg cost), confirming that diversity is the dominant cost driver, not the presence or absence of the cluster defense.

### 4. Sentinel preservation is uniformly 1.0 — no stress visible

All 12 sentinels are preserved in every condition across every profile and workload. This is a null result for the false-negative drift hypothesis at this scale (300 inputs, 12 sentinels). The run size is too small to generate meaningful queue contention or show degradation under load. Any claim about sentinel preservation robustness would need much larger runs (>10,000 inputs) or forced queue depth experiments to be credible.

---

## Next Steps

1. **Model early-exit cost savings in the timing harness.** The most urgent gap is that dedup and clustering fast-paths do not currently reduce simulated processing time. Add a `dedup_cost_ms` and `cluster_cost_ms` parameter to the profile config so that hits draw from a cheaper distribution. This is necessary before any cost-asymmetry claim can be quantified experimentally.

2. **Stress-test sentinel preservation at scale.** Run with `--total-inputs 5000 --sentinel-interval 50` (100 sentinels per run) across all high-diversity conditions to determine whether sentinel_preservation_rate degrades under realistic queue pressure. The current uniformly-1.0 result is uninformative for the defender's core concern.

3. **Run the mixed workload and compare it to pure-diversity baselines.** The harness supports a `mixed` workload that cycles through all four input types. A mixed run approximates a realistic attacker strategy (vary techniques to avoid pattern detection) and should be compared against the high_diversity pure baseline to see whether interleaving workload types provides the attacker further clustering evasion beyond what high_diversity alone achieves.

4. **Measure cost with explicit early-exit branching.** Implement a `--fast-exit-on-dedup` flag that short-circuits all downstream stages on a dedup or cluster hit and records both the fast-path cost and the full-path cost. This gives a real measured ratio for the defender cost asymmetry rather than the current synthetic-only estimate.

5. **Test the mass_surveillance and automated_targeting profiles.** All current experiments used soc_triage, fraud_abuse, and trust_safety. The two additional profiles (mass_surveillance, automated_targeting) have distinct classifier biases and false-negative cost weights that may show qualitatively different behavior — in particular, automated_targeting has a high queue_priority_threshold that should change how the clustering defense interacts with priority routing.

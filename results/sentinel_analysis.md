# Sentinel Analysis — Baseline Runs

**Runs:** `templated_variation` workload, 200 inputs, sentinel_interval=25, seed=42  
**Profiles:** `soc_triage`, `trust_safety`, `fraud_abuse`

## Sentinel Counts

With 200 total inputs and `sentinel_interval=25`, sentinels are injected at
positions 25, 50, 75, …, 200 — giving 8 sentinels per run. This is correct.

## Preservation Rates

| Profile | sentinel_total | sentinel_preserved | preservation_rate |
|---|---|---|---|
| soc_triage | 8 | 8 | 1.0 |
| trust_safety | 8 | 8 | 1.0 |
| fraud_abuse | 8 | 8 | 1.0 |

**Concern: all three profiles show `sentinel_preservation_rate = 1.0`.**

This is plausible given the synthetic design but represents a ceiling effect worth
noting. Two compounding causes:

1. **Classifier boost is unconditional.** `pipeline.py::_classify` adds a flat
   `+0.2` score to every sentinel (`is_sentinel=True`), in addition to any
   keyword hits from `sentinel_keywords`. Because the sentinel text strings are
   specifically crafted to hit those keywords, every sentinel ends up well above
   `queue_priority_threshold` and is marked `queue_priority="high"`. The
   preservation condition (`accepted and queue_priority == "high"`) is therefore
   always satisfied for sentinels.

2. **No prefilter drops sentinels.** `accepted_input_rate = 1.0` for all three
   runs — the sentinel texts are longer than `prefilter_min_tokens` and contain
   no blocklist tokens, so the prefilter never drops them.

## False-Negative Drift by Load (sentinel_fn_by_load)

All 8 sentinels fall in the `low` load tercile; `mid` and `high` are empty.

This is expected: `avg_queue_depth = 0` and `queue_depth_stats.max = 0` for all
runs. The simulated arrival interval (~67 ms at 15 inputs/s) is far longer than
per-item processing cost (<5 ms), so the queue never backs up and all items
arrive at depth 0. All 200 items land in the `low` tercile, leaving `mid` and
`high` empty.

As a result, the `sentinel_fn_by_load` breakdown provides no signal here.
Setting a higher `--input-rate` (e.g., 150–500 inputs/s) or lower `--total-inputs`
spread over a shorter interval would produce non-zero queue depths and populate
the mid/high terciles.

## Recommendations

- **Rate the preservation signal skeptically.** Until the classifier boost is
  made conditional (e.g., disabled during load-testing experiments), or until
  the prefilter can reject sentinels, `sentinel_preservation_rate` will stay at
  1.0 for well-formed sentinel inputs and provides no differentiation across
  profiles or load conditions.

- **Run at higher input rates** to exercise queue backlog and the
  `sentinel_fn_by_load` breakdown. Suggested follow-on: rerun with
  `--input-rate 200` (or higher) to produce non-zero queue depths.

- **Consider adding adversarial sentinel variants** — sentinels that are shorter
  (to risk prefilter rejection) or use lower-confidence keyword density — to
  expose realistic false-negative conditions that the current 1.0 rate masks.

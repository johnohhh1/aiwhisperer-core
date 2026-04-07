# Results Memo v1: Baseline Benchmark Architecture and Pre-Experimental Framing

**Status:** Pre-results framing document  
**Date:** April 2026  
**Scope:** What the baseline benchmark reveals before the full experiment sweep is
complete; how to interpret results when they arrive; what the current model
intentionally does and does not capture.

---

## Purpose

This memo exists because the benchmark harness is now functional and producing
structured output, but the experiment sweep is not complete. Before running
systematic experiments, we want to establish what the model already tells us —
from its design alone — about the shape of expected results. This document is the
reference for evaluating whether future results are surprising, expected, or
outside the model's range.

It is not a results paper. It is the pre-registration framing that makes the
results meaningful when they arrive.

---

## 1. What the Pipeline Model Captures

The synthetic pipeline in `src/aiwhisperer_core/pipeline.py` is a structural
approximation of the generic intake-classify-triage sequence. It captures the
following features of real pipelines:

**Per-stage cost attribution.** The harness instruments four distinct stages
(intake, prefilter, feature extraction, classification) with independent timing
models. This allows the experiment to attribute processing cost to the stage that
generates it, rather than treating total processing cost as an undifferentiated
number. In initial baseline runs, feature extraction accounts for approximately
60–65% of simulated per-input cost across all profiles, which reflects the
expected relative expense of token-level feature computation.

**Deduplication state.** The pipeline maintains a persistent exact-fingerprint
set across a run, so that repeated inputs incur only the cost of a fingerprint
lookup rather than full processing. This correctly captures the key property of
hash-based dedup: its effectiveness degrades as input diversity increases, not
because the mechanism fails, but because diversity produces inputs that are
genuinely novel.

**Cluster state and sliding window dynamics.** Jaccard-based clustering operates
over a window of 128 recent token sets. This means clustering effectiveness depends
on both the diversity of the current input and the recent history of inputs
processed before it. The window size creates a temporal dependency: a sustained
high-diversity stream that fills and expires the window will have lower cluster
hit rates over time than a mixed stream where diverse inputs are interspersed
with repetitive ones.

**Queue depth as a derived metric.** The pipeline models queue depth as the ratio
of processing backlog to an assumed 8 ms per-item service interval. At the current
experiment volumes (200 inputs, 15/sec), queue depth remains zero because the
pipeline processes inputs faster than they arrive. This is a deliberate starting
point: it establishes the cost model under no-load conditions before introducing
load pressure.

**Sentinel-specific score inflation.** Sentinel inputs receive a fixed +0.2
classifier score boost. This ensures that well-constructed sentinel texts reliably
exceed the priority threshold in the absence of load pressure. The boost is
transparent: it exists to ensure that sentinels are reliably identifiable in
baseline conditions, so that any future degradation in sentinel preservation is
clearly attributable to load or classifier compression rather than to sentinel
construction quality.

---

## 2. What the Model Intentionally Simplifies

The following design choices are intentional simplifications whose effects should
be understood before interpreting any results.

**Generation cost is understated.** The current `_measure_generation_cpu`
function measures the CPU time to sum character ordinals over a generated string.
This is not a meaningful measure of real generation cost. In a real adversarial
scenario, generation involves template rendering, random sampling, and possibly
model inference — costs measured in milliseconds to seconds per input, not
microseconds. The current measurement is a structural placeholder that establishes
that the harness can measure generation cost; it is not a calibrated estimate.

*Implication:* Any asymmetry ratio (processing cost / generation cost) computed
from current runs will be inflated by roughly 2–3 orders of magnitude relative to
what a realistic generation mechanism would produce. Results should not be
interpreted as evidence that the asymmetry is large. They are evidence that the
ratio measurement infrastructure works.

**The prefilter does not fire.** All workloads currently produce inputs that pass
the prefilter without rejection. This is intentional: the baseline workloads are
designed to represent coherent, syntactically valid inputs that would pass a
lightweight content check. A prefilter that successfully rejects low-actionability
inputs before feature extraction would substantially reduce the asymmetry. The
current baseline therefore represents the worst-case scenario for the defender's
cheapest control.

*Implication:* The baseline asymmetry figures represent the upper bound of cost
exposure before prefilter hardening is applied. Phase 2 should add a calibrated
prefilter that rejects some fraction of background inputs and measure the cost
reduction.

**Queue saturation does not appear.** At 200 inputs, 15/sec, the pipeline
processes inputs slightly faster than they arrive. Queue depth is zero in all
baseline runs. This means H3 (false-negative drift under queue saturation) cannot
be tested at the current volume and rate.

*Implication:* Current sentinel preservation rate of 1.0 is the result of no
saturation, not evidence that sentinels survive saturation. The rate will remain
1.0 until the experiment is run at volumes or rates that create queue backlog.

**Classifier is a heuristic, not a model.** The classifier assigns scores based
on keyword matches and a diversity bonus. It does not perform semantic inference.
The high-diversity workload generates inputs that score slightly higher on average
than low-diversity workloads because diverse inputs have more unique tokens, which
increases the diversity bonus. This is a structural feature of the cost model that
partially simulates the real property that novel inputs are harder to classify quickly.

*Implication:* Any classifier score compression observed under high-diversity load
is a function of the diversity bonus mechanism, not of semantic classifier behavior.
The effect direction is correct — diverse inputs are harder to dismiss — but the
magnitude is not calibrated against real classification systems.

---

## 3. What the Baseline Runs Already Show

The baseline runs (200 inputs, three profiles, four workload types, all defenses
enabled) produce results that are structurally informative even before the experiment
sweep is complete.

### Deduplication collapse is workload-sensitive, not defense-dependent

The dedup hit rate across profiles shows a clean monotonic decrease from exact
repetition (0.98) to benign background (0.86–0.91) to templated variation (0.06–0.67)
to high diversity (0.05–0.075). This range reflects the design of the workloads, not
a novel finding — but it confirms that the workload classes are doing what they are
designed to do and that the dedup mechanism is correctly tracking input novelty.

The wide range in templated variation (0.06 for soc_triage vs. 0.665 for fraud_abuse)
indicates that profile-specific template design affects how much variation the
templated workload actually produces. This is worth tracking: if some profiles
produce templated variation that is nearly as diverse as the high-diversity workload,
the distinction between Workloads C and D may be weaker for those profiles.

### Clustering is more robust than deduplication but still degrades

Cluster hit rates are consistently higher than dedup hit rates for templated and
background workloads, confirming that Jaccard-based clustering provides meaningful
compression beyond exact matching. For high-diversity workloads, cluster hit rates
fall to 0.21–0.27 — low, but not zero. The window of 128 recent token sets retains
some overlap signal even against high-diversity inputs.

The question is whether 0.21–0.27 cluster compression is enough to matter. At 27%
cluster compression, the average processing cost is reduced by roughly 39% for those
hits (0.61x multiplier). Applied to 27% of inputs, the net processing cost reduction
from clustering is approximately 10% of total load. Whether this is meaningful
depends on the absolute cost level, which requires the Phase 2 realistic cost model.

### Sentinel preservation is robust under current conditions, for the right reasons

The 1.0 sentinel preservation rate in all baseline runs is plausible and expected,
for reasons documented in `results/sentinel_preservation_notes.md`. Sentinels contain
multiple profile-specific high-priority keywords, receive a +0.2 score boost, and
face no queue pressure or prefilter rejection. The 1.0 rate is not evidence that the
pipeline is resilient to adversarial load; it is evidence that the harness correctly
implements sentinel detection in the absence of stress conditions.

### Per-stage timing establishes the cost attribution baseline

Stage timing averages for the SOC triage profile across workloads:

| Workload | intake_ms | prefilter_ms | feature_ms | classifier_ms |
|---|---|---|---|---|
| exact_repetition | 0.165 | 0.228 | 1.418 | 0.270 |
| templated_variation | 0.242 | 0.338 | 2.375 | 0.550 |
| high_diversity | 0.409 | 0.583 | 4.549 | 1.364 |

Feature extraction is the dominant cost stage across all workloads, and its cost
increases by 3.2x from exact repetition to high diversity. This reflects the design
of the cost model: `feature_ms` scales with unique token count, which increases with
diversity. Classifier cost increases by 5x over the same range, suggesting that the
classifier is more sensitive to input diversity than the feature extraction stage.

These are model-derived figures. The relative ordering and scaling directions are
meaningful; the absolute values are not.

---

## 4. What the Preliminary Result Structure Is Expected to Show

Based on the benchmark design, model properties, and the hypotheses stated in the
whitepaper, we expect the Phase 1 experiment sweep to produce the following
structural pattern. These are predictions, not results.

### H1 (Baseline asymmetry): Expected to hold weakly at current scale

The simulated processing cost will exceed the simulated generation cost across all
workload types and all profiles. The asymmetry will be large in the current harness
because generation cost is measured as character iteration rather than realistic
generation. Once realistic generation costs are incorporated, the ratio will decrease
significantly. The Phase 1 sweep will establish the ratio under the current
measurement model as a structural baseline.

### H2 (Diversity resistance): Expected to hold against exact dedup, partially against clustering

High-diversity workloads will show substantially lower dedup hit rates than templated
variation workloads across all profiles (already confirmed in baseline). Against
semantic clustering, high-diversity workloads will show lower hit rates than
templated variation, but the gap will be smaller. The key question is whether that
smaller gap translates to meaningfully higher per-input processing costs. Based on
current baseline figures, the processing cost difference between high-diversity and
templated variation is approximately 1.9x (7.5 vs. 3.9 ms in the SOC profile). This
is a model-derived estimate pending controlled experimentation.

### H3 (False-negative drift): Cannot be evaluated at current scale

Sentinel drift requires queue saturation, which does not occur at 200 inputs at 15/sec.
Phase 1 results will show a flat 1.0 preservation rate across all workloads. This is
a measurement limitation, not a finding. The experiment design needs a higher input
rate or explicit queue depth forcing before H3 can be evaluated.

### H4 (Cross-domain generalization): Likely to hold structurally

The three profiles share the same pipeline model and differ only in parameterization.
Any structural feature of the asymmetry — such as the workload-diversity effect on
dedup and clustering hit rates — will appear in all three profiles. Profile-specific
differences in absolute cost figures will reflect the parameterization choices rather
than fundamentally different dynamics. The Phase 1 sweep will confirm or refute this
expectation.

---

## 5. What This Memo Does Not Predict

- Whether the asymmetry is large enough to matter in any real operational context.
  The current harness cannot answer this question.
- Whether semantic defenses beyond Jaccard clustering (embedding-based similarity,
  learned classifiers) can collapse the asymmetry more effectively than the current
  model suggests.
- Whether the high-diversity generation strategy in `workloads.py` represents a
  meaningful adversarial advance over templated variation, or whether the difference
  is a modeling artifact.
- Whether any of these effects scale. All current claims apply to 200-input runs on
  a single machine.

---

## 6. Open Questions for the Experiment Sweep

The following questions should be answerable from the Phase 1 sweep:

1. Does the dedup hit rate for high-diversity workloads change materially when
   clustering is disabled? (Tests whether clustering adds independent compression
   or merely reinforces dedup.)
2. Does the per-input processing cost increase monotonically with input rate, or
   does the cost model saturate?
3. Are there any cross-profile differences in dedup or clustering effectiveness that
   cannot be explained by template diversity alone?
4. What is the effective cost ratio between generating one high-diversity input and
   processing it, using a more realistic generation cost measurement?

These are questions with measurable answers under the current harness configuration.
Questions that require realistic inference costs, queue saturation modeling, or
multi-machine scale are Phase 2 objectives.

---

## 7. Relationship to the Whitepaper

This memo is a companion to `docs/whitepaper_stub.md`, Section 7. The whitepaper's
results section contains bracketed placeholders where empirical data will go. This
memo provides the interpretive frame for those placeholders: what each result means,
what its limitations are, and what would constitute a surprising versus expected
finding.

When Phase 1 results are available, this memo should be updated with a summary of
whether the predicted patterns were confirmed, partially confirmed, or refuted, along
with the observed figures. It then serves as the pre-registration record that
establishes the methodology and predictions were fixed before the data was collected.

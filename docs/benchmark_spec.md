# Benchmark Specification: Benign Intake Cost Evaluation

**Status:** Draft v0.1  
**Purpose:** Define a local, reproducible harness for testing whether intake-cost
asymmetry exists at all under controlled conditions.

---

## Objective

Measure whether coherent but low-actionability inputs can create higher processing cost
for a synthetic classification pipeline than they cost to generate.

This benchmark is explicitly scoped to:
- local execution
- open models or lightweight heuristics
- synthetic workloads
- defender-oriented evaluation

It should, however, support multiple defensive-domain abstractions rather than a
single scenario.

---

## Core Question

For a fixed budget of generated inputs, what happens to:
- per-input processing cost
- end-to-end latency
- queue depth
- prioritization quality

as input volume and diversity increase?

---

## Benchmark Architecture

The initial benchmark should use a toy but realistic-enough pipeline:

```
[Input Generator]
        ↓
[Intake Validation / Normalization]
        ↓
[Low-Cost Prefilter]
        ↓
[Embedding or Feature Extraction]
        ↓
[Classifier / Relevance Scorer]
        ↓
[Triage Queue]
        ↓
[Metrics Logger]
```

Each stage should be measurable in isolation.

---

## Defensive-Domain Profiles

The harness should support at least three profiles with the same measurement layer:

### Profile A: SOC / Threat Triage
- Inputs resemble alerts, reports, or event summaries
- Priority depends on suspiciousness and analyst-routing value
- Sentinel items represent genuinely important alerts

### Profile B: Trust and Safety Moderation
- Inputs resemble reports, flagged content summaries, or moderation events
- Priority depends on severity and confidence
- Sentinel items represent clear harmful-policy violations

### Profile C: Fraud / Abuse Review
- Inputs resemble transaction narratives, device-risk notes, or abuse reports
- Priority depends on loss-risk or abuse-likelihood
- Sentinel items represent true high-risk cases

Additional profiles can be added later, but these three are enough to test whether
the thesis generalizes beyond one narrative frame.

---

## Workload Classes

The benchmark should compare at least four workload classes:

### A. Benign Background
Ordinary low-volume inputs used to establish baseline latency and throughput.

### B. Exact Repetition
Identical repeated inputs used to measure the effectiveness of trivial deduplication.

### C. Templated Variation
Inputs generated from a small family of prompt templates with parameter substitution.

### D. High-Diversity Variation
Inputs generated from a more expressive mechanism, such as a reservoir-inspired state
generator or a strong randomized prompt family.

The point is not to assume class D wins. The point is to measure whether it adds
anything beyond class C.

---

## Measured Variables

Record at minimum:

- generation latency per input
- generation CPU time per input
- processing latency per input
- processing CPU time per input
- peak and average memory use
- queue depth over time
- accepted-input rate after prefiltering
- deduplication hit rate
- classifier score distribution
- false-negative rate on seeded high-priority benign items

If a metric cannot be collected reliably, omit it rather than inventing a proxy.

---

## Independent Variables

Vary these intentionally:

- input rate
- workload mix
- diversity method
- classifier model size or complexity
- prefilter enabled vs. disabled
- semantic clustering enabled vs. disabled
- cache window size

Change one variable at a time before testing combinations.

---

## Seeded Sentinel Inputs

Each run should include a small number of known high-priority benign inputs inserted
at fixed or randomized intervals.

Purpose:
- detect false-negative drift
- measure time-to-triage under pressure
- verify whether queue saturation affects meaningful inputs

These sentinels should be human-readable, harmless, and stable across repeated runs.

---

## Success and Failure Conditions

### Evidence Supporting the Thesis

- Processing cost remains materially above generation cost across sustained runs.
- Queue depth or triage delay grows under coherent diverse inputs.
- Cheap exact-match defenses fail, but stronger semantic defenses impose meaningful
  tradeoffs.

### Evidence Against the Thesis

- Processing cost is close to or below generation cost.
- Low-cost prefilters collapse the effect with little collateral damage.
- High-diversity generation is not meaningfully harder to collapse than template
  variation.
- Sentinel-input handling remains stable even under heavy benign load.

Negative results are valuable and should be written up explicitly.

---

## Baseline Experiments

Minimum experiment set for Phase 1:

1. Baseline pipeline with benign background only
2. Exact repetition against deduplication on/off
3. Templated variation against semantic clustering on/off
4. High-diversity variation against semantic clustering on/off
5. Mixed workload with sentinel inputs and queue measurement
6. Repeat experiments 1 to 5 across at least three defensive-domain profiles

Each experiment should be repeated enough times to estimate variance.

---

## Reporting Format

Every benchmark run should produce:

- environment summary
- model or heuristic configuration
- run duration
- workload composition
- key metrics table
- short interpretation
- failure notes

Prefer a simple CSV or JSON result format plus one Markdown summary per experiment set.

---

## Threats to Validity

- Synthetic pipelines may understate or overstate real intake costs.
- Open-model behavior may not resemble production classifier stacks.
- Diversity measured in embeddings may not reflect classifier internals.
- Small local runs may hide scaling breakpoints.
- Poor metric instrumentation may fabricate asymmetry that is not real.

These validity limits should be reported with every benchmark summary.

---

## Implementation Guidance

Keep the first harness simple:

- one machine
- one generator process
- one pipeline process
- deterministic config files
- repeatable random seeds

Do not optimize for scale until the baseline question is answered.

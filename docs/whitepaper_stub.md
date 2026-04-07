# AI Whisperer: Intake-Cost Asymmetry as a Defensive Research Problem

**Status:** Draft v0.2  
**Date:** April 2026  
**Classification:** Unclassified / Public Research

---

## Abstract

AI-driven classification pipelines — whether deployed for security operations,
content moderation, fraud detection, or surveillance — share a structural invariant:
no input can be dismissed without first being processed. This paper presents the AI
Whisperer framework, a defender-oriented research program that investigates whether
this invariant creates a measurable intake-cost asymmetry exploitable as a
countermeasure against adversarial AI pipelines. The central claim is that generating
a coherent, low-actionability input is cheaper than classifying it, and that this gap
can be sustained at scale using diversity strategies that defeat cheap defenses such as
exact deduplication. We describe the threat model, formalize four testable hypotheses,
present a benchmark methodology grounded in a working harness, and characterize the
defender countermeasures that the research must survive before the thesis is taken
seriously. We do not claim the asymmetry is large, persistent, or generalizable across
all pipeline types. We claim it is worth measuring carefully, that the measurement
apparatus now exists, and that negative results are as valuable as positive ones.

---

## 1. Problem Framing

### 1.1 The Intake Invariant

Any classification pipeline that acts on inputs from an open environment must perform
some processing before determining that an input is irrelevant. The sequence is:

```
[Intake / Normalization] → [Feature Extraction] → [Classification] → [Triage]
```

This sequence is not a software design choice. It is a logical requirement: you
cannot decide that something is not a threat without determining what it is. There is
no architectural skip path from intake to action. Even the cheapest possible prefilter
— a token blocklist, a rate limiter, an exact-match cache — consumes resources and
introduces latency for every input it touches, including inputs it ultimately rejects.

We term this the intake invariant. It is not a vulnerability in the conventional
sense. There is no CVE number, no patch, and no vendor to notify. It is a structural
property of all systems that must classify before they can act.

### 1.2 The Asymmetry Hypothesis

The intake invariant is only a research problem if a useful cost gap exists between
generating an input and processing it. We define **intake-cost asymmetry** as the
condition where:

> The expected compute cost of generating one candidate input is strictly less than
> the expected compute cost of processing that input through a defender's pipeline.

This condition exists trivially in many settings — generating a string is cheaper
than running a transformer over it. What matters is whether the gap is large enough
to sustain meaningful queue pressure, whether diversity strategies can prevent cheap
defenses from collapsing it, and whether the effect persists when real-world
countermeasures are deployed.

None of these questions have been answered for the full range of defensive pipeline
types. This project exists to answer them, or to discover which answers require
conditions that do not hold.

### 1.3 Scope and Non-Goals

This work is defensive research. The relevant question in every section is: what
should defenders understand about intake brittleness, and what controls actually work?

This paper does not:
- Provide operational guidance for deploying adversarial inputs against real systems.
- Characterize specific adversary implementations.
- Claim the asymmetry is large enough to matter in production without evidence.
- Treat the nation-state surveillance use case as the only or primary application
  domain.

The benchmark harness operates entirely in synthetic, local environments against
open-weight models and parameterized heuristics. No real-world systems are involved.

---

## 2. Threat Model

### 2.1 Target Pipeline Model

We model the target as a generic AI classification pipeline with the following stages:

```
[Signal Collection Surface]
        ↓
[Intake / Normalization]       ← primary cost surface
        ↓
[Feature Extraction]           ← secondary cost surface
        ↓
[Classification Engine]
        ↓
[Triage / Prioritization]
        ↓
[Analyst / Action Layer]
```

The research targets the first two stages. If intake is sufficiently loaded, the
classification and triage stages may receive degraded or delayed input regardless of
their own efficiency. The analyst or action layer is outside scope.

### 2.2 Explicit Assumptions

The model assumes:

1. The pipeline processes inputs sequentially or with bounded parallelism.
2. Feature extraction and classification are more expensive per input than intake
   normalization alone.
3. The pipeline cannot cheaply determine input quality without performing substantial
   processing.
4. The generator has no privileged access to the target pipeline's internals.

Assumption 3 is the one most likely to fail in practice. Systems with well-calibrated
lightweight prefilters may be able to reject low-quality inputs cheaply. Measuring
the conditions under which this assumption holds is a core research objective.

### 2.3 Defender Threat Scenarios

We consider three scenarios that share the same pipeline model but differ in
operational context. These are presented to motivate the research, not as operational
targets.

**Scenario A: SOC / Threat-Intel Triage.** An analyst queue receives alerts, event
summaries, and incident reports. The threat is that a high volume of coherent but
low-actionability inputs degrades analyst throughput and increases time-to-triage for
real incidents.

**Scenario B: Trust and Safety Moderation.** A moderation pipeline receives user
reports and automated policy flags. The threat is reviewer overload and delayed
handling of severe reports when lower-value reports dominate the queue.

**Scenario C: Fraud and Abuse Review.** A risk pipeline receives transaction
narratives, account-anomaly notes, and abuse reports. The threat is that coherent
low-risk inputs delay intervention on high-confidence fraud cases.

These three scenarios are used to structure the benchmark's defender profile system,
described in Section 5. The research must show results that generalize across at least
these three before the thesis is taken seriously.

### 2.4 Countermeasure Surface

A defender with knowledge of this threat model has several candidate controls. We
list them here to establish what the benchmark must stress-test, not to claim they
fail:

| Control | Expected Benefit | Potential Failure Mode |
|---|---|---|
| Rate limiting | Reduces burst pressure | Crude thresholds drop benign spikes |
| Exact deduplication | Eliminates repeated work | Fails on semantically similar variation |
| Semantic clustering | Collapses near-duplicate processing | Aggressive clustering merges distinct cases |
| Embedding cache | Avoids repeated inference | Cache misses rise with diversity |
| Lightweight prefilter | Rejects low-value inputs early | Poor calibration creates false negatives |
| Queue partitioning | Protects priority classes | Requires reliable priority assignment |
| Elastic compute | Buys time during bursts | May be economically unsustainable |

The project is only useful if these controls do not trivially collapse the asymmetry
in synthetic environments. If they do, that is the result, and it is worth reporting.

---

## 3. Hypotheses

We state the research hypotheses in explicit, testable form. Each is attached to a
specific experiment track in the benchmark.

**H1 (Baseline asymmetry).** Under benign background load and with all defenses
enabled, the simulated processing cost per input exceeds the generation cost per
input by a measurable margin.

*Falsification condition:* Processing cost is at or below generation cost, or the
margin is within measurement noise.

**H2 (Diversity resistance).** High-diversity inputs resist deduplication and
semantic clustering more effectively than exact-repetition or templated-variation
inputs. The asymmetry is preserved or grows under high-diversity load when defenses
are enabled.

*Falsification condition:* Semantic clustering collapses high-diversity load as
effectively as it collapses templated variation, without meaningful collateral damage
to sentinel inputs.

**H3 (False-negative drift).** As input volume and diversity increase, the rate at
which sentinel inputs (known high-priority inputs) are correctly prioritized
decreases. Queue saturation or classifier score compression causes high-value inputs
to be missed or delayed.

*Falsification condition:* Sentinel preservation rate remains stable across load
levels in the benchmark harness.

**H4 (Cross-domain generalization).** The asymmetry pattern, where it exists,
appears in at least two of the three defender profile domains (SOC triage, trust and
safety, fraud and abuse), ruling out single-domain artifact explanations.

*Falsification condition:* Effects appear in only one profile and are attributable to
profile-specific parameterization rather than the underlying pipeline model.

These hypotheses are presented in order of increasing specificity. H1 is the
necessary precondition for H2, H2 is the precondition for H3, and H4 is a robustness
check on all three.

---

## 4. Benchmark Methodology

See Section 5 for the full benchmark specification. This section provides a narrative
summary for readers who prefer the experimental design in context.

### 4.1 Overview

We constructed a synthetic evaluation harness (`src/aiwhisperer_core/`) that
implements a simplified but instrumented version of the generic pipeline model from
Section 2.1. The harness is written in Python using only the standard library. It is
deterministic given a fixed random seed and designed to be reproduced on a single
machine.

The harness does not simulate a specific real-world system. It implements the
invariant structure — intake, prefilter, feature extraction, classification, triage —
using cost models calibrated to approximate the relative expense of each stage. The
goal is not accuracy to any particular production system; it is to isolate the
structural question of whether intake asymmetry exists at all under controlled
conditions.

### 4.2 Pipeline Stages

The pipeline is implemented in `pipeline.py` as the `SyntheticPipeline` class. It
processes each input through four instrumented stages:

**Intake / Normalization.** Raw text is tokenized using a lowercase alphanumeric
regex. The stage records `intake_ms`, modeled as a linear function of token count:
`0.3 + token_count * 0.005 ms`. This reflects the real property that longer inputs
cost more to normalize.

**Low-Cost Prefilter.** A lightweight filter checks token count against a
profile-specific minimum and tests for blocklisted tokens. Inputs that fail are
rejected here, before feature extraction. `prefilter_ms` is modeled as
`0.4 + token_count * 0.008 ms`. The prefilter is cheap relative to downstream stages
by design — this represents the most favorable possible case for the defender.

**Feature Extraction.** Token-level features are computed. Cost is modeled as
`log2(token_count) * 0.6 + unique_token_count * 0.07 ms`, which captures the
sub-linear scaling of sequence processing and the additional cost of lexical richness.
This stage produces the token-set representation used by the deduplication and
clustering subsystems.

**Classification.** A parameterized scorer assigns a relevance score based on
keyword matches, a diversity bonus, and profile-specific bias and scale factors.
`classifier_ms` is modeled as `token_count^1.08 * 0.035 + classifier_bias * 0.2 ms`.
The super-linear token scaling reflects the empirical cost profile of transformer
inference at small sequence lengths.

Each stage records timing independently, allowing per-stage cost attribution in
experiment summaries. The `benchmark.py` module's `summarize_run` function reports
`stage_timing_ms` averages across all inputs in a run.

### 4.3 Deduplication and Semantic Clustering

The pipeline implements two defensive controls as toggleable options:

**Exact deduplication.** A SHA-256 fingerprint of the full input text is stored in
a set. If an input's fingerprint has been seen before, the pipeline applies a 0.32x
cost multiplier — reflecting the cost of the cache lookup but avoiding full-stage
processing. The dedup hit rate is reported per run.

**Semantic clustering (Jaccard-based).** A sliding window of up to 128 recent token
sets is maintained. An incoming input's token set is compared against all cached sets
using Jaccard similarity. If any comparison exceeds the 0.82 threshold, the input is
treated as a cluster hit and processing cost is reduced to 0.61x. Cluster hits also
reduce the classifier score by 0.15, reflecting the assumption that near-duplicate
inputs carry less marginal information.

The 0.82 Jaccard threshold and the 128-window size are configurable starting points
pending empirical calibration. The benchmark explicitly tests what happens when these
controls are disabled, to measure the counterfactual cost.

### 4.4 Workload Classes

The harness in `workloads.py` implements four workload classes, each testing a
different point on the diversity spectrum:

**Workload A: Benign Background.** Inputs are rendered from a small set of
profile-specific templates with randomized parameter substitution. This is the
baseline: inputs are varied enough to avoid trivial deduplication but constrained
enough that semantic clustering is effective. It establishes the cost floor under
normal operating conditions.

**Workload B: Exact Repetition.** A single fixed input text is repeated across all
positions. This tests the lower bound of processing cost when deduplication is
enabled and the upper bound of deduplication effectiveness. It establishes the cost
floor achievable by the cheapest possible defense.

**Workload C: Templated Variation.** Inputs are generated from the same template
family as the background workload, but a variation suffix is appended from a small
set of phrasing alternatives. This produces lexically distinct inputs that share
structural patterns. It tests whether semantic clustering can collapse moderate
variation before it reaches the classifier.

**Workload D: High-Diversity Variation.** Inputs are rendered from randomized
template combinations with variation suffixes, then augmented with supplemental
phrases drawn from an independent vocabulary set. The result is inputs that are
coherent and grammatical but have low lexical overlap with each other. This workload
is designed to stress the deduplication and clustering defenses. It is the closest
approximation in the current harness to an adversarially crafted input stream.

The comparison between Workloads C and D is the methodological core of H2: does
high-diversity generation add processing burden beyond what templated variation
already creates, given that both must pass the same defenses?

### 4.5 Sentinel Inputs

Each benchmark run includes a small number of sentinel inputs — known high-priority
items inserted at regular intervals. Sentinels are purpose-built human-readable texts
that contain multiple profile-specific high-priority keywords and represent the kind
of input the pipeline must not miss: a clear privilege escalation alert in the SOC
profile, an explicit self-harm escalation in the trust and safety profile, a
confirmed account-takeover pattern in the fraud profile.

Sentinels are injected at a configurable interval (default: every 25th input) and are
tracked independently in the run summary. The sentinel preservation rate — the
fraction of sentinels that receive high-priority queue classification — is the primary
metric for H3.

The mechanism that makes sentinels meaningful as a test is that they compete with
background inputs for classifier score separation. If the score distribution of
background inputs shifts upward under load (either because high-diversity inputs
receive higher diversity bonuses or because the clustering penalty no longer applies),
the gap between sentinel scores and background scores narrows, and sentinel
preservation may degrade.

### 4.6 Compute Asymmetry as a Measurable Ratio

We define the compute asymmetry ratio for a given run as:

> R = mean processing CPU time per input / mean generation CPU time per input

In the current harness, generation cost (`avg_generation_cpu_ms`) is measured as the
CPU time to iterate over the characters of the generated text string — an intentional
lower bound on realistic generation cost. Processing cost (`avg_processing_cpu_ms`)
is the wall-clock CPU time for the full `SyntheticPipeline.process()` call.

An R value substantially above 1.0 indicates that processing is more expensive than
generation at the measured volume. An R value at or below 1.0 indicates the
asymmetry does not hold under the current conditions. Intermediate values between 1.0
and roughly 5.0 indicate the asymmetry exists but may be trivially collapsed by
simple defenses.

[RESULT: baseline asymmetry ratio measurements pending full experiment sweep. Initial
baseline runs across three profiles show avg_processing_cpu_ms in the 0.05–0.15 ms
range versus avg_generation_cpu_ms in the 0.003–0.007 ms range, suggesting R values
in the 10–22x range under the current harness cost model. These figures are artifacts
of the synthetic cost model and should not be interpreted as real-system measurements.]

### 4.7 Defender Domain Profiles

The harness supports multiple defender profiles, each configuring the pipeline with
domain-appropriate parameters. Three primary profiles are defined for Phase 1:

**Profile 1: SOC / Threat Triage** (`soc_triage`). The pipeline prioritizes security
event summaries and incident reports for analyst attention. Sentinel inputs represent
high-confidence malware detections, privilege escalation alerts, and lateral movement
indicators. The acceptable false-negative cost is high: missing a real incident has
severe consequences.

**Profile 2: Trust and Safety Moderation** (`trust_safety`). The pipeline prioritizes
user reports and automated policy flags for review capacity. Sentinel inputs represent
severe abuse reports and policy-critical content. The false-negative cost is also high,
with additional complexity from the heterogeneous character of harmful content.

**Profile 3: Fraud / Abuse Review** (`fraud_abuse`). The pipeline prioritizes
transaction-risk narratives and account-anomaly reports for intervention. Sentinel
inputs represent confirmed high-risk takeover patterns and corroborated fraud signals.
The false-negative cost is operationally measured in expected loss value.

Each profile specifies its own classifier bias, classification scale, keyword sets,
prefilter blocklist, queue priority threshold, and sentinel inputs. The same generator
interface and pipeline instrumentation apply to all profiles, making cross-profile
comparison valid.

---

## 5. Candidate Generation Strategies

The benchmark evaluates three distinct approaches to generating low-actionability
inputs, ordered from simplest to most complex:

### 5.1 Fixed Templates

The simplest generation strategy renders inputs from a small fixed template set with
randomized slot substitution. Templates are short declarative sentences in the
domain-appropriate register of each profile (alert summaries, report notes,
transaction narratives).

This strategy is effective against exact deduplication but is readily collapsed by
semantic clustering, since all rendered outputs share the token-set structure of the
underlying template. It serves as the lower bound of adversarial sophistication — if
the thesis cannot survive even this defense under fixed templates, stronger strategies
are unlikely to matter.

### 5.2 Prompt-Family Variation

Templated variation appends short modifying phrases drawn from a variation vocabulary,
producing a set of rendered inputs that share structural origins but differ in surface
token distribution. The harness's Workload C (`templated_variation`) implements this
strategy.

The question this strategy tests is whether surface variation — achieved without any
model or learned component — can meaningfully reduce the cluster hit rate relative to
fixed templates, and if so, at what cost to the defender's clustering defense.

### 5.3 Reservoir-Inspired Diversity

The most complex strategy under evaluation uses a higher-entropy generator that
combines multiple templates with cross-domain vocabulary fragments, producing inputs
with substantially lower pairwise Jaccard similarity. The harness's Workload D
(`high_diversity`) implements a simplified version of this strategy.

The reservoir layer concept — a fixed recurrent network that projects low-dimensional
generator state into a high-dimensional temporal representation — is a more
principled version of this approach, described in the architecture documents. However,
the glossary explicitly lists the reservoir layer as a hypothesis to be evaluated
against simpler baselines, not a presupposed necessity. The current benchmark is
designed to answer the prior question: does high-diversity generation, however
achieved, add measurable burden beyond what templated variation already creates?

If the answer is no, the reservoir layer architecture is premature. If the answer is
yes, it becomes a candidate for the generation mechanism that achieves it most
efficiently.

---

## 6. Defender Countermeasures

This section is a major part of the research, not a footnote. The framework's
defensive value lies in what defenders learn from watching these controls succeed and
fail.

### 6.1 Rate Limiting

A rate limiter at intake can cap input throughput, reducing queue pressure
mechanically. It is the cheapest-to-implement defense and requires no understanding
of input content.

Rate limiting's primary failure mode is threshold calibration. A limit set too
conservatively drops burst traffic that may include legitimate high-priority inputs. A
limit set too permissively provides insufficient protection against sustained
high-volume loads. The benchmark does not currently implement rate limiting as a
toggleable variable; it is a planned addition for Phase 2.

### 6.2 Exact Deduplication

SHA-256 fingerprint comparison eliminates repeated work on identical inputs. It is
the most effective defense against Workload B (exact repetition), achieving a hit
rate above 0.98 in baseline runs. Against Workload D (high-diversity), it is nearly
useless: the dedup hit rate falls to 0.05–0.08 in baseline measurements.

The critical finding from baseline runs is that deduplication effectiveness degrades
monotonically as input diversity increases. This is not a surprising result, but it
quantifies what "diversity defeats dedup" means in measurable terms: a 13-fold
increase in per-input processing cost between exact-repetition and high-diversity
workloads in the SOC triage profile, measured in simulated pipeline cost.

[RESULT: Cross-profile dedup hit rate comparison pending complete experiment sweep.]

### 6.3 Semantic Clustering

Jaccard-similarity clustering over a sliding window of recent token sets provides
meaningful compression even against templated variation. Cluster hit rates of 0.84–
0.95 are observed in baseline runs for benign background workloads. Against
high-diversity workloads, clustering compresses only 0.21–0.27 of inputs — a 3–4x
reduction in effectiveness compared to background workloads.

Clustering introduces a collateral risk not present in deduplication: it reduces the
classifier score for cluster-hit inputs, which can lower the scores of legitimate
inputs that happen to resemble recently seen items. The benchmark tracks this through
the false-negative drift metric on sentinel inputs.

The key open question — addressed in the research agenda but not yet answered — is
whether the 0.82 Jaccard threshold can be lowered enough to capture high-diversity
inputs without collaterally suppressing distinct legitimate inputs. This is a
precision-recall tradeoff with domain-specific stakes: in the fraud profile, the cost
of a false negative is measured in direct financial loss.

### 6.4 Embedding Cache and Lightweight Prefilter

An embedding cache avoids repeated inference on inputs whose feature representation
has already been computed. Its effectiveness tracks directly with input novelty: it
provides strong compression for low-diversity workloads and near-zero compression for
high-diversity workloads. It is modeled in the harness as a 0.44x cost multiplier on
cache hit.

The prefilter in the current harness checks token count and blocklist membership. It
is cheap and consistent but miscalibrated for the current experiment set: no inputs
in baseline runs are rejected by the prefilter, meaning it contributes no reduction
in classification load. This is an intentional property of the baseline workloads —
they are designed to pass prefilter checks. A more sophisticated prefilter, such as a
calibrated low-complexity classifier, is a planned extension.

### 6.5 Queue Partitioning

Queue partitioning protects high-priority inputs from being delayed by low-priority
volume. In the current harness, priority assignment is a direct function of the
classifier score threshold. If the classifier cannot reliably separate sentinel inputs
from background inputs under high diversity, queue partitioning provides no
protection — it depends on reliable classification as a precondition.

This dependency structure is important for H3: the sentinel preservation rate is a
joint measure of classifier accuracy and queue management, not a direct measure of
either in isolation.

---

## 7. Results

*Full experimental results are pending completion of the Phase 1 experiment sweep
described in the research agenda. This section presents the baseline characterization
from initial runs and the structural interpretation of what the benchmark design
reveals before empirical results exist.*

### 7.1 Baseline Pipeline Behavior

Initial baseline runs across three profiles (SOC triage, trust and safety, fraud and
abuse) with all defenses enabled and 200 inputs per run show:

- All inputs are accepted by the prefilter under benign and high-diversity workloads.
  No inputs are dropped in any run across all three profiles.
- Sentinel preservation rate is 1.0 across all runs and all workload types. Sentinels
  receive high-priority queue classification in 100% of cases.
- The deduplication hit rate varies dramatically by workload: 0.98 for exact
  repetition, 0.05–0.075 for high-diversity, confirming that diversity defeats
  exact-match defenses as expected.
- Per-input simulated processing cost ranges from approximately 2.4 ms (exact
  repetition, full dedup compression) to 7.5 ms (high-diversity, minimal compression).

[RESULT: baseline benchmark data from three profiles, 200 inputs each, seed=7,
all defenses enabled. Full sweep with defenses toggled pending.]

### 7.2 Interpretation Cautions

These baseline results are subject to three important cautions:

**The cost model is synthetic.** Simulated stage costs are parameterized heuristics,
not measurements of real inference workloads. The absolute cost figures are not
meaningful outside the benchmark context. The relative relationships — high diversity
costs more than low diversity, dedup compresses exact repetition effectively —
are structural features of the model, not empirical discoveries.

**The prefilter does not fire.** The current baseline workloads are designed to pass
prefilter checks. A well-calibrated prefilter that could identify and reject the
majority of low-actionability inputs before feature extraction would change the cost
calculus substantially. The experiment sweep includes prefilter-disabled runs to
measure the counterfactual.

**Queue saturation does not appear.** At 200 inputs at 15 inputs/second, queue depth
remains zero in all runs. The synthetic pipeline processes inputs faster than they
arrive at the test rate. Queue saturation — the condition most directly relevant to
H3 — requires either higher input rates, larger input counts, or explicit queueing
model modifications. This is on the Phase 2 agenda.

### 7.3 Planned Experiment Sweep

The minimum experiment set for Phase 1, as specified in `docs/benchmark_spec.md`:

1. Baseline pipeline with benign background only (completed).
2. Exact repetition against deduplication on/off.
3. Templated variation against semantic clustering on/off.
4. High-diversity variation against semantic clustering on/off.
5. Mixed workload with sentinel inputs and queue measurement.
6. Experiments 1–5 repeated across all three defender profiles.

Each experiment should be repeated with at least three seeds to estimate variance.

---

## 8. Policy and Governance

### 8.1 Classification of the Mechanism

This mechanism does not inject false data into any system, degrade hardware, or
constitute an armed attack under traditional legal definitions. It operates by
generating inputs that are processed under normal pipeline rules. Whether it
constitutes electronic warfare, cyber operations, or a novel category requiring
new legal framing is a policy question that is outside the scope of this paper but
must be addressed before any operational consideration.

The paper takes no position on operational deployment. The research is scoped
exclusively to defensive evaluation and countermeasure design.

### 8.2 Transferability Across Domains

The benchmark results should not be assumed to transfer automatically across the
three tested domains, and should be assumed to transfer even less reliably to
production systems. Each defender profile has domain-specific characteristics — cost
of false negatives, acceptable false-positive rates, input volume expectations —
that affect the practical significance of any asymmetry the benchmark reveals.

A result that holds in the SOC triage profile may not hold in the trust and safety
profile because trust and safety pipelines typically operate at higher input volumes
with more heterogeneous input distributions. Cross-domain comparison is a robustness
check, not a proof of universality.

### 8.3 Responsible Publication Boundary

Following the project safety scope, we do not publish:
- Target-specific operational guidance.
- Infrastructure fingerprinting workflows.
- Tactics whose primary effect is to increase offensive capability without
  corresponding defensive insight.

The full harness implementation and all benchmark results are published to enable
defender replication and countermeasure validation, not to enable offensive use.

---

## 9. Limitations

### 9.1 Synthetic Pipeline Limitations

The benchmark harness is not a simulation of any specific production system. It
implements a structural approximation of the cost relationships between pipeline
stages. The simulated cost functions are parameterized to produce plausible relative
relationships, but absolute cost figures are not meaningful outside the harness
context.

Synthetic pipelines may systematically understate or overstate real intake costs. In
particular, production classifier stacks that use large transformer models will have
substantially higher per-input inference costs than the harness's polynomial
approximations. This would make the asymmetry appear larger in production than in the
benchmark, which is a direction that the research should not count as a positive
result without empirical verification.

### 9.2 Model Mismatch

The harness uses keyword-based classification heuristics and Jaccard-similarity
clustering as proxies for semantic classification. Real production systems use dense
embeddings, attention-based models, or fine-tuned classifiers that may exhibit
substantially different cost profiles and sensitivity characteristics. The Jaccard
similarity threshold used for clustering (0.82) is an approximation of what a
semantic clustering step might achieve; real embedding-based clustering may be either
more or less effective at the same computational cost.

### 9.3 Scale Limitations

All current experiments use 200 inputs at 15 inputs/second on a single machine. This
volume is insufficient to observe queue saturation or backpressure effects. Scale
experiments — higher input rates, larger total counts, multi-run aggregation — are
required before claims about queue dynamics can be made with any confidence.

### 9.4 Measurement Validity

The generation cost measurement in the current harness is intentionally minimal: it
measures the CPU time to sum character ordinals over the generated string. This
significantly understates realistic generation cost (which would include template
rendering, random sampling, or model inference) and makes the asymmetry ratio appear
larger than it would be for realistic generators. This is a known limitation to be
addressed in Phase 2 by implementing a more realistic generation cost measurement.

---

## 10. Conclusion

We have presented the AI Whisperer framework as a defensive research program
investigating intake-cost asymmetry in AI classification pipelines. The framework
rests on a structural invariant — that no input can be dismissed without first being
processed — and asks whether this invariant can be exploited to create measurable
queue and compute pressure on systems that must classify before acting.

The current state of the work is:

- The threat model is formalized and the hypotheses are stated in testable form.
- A working benchmark harness exists, with four workload classes, three defender
  domain profiles, and configurable toggles for the primary defensive controls.
- Baseline runs have been completed and show plausible behavior: diversity defeats
  deduplication as expected, sentinel preservation is robust under current load
  conditions, and per-stage cost attribution is working as designed.
- The primary open questions — whether the asymmetry survives high-quality semantic
  defenses, whether sentinel drift appears under sustained load, and whether the
  effect generalizes across domains — have not yet been answered.

The project's success condition is not that the original thesis is confirmed. A strong
outcome is that the asymmetry claim is tested rigorously, that defenders learn where
intake pipelines are brittle, and that practical hardening guidance emerges from the
work regardless of whether the asymmetry turns out to be large, small, or
context-dependent. Negative results will be written up explicitly.

---

## References

- Jaeger, H. (2001). The "echo state" approach to analysing and training recurrent
  neural networks. GMD Technical Report 148, German National Research Center for
  Information Technology.
- Lukoševičius, M. (2012). A practical guide to applying echo state networks.
  In *Neural Networks: Tricks of the Trade*, Springer, LNCS 7700, pp. 659–686.
- Goodfellow, I., Shlens, J., and Szegedy, C. (2015). Explaining and harnessing
  adversarial examples. *ICLR 2015*.
- Vaswani, A., et al. (2017). Attention is all you need. *NeurIPS 2017*.
- Carlini, N., and Wagner, D. (2017). Towards evaluating the robustness of neural
  networks. *IEEE S&P 2017*.

*(Full bibliography to be populated on submission.)*

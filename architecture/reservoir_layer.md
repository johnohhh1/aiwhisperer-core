# Reservoir Layer Architecture

**Status:** Hypothesis stub v0.2  
**Component:** High-diversity motif generator (candidate)

---

## Overview

The reservoir layer is a proposed generator component whose job is to produce
parameterized input specifications — called motifs — such that no two batches of
inputs share a statistically detectable generating signature. Without this
property, the structure of the generator becomes a detectable fingerprint that
a defender's clustering or anomaly-detection system can exploit to batch-dismiss
entire input families.

Whether a reservoir-based generator is necessary, or whether simpler diversity
strategies achieve equivalent input-set properties at lower implementation cost,
is an open question. The benchmark harness (`src/aiwhisperer_core/workloads.py`)
is designed to test this directly by comparing high-diversity generation (Workload D)
against templated variation (Workload C). The reservoir layer is not implemented
until that comparison justifies it.

---

## Echo State Network Basics

A reservoir is a large, fixed, randomly connected recurrent network. Its relevant
properties for this application are:

**Echo state property.** The network's current hidden state is a decaying function
of the history of inputs it has received. Earlier inputs contribute progressively
less to the current state. This creates a finite temporal memory without requiring
any learned state management.

**High-dimensional projection.** A low-dimensional input vector is mapped to a
state vector in a space with dimensionality equal to the number of reservoir nodes
(N). For N = 10,000, a handful of input parameters produce a 10,000-dimensional
state representation. This large state space is what enables output diversity.

**Fixed internal weights; only output weights are trained.** The reservoir's
recurrent connection matrix is initialized randomly and never modified after
initialization. The only learned component is a linear readout layer that maps the
reservoir state to the desired output parameters. This makes training fast and
avoids the instability problems of backpropagation through recurrent networks.

These properties mean the reservoir's output sequence is:
1. Deterministic given a fixed input sequence and a fixed initialization seed.
2. Non-invertible in practice: recovering the input from the output state requires
   solving a high-dimensional system for which no shortcut is known.
3. Non-repeating over sequences long enough to matter operationally, given
   sufficient reservoir size and input entropy.

---

## Role in AI Whisperer

The proposed data flow for a reservoir-based generator is:

```
External entropy source (hardware RNG, atmospheric noise, timing jitter)
        ↓
[Echo State Network — N nodes, fixed random weights]
        ↓
High-dimensional state vector (dimension = N)
        ↓
[Motif Decoder — learned linear readout]
        ↓
Motif specification:
  - semantic domain (e.g., security-event, transaction-risk)
  - register and vocabulary constraints
  - temporal spacing parameter (input rate offset)
  - target coherence score (minimum threshold to pass prefilter)
```

The motif specification is then passed to the input generator, which renders a
concrete input text matching the specified parameters.

---

## Motif Decoder

The motif decoder is a learned linear mapping from reservoir state to motif
parameters. It is the only trained component in the system.

Training objective:

- Outputs should produce rendered inputs that score above the intake prefilter
  threshold (high coherence).
- Pairs of outputs from different input sequences should have low Jaccard similarity
  between their rendered token sets (high inter-motif diversity).
- The sequence of outputs should not exhibit periodicity detectable by a frequency
  analysis over any window of 10^6 or more positions (aperiodicity requirement).

These three objectives are in tension: higher coherence constraints narrow the
vocabulary, which reduces diversity. The training objective weights them by
application priority. The benchmark harness measures their joint outcome — not the
training process — by reporting dedup hit rate, cluster hit rate, and classifier
score distribution for each workload.

---

## Entropy Sourcing

The reservoir input sequence must be unpredictable by any party who could use
prediction to anticipate and cache expected outputs. Requirements:

- High min-entropy per input vector (hardware RNG preferred; minimum 128 bits
  effective entropy per update).
- Non-predictable by the defender even with access to all prior outputs.
- Refreshable without full re-initialization of the reservoir, to allow periodic
  seed rotation without disrupting continuity.

Candidate entropy sources in order of preference:
1. Hardware RNG (TPM 2.0 / RDRAND instruction).
2. Physical process measurement (atmospheric noise, photon counting).
3. Network timing jitter aggregated across many simultaneous connections.

The seed refresh frequency is a design parameter with a tradeoff: refreshing too
frequently reduces the echo state memory (recent inputs no longer influence current
state), which may reduce output coherence. Refreshing too infrequently risks
detectable periodicity if the input space is finite. The right refresh interval
depends on reservoir size and is an open calibration question.

---

## Relationship to the Benchmark Harness

The harness's `high_diversity` workload (Workload D in `workloads.py`) implements
a simplified version of the reservoir generator's intended behavior without using
an actual echo state network. It combines multiple template families with
cross-domain phrase fragments using a seeded PRNG, producing inputs with low
pairwise Jaccard similarity.

The benchmark comparison between Workload C (templated variation) and Workload D
(high diversity) is a direct test of whether the additional complexity of a
reservoir generator is justified. If the dedup hit rate, cluster hit rate, and
processing cost distribution for Workload D are not materially different from
Workload C, the reservoir layer adds no measurable benefit over simpler diversity
methods.

If Workload D does show measurably lower dedup and cluster compression rates with
no degradation in sentinel preservation, that is the precondition that motivates
implementing the full reservoir generator as the next architectural step.

---

## Open Design Questions

- What reservoir size (N) is required to maintain output diversity across 10^6+
  sequential motif specifications?
- Does the motif decoder need periodic retraining as the target pipeline's
  countermeasures evolve? If so, what is the minimum data requirement for an update
  cycle?
- What is the correct seed refresh interval, expressed as a function of reservoir
  size and the number of distinct motif domains?
- Is the computational cost of running a 10,000-node ESN at operational throughput
  rates feasible on commodity hardware?

These questions should not be addressed architecturally until the benchmark
comparison (Workload C vs. D) shows that a more sophisticated generator is needed.

---

## References

- Jaeger, H. (2001). The "echo state" approach to analysing and training recurrent
  neural networks. GMD Technical Report 148.
- Lukoševičius, M. (2012). A practical guide to applying echo state networks.
  In *Neural Networks: Tricks of the Trade*, Springer, LNCS 7700, pp. 659–686.

# Reservoir Layer Architecture

**Status:** Stub v0.1  
**Component:** Meta-motif generator for canon engine

---

## Overview

The reservoir layer is the entropy source for the entire AI Whisperer system. Its job
is to generate canon voice motifs such that no two rounds share a statistically
detectable generating signature. Without this layer, the round structure — which is
the offensive strength — becomes a detectable fingerprint.

---

## Echo State Network Basics

A reservoir is a large, fixed, randomly connected recurrent network. Key properties:

- **Echo state property:** current reservoir state is a fading function of input history
- **High-dimensional projection:** low-dimensional inputs mapped to rich temporal space
- **Only output weights are trained** — the reservoir itself is never modified

This means the reservoir's internal dynamics produce variation that is:
1. Deterministic given seed
2. Practically irreversible (cannot recover input from output)
3. Non-repeating over operationally relevant timescales

---

## Role in AI Whisperer

```
External seed (entropy source)
        ↓
[Echo State Network — N=10,000+ nodes]
        ↓
High-dimensional state vector
        ↓
[Motif Decoder] — maps state → semantic whisper parameters
        ↓
Canon voice specification:
  - semantic domain
  - tone/register
  - temporal phase offset
  - spatial target vector
  - coherence score target
```

---

## Motif Decoder

The motif decoder is a learned mapping from reservoir state to whisper parameters.
It is the only trained component in the system. Training objective:

- Maximize semantic coherence score (passes intake filters)
- Minimize inter-motif similarity (defeats round fingerprinting)
- Maintain aperiodicity over 10^6+ round cycles

---

## Entropy Sourcing

The reservoir seed must be:
- High-entropy (hardware RNG or physical process preferred)
- Non-predictable by adversary
- Refreshable without full system restart

Candidate sources:
- Hardware RNG (TPM, RDRAND)
- Atmospheric noise
- Network timing jitter at scale

---

## Open Design Questions

- Optimal reservoir size vs. motif diversity tradeoff
- Whether motif decoder needs periodic retraining against adversary classifier updates
- Seed refresh frequency — too frequent breaks echo state continuity, too infrequent
  risks motif periodicity detection

---

## References

- Jaeger, H. (2001) — The Echo State Approach to Recurrent Neural Networks
- Lukoševičius, M. (2012) — A Practical Guide to Applying Echo State Networks

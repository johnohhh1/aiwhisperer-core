# AI Whisperer Research Agenda

**Status:** Working draft v0.1  
**Purpose:** Turn the current concept into a defensible research program with explicit
decision gates, measurable claims, and domain-general evaluation criteria.

---

## Research Goal

Test whether semantic-noise saturation can create measurable compute and triage costs
for generic AI intake pipelines without requiring privileged access to the target
model.

This repo should answer one question before anything else:

**Can the claimed asymmetry be demonstrated in controlled, benign evaluation
environments?**

If the answer is no, the concept should be narrowed or abandoned quickly.

---

## Primary Hypotheses

### H1: Intake Cost Asymmetry Exists
Semantically coherent, low-actionability inputs should cost more to classify than to
generate.

### H2: Diversity Matters
A motif generator with sufficient temporal and semantic diversity should resist simple
deduplication, clustering, or cache-based mitigation better than fixed prompt sets.

### H3: Saturation Occurs Upstream
The strongest effects should appear at intake, normalization, feature extraction, or
triage layers before any human analyst stage.

### H4: Effects Must Generalize Across Domains
If the asymmetry is real, some version of it should appear across more than one intake
pipeline class rather than only in a hand-picked scenario.

### H5: Strong Cheap Defenses May Collapse the Effect
The concept only matters if low-cost countermeasures fail or impose meaningful
tradeoffs on defenders.

---

## Research Tracks

### 1. Formal Model
- Define the pipeline abstraction precisely: collection, intake, feature extraction,
  classification, triage.
- State what "attention saturation" means in measurable terms.
- Distinguish model compute cost, queueing delay, and analyst burden.

### 2. Evaluation Harness
- Build a local benchmark that compares generation cost against inference cost.
- Use open models and synthetic intake pipelines only.
- Record latency, throughput degradation, queue depth, and false-negative drift under
  controlled load.

### 3. Motif Diversity Study
- Compare fixed prompts, templated prompt families, and reservoir-driven motif output.
- Measure pairwise similarity, embedding-cluster collapse, and replay detectability.
- Identify the minimum diversity needed to defeat naive clustering defenses.

### 4. Defender Countermeasures
- Test rate limiting, semantic clustering, cache layers, deduplication, and low-cost
  prefilters.
- Treat countermeasures as first-class deliverables, not only adversary obstacles.
- Document where the concept fails cleanly under competent defensive design.

### 5. Domain Transfer Study
- Compare results across at least three pipeline classes.
- Identify which parts of the thesis are domain-specific and which generalize.
- Avoid treating one scenario as evidence for all classifier architectures.

---

## Phased Plan

### Phase 0: Terminology and Scope Lock
**Goal:** Remove ambiguity before any prototype work.

Deliverables:
- Canonical glossary for core terms
- Defensive scope statement
- Precise problem statement and non-goals

Exit criteria:
- A new reader can explain the thesis, the intended evidence, and the prohibited work
  after reading the repo for 10 minutes.

### Phase 1: Benign Baseline Harness
**Goal:** Prove or falsify cost asymmetry in a sandbox.

Deliverables:
- Local synthetic intake pipeline
- Baseline generator and classifier benchmarks
- Initial plots for generation cost vs. classification cost

Exit criteria:
- Reproducible benchmark showing whether asymmetry exists at all
- Clear statement of assumptions and limits

### Phase 2: Diversity Engine Evaluation
**Goal:** Determine whether the reservoir/canon concept adds measurable value over
simple prompt variation.

Deliverables:
- Motif generation candidates
- Similarity and detectability evaluation suite
- Comparative report against simpler baselines

Exit criteria:
- Evidence that the reservoir layer meaningfully improves diversity or resilience
- Or a decision to replace it with a simpler generator

### Phase 3: Defender Lens
**Goal:** Translate findings into defensive guidance.

Deliverables:
- Recommended intake hardening patterns
- Failure modes and mitigation catalogue
- Report on which defenses collapse the asymmetry
- Domain comparison notes showing where results transfer and where they do not

Exit criteria:
- The project yields practical defensive recommendations even if the original concept
  is weakened
- The repo can state clearly which defensive domains are affected and which are not

---

## Metrics That Matter

- Generation cost per accepted input
- Classification cost per input
- End-to-end latency increase under load
- Queue depth growth rate
- Deduplication success rate
- Embedding-space similarity distribution
- False-positive and false-negative drift
- Countermeasure cost to defender

Avoid vague success criteria such as "seems noisy" or "probably hard to filter."

---

## Immediate Backlog

1. Add a glossary so the architecture docs use consistent terms.
2. Convert open problems in the whitepaper into testable questions.
3. Define a toy intake pipeline for evaluation.
4. Write a benchmark spec before building any prototype.
5. Add a defender-countermeasure matrix to the threat model.
6. Define the first three defensive-domain benchmark profiles.

---

## Decision Gates

Stop or re-scope the project if any of the following are true:

- The generation/classification asymmetry is weak in realistic local benchmarks.
- Cheap prefilters collapse the effect with low collateral damage.
- The reservoir layer does not outperform simpler diversity methods.
- Results do not transfer across multiple pipeline classes.

---

## Research Discipline

Default to prioritizing:
- benchmark methodology
- negative results
- countermeasure analysis
- cross-domain comparison

Avoid:
- unverifiable claims
- single-domain overgeneralization
- rhetorical certainty without measurement

# Whitepaper Expansion Outline

**Status:** Draft v0.1  
**Purpose:** Turn `whitepaper_stub.md` into a publishable research note with stronger
methodology and less rhetorical drift.

---

## Proposed Structure

### 1. Abstract
- State the core claim narrowly.
- Emphasize that the current work is a defensive research hypothesis.
- Preview the benchmark and mitigation lens.

### 2. Problem Framing
- Define intake cost asymmetry precisely.
- Separate architectural invariants from speculative effects.
- Introduce the pipeline abstraction used throughout the paper.

### 3. Threat Model
- Summarize the intake/feature/classify/triage model.
- State assumptions explicitly.
- Include system boundaries and non-goals.

### 4. Hypotheses
- Present H1 through H4 in explicit, testable form.
- Tie each hypothesis to an experiment or research track.

### 5. Benchmark Methodology
- Describe the synthetic pipeline.
- Explain workload classes and sentinel inputs.
- Define success and falsification conditions.

### 6. Candidate Generation Strategies
- Fixed templates
- Prompt-family variation
- Reservoir-inspired diversity

This section should compare alternatives rather than presuppose the reservoir layer is
necessary.

### 7. Defender Countermeasures
- Rate limiting
- Deduplication
- Semantic clustering
- Low-cost prefilters
- Queue partitioning

This should be a major section, not an appendix.

### 8. Results and Interpretation
- Present measured asymmetry or lack thereof.
- Discuss false-negative drift, queue growth, and mitigation effectiveness.
- State clearly where the idea fails if the data says it fails.

### 9. Policy and Governance
- Domain boundaries and assumptions
- What transfers across defensive settings and what does not
- Legal classification questions only if they affect deployment or publication claims

### 10. Limitations
- Synthetic environment limitations
- Model mismatch limitations
- Uncertain transfer to production systems

### 11. Conclusion
- Summarize what was shown
- Summarize what remains hypothetical
- Emphasize defender takeaways

---

## Writing Rules

- Prefer measurable language over dramatic language.
- Replace metaphor with defined terms where possible.
- Mark speculation explicitly.
- Keep every claim attached to either an invariant, an assumption, or a planned test.
- Do not let one use case stand in for all defensive settings.

---

## Missing Inputs Before Draft Expansion

- Glossary completion
- Benchmark specification signoff
- Initial countermeasure matrix
- At least one toy experiment result, even if negative

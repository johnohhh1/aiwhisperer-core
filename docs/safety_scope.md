# Safety Scope

**Status:** Draft v0.1  
**Purpose:** Keep the project aligned to defensive research, controlled evaluation,
and policy analysis.

---

## Allowed Work

- Threat modeling at the architectural level
- Controlled benchmarking against local or synthetic pipelines
- Analysis of compute asymmetry in toy environments
- Research on defensive mitigations and intake hardening
- Policy, legal, and governance framing

---

## Prohibited Work

- Target-specific operational planning
- Guidance for deployment against real-world systems
- Infrastructure fingerprinting workflows for live targets
- Instructions for evading attribution or enforcement
- Publication of tactics whose main effect is to enable misuse

---

## Review Questions

Before adding a new document or prototype, ask:

1. Does this materially help a defender understand the risk or mitigation?
2. Could this be executed safely in a closed local environment?
3. Would publishing this increase offensive capability more than defensive insight?

If the answer to question 3 is yes, do not add it in public form.

---

## Project Posture

This repository should aim to become useful even if the original thesis is partly
wrong. A strong outcome is not "the concept works exactly as imagined." A strong
outcome is:

- the asymmetry claim is tested rigorously
- defenders learn where intake pipelines are brittle
- practical hardening guidance emerges from the work

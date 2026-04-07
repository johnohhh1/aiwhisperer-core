# Defender Profiles

**Status:** Draft v0.1  
**Purpose:** Define the first cross-domain benchmark abstractions so the project does
not collapse into a single narrative use case.

---

## Why This Exists

If the project is about defense broadly, the research has to survive contact with more
than one pipeline type. A result that appears only in one handcrafted scenario is weak.

This document defines the first benchmark profiles that should share a common harness
while varying:
- input shape
- triage objective
- sentinel definition
- acceptable false-negative cost

---

## Profile 1: SOC / Threat Triage

**Pipeline purpose**  
Prioritize security events, incident reports, and suspicious activity for analyst
attention.

**Representative inputs**
- alert summaries
- event narratives
- suspicious login reports
- endpoint risk notes

**Triage objective**
- surface likely incidents quickly
- suppress low-value repetitive noise

**Sentinel examples**
- a clear privilege-escalation alert
- repeated anomalous authentication tied to one identity
- a concise high-confidence malware-detection summary

**Primary failure risks**
- analyst backlog
- buried high-confidence incidents
- over-clustering distinct incident threads

---

## Profile 2: Trust and Safety Moderation

**Pipeline purpose**  
Prioritize content or account reports for review under platform policy.

**Representative inputs**
- user reports
- content summaries
- automated policy flags
- account-behavior notes

**Triage objective**
- surface severe, policy-relevant cases rapidly
- avoid wasting review capacity on low-value repetitive reports

**Sentinel examples**
- explicit high-severity abuse report
- credible coordinated-harassment signal
- repeated child-safety or self-harm escalation flag

**Primary failure risks**
- delayed handling of severe abuse
- reviewer overload
- aggressive clustering that hides distinct victims or contexts

---

## Profile 3: Fraud / Abuse Review

**Pipeline purpose**  
Prioritize risky transactions, abuse reports, or account anomalies for intervention.

**Representative inputs**
- payment-risk notes
- account-takeover reports
- promo-abuse indicators
- device-fingerprint anomalies

**Triage objective**
- surface high-loss or high-confidence abuse cases
- keep routine noise cheap to dismiss

**Sentinel examples**
- likely account takeover with corroborating signals
- high-risk transaction narrative with multiple anomaly flags
- confirmed refund or bonus-abuse pattern

**Primary failure risks**
- delayed intervention on real loss events
- review-cost inflation
- false-negative drift under mixed low-value load

---

## Shared Harness Requirements

All profiles should support:

- the same generator interface
- the same intake and prefilter instrumentation
- the same queue-depth metrics
- the same deduplication and clustering toggles
- profile-specific sentinel inputs

This keeps the benchmark comparable while allowing different domains to express
different notions of priority and harm.

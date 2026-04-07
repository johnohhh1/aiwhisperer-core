# AI Whisperer Glossary

**Status:** Draft v0.1  
**Purpose:** Standardize terminology across theory, architecture, and evaluation
documents.

---

## Core Terms

**Accepted input**  
An input that survives initial syntactic checks and is processed by the benchmark
pipeline's classifier or triage stages.

**Actionability**  
The degree to which an input supports a downstream decision or response. In this repo,
"low-actionability" means an input may appear coherent while providing little value
for prioritization or action.

**Attention saturation**  
A condition where limited intake, feature extraction, or classification resources are
consumed by inputs that are individually processable but collectively degrade system
throughput, latency, or prioritization quality.

**Benign evaluation environment**  
A local, synthetic, or otherwise closed test setting that does not interact with
real-world target systems and is used only for measurement, validation, and defense
research.

**Canon engine**  
The scheduling layer that coordinates multiple motif instances over time. In the
public research version of this repo, it is a conceptual component until benchmark
evidence justifies implementation.

**Classification cost**  
The compute, latency, and memory burden required for a pipeline to process an input
through feature extraction, model inference, and any downstream scoring relevant to
the benchmark.

**Coherence**  
The degree to which an input appears internally consistent, syntactically valid, and
semantically plausible to a classifier or heuristic filter.

**Countermeasure**  
A defensive mechanism that reduces intake burden, collapses duplicate work, or lowers
the cost of rejecting low-value inputs.

**Deduplication**  
A defensive process that detects exact or near-exact repetition and avoids paying full
processing cost more than once.

**Diversity**  
The extent to which a set of inputs differs across lexical, semantic, temporal, or
structural dimensions relevant to clustering or caching defenses.

**False-negative drift**  
A degradation mode where valid high-priority inputs are increasingly missed, delayed,
or deprioritized as intake pressure rises.

**Feature extraction**  
The stage between raw intake and classification where tokens, embeddings, metadata, or
engineered features are derived for later scoring.

**Generation cost**  
The compute, latency, and memory burden required to produce one candidate input in the
benchmark environment.

**Input pipeline**  
The end-to-end path by which candidate inputs are received, normalized, scored, and
prioritized.

**Intake**  
The earliest stage that accepts an input into the system and performs validation,
normalization, routing, or lightweight filtering.

**Intake cost asymmetry**  
A condition where generating an input is cheaper than processing it through the target
pipeline model used in the benchmark.

**Low-cost prefilter**  
A cheap defensive layer intended to reject malformed, repetitive, or obviously
low-value inputs before expensive inference occurs.

**Motif**  
A parameterized family of coherent inputs sharing a conceptual pattern. In this repo,
motifs are a unit of analysis, not an operational payload.

**Motif decoder**  
The component that maps internal generator state into motif parameters such as domain,
style, or coherence target.

**Normalization**  
The transformation of raw inputs into a canonical format suitable for feature
extraction and scoring.

**Queue depth**  
The number of inputs waiting to be processed at a given stage of the benchmark
pipeline.

**Reservoir layer**  
A proposed high-dimensional temporal generator used to create diverse motif states. It
is currently a hypothesis to be evaluated against simpler baselines.

**Semantic similarity clustering**  
A defense that groups inputs by embedding or feature similarity to reduce repeated
processing.

**Synthetic pipeline**  
A benchmark pipeline assembled from local components to approximate intake,
classification, and triage costs without modeling any real target system.

**Triage**  
The prioritization stage that determines which processed inputs receive more attention
or further downstream handling.

---

## Working Distinctions

Use these distinctions consistently:

- "input" refers to an item processed by the benchmark harness
- "signal" refers to the higher-level abstract concept discussed in the whitepaper
- "motif" refers to a family or generator pattern, not a single input
- "countermeasure" refers to defender-facing controls
- "benchmark" refers to local evaluation only

---

## Terms To Avoid Without Definition

Avoid using these loosely in future drafts:

- noise
- whisper
- interference
- listener
- target
- saturation

Each of these is rhetorically strong but technically ambiguous unless tied to a
measurable benchmark concept.

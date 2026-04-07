# TODO

## Sprint 1 — Complete ✅
All items from the original TODO are done. See git log for details.

---

## Sprint 2 — Fix the Model Before Running More Experiments

These are blocking issues. The first research sweep exposed three gaps in the harness
that make further experiments misleading until they're fixed.

### Harness Fixes (blocking)
- [ ] **Fix cost model: dedup/cache hits must reduce simulated processing time.**
      Currently `avg_processing_cost_ms` is identical with dedup on and off — the
      early-exit fast path exists in routing logic but not in timing. Add `dedup_cost_ms`
      and `cluster_cost_ms` fields to profile JSON so hits draw from a cheaper cost
      distribution. This is required before any cost-asymmetry claim is quantifiable.
- [ ] **Fix prefilter: blocklists need tuning so they actually fire.**
      `accepted_input_rate` is 1.0 in every condition — the prefilter never rejects
      anything. Extend blocklists in each profile and add a `prefilter_max_tokens` cap
      so the prefilter stage contributes variance to results.
- [ ] **Fix sentinel score boost: remove the hardcoded +0.2 unconditional boost.**
      Every sentinel gets a guaranteed +0.2 classifier score bump making preservation
      always 1.0 regardless of load. Make the boost configurable per profile (or remove
      it) so false-negative drift can actually be measured.
- [ ] **Add queue saturation mode.**
      All queue depths are 0 because simulated processing (~2–4ms/item) is far faster
      than the 67ms inter-arrival gap at 15 inputs/s. Add `--saturate` flag that sets
      `--input-rate` high enough to guarantee queue backlog, or add a
      `--queue-depth-target N` parameter that back-calculates the required rate.

### Metrics
- [ ] **Add actual CPU ratio metric: R = mean_processing_cpu_ms / mean_generation_cpu_ms.**
      This is the primary asymmetry claim expressed as a measurable number. Currently
      generation cost is a placeholder (sum of char ordinals). Implement a realistic
      generation cost simulation (e.g. tokenization + template render time) so R is
      meaningful.
- [ ] **Add `--fast-exit-on-dedup` flag** that short-circuits all downstream stages on a
      dedup or cluster hit and records actual fast-path vs full-path timing separately.
      Gives a real measured cost ratio rather than a synthetic estimate.
- [ ] **Track and report `filter_rate`** — fraction of inputs rejected at each stage
      (prefilter, dedup-reject, cluster-reject). Currently only dedup/cluster *hits* are
      counted; rejections aren't reported.

---

## Sprint 3 — Second Research Sweep (after harness fixes)

Run these only after Sprint 2 fixes are in — results will be meaningless otherwise.

- [ ] Re-run all 27 Sweep 1 experiments with the fixed cost model and compare deltas.
- [ ] Stress-test sentinel preservation at scale: `--total-inputs 5000 --sentinel-interval 50`
      (100 sentinels/run) across all high-diversity conditions. Target: first non-1.0
      `sentinel_preservation_rate` result.
- [ ] Run queue saturation experiments: high input rate + high_diversity + clustering on/off.
      Key question: does queue depth correlate with sentinel false-negative rate?
- [ ] Run mass_surveillance and auto_targeting profiles across all workloads.
      Both profiles are untested — auto_targeting has a high `queue_priority_threshold`
      that should change priority routing behavior meaningfully.
- [ ] Run mixed workload vs. pure high_diversity (all defenses on) across all 5 profiles.
      Question: does interleaving workload types give the attacker additional clustering
      evasion beyond what high_diversity alone achieves?
- [ ] Measure cost asymmetry ratio R across profiles and workloads once generation
      cost model is realistic. This is the number the paper needs.

---

## Sprint 4 — Reservoir Generator

Gated on Sweep 2 results. Only worth building if high_diversity doesn't already saturate
the cost curve.

- [ ] Define ESN benchmark comparison protocol: what metrics would prove the reservoir
      generator adds value over `high_diversity`? Write the protocol before any code.
- [ ] Implement a minimal echo state network input generator as a new workload type
      (`reservoir`). Use a small fixed-size reservoir (N=100–500 units) with sparse
      connectivity.
- [ ] Run `reservoir` vs `high_diversity` head-to-head with all defenses on.
      If the cost delta is < 5%, the simpler approach wins and the ESN is not worth
      pursuing further.
- [ ] If reservoir wins: document the architecture, benchmark parameters, and decision
      criteria in `architecture/reservoir_layer.md`.

---

## Paper

- [ ] Replace all `[RESULT: ...]` placeholders in `docs/whitepaper_stub.md` with
      actual Sweep 1 numbers.
- [ ] Add honest negative results section to the paper body (the harness gaps, the
      uniformly-1.0 sentinel rate, the prefilter non-firing). The paper is stronger
      for acknowledging them.
- [ ] Add Sweep 2 results section once Sprint 3 is complete.
- [ ] Write the defender recommendations section: what the sweep results imply for
      operators deploying these pipelines.
- [ ] First external review pass — share `docs/whitepaper_stub.md` with a friendly
      reader outside the project before submission anywhere.

---

## Housekeeping
- [ ] Mark Sprint 1 Research and Paper items complete in this file (agents did the
      work but didn't tick the boxes).
- [ ] Add a `results/README.md` explaining the naming convention for result files.
- [ ] Set up a simple CI run (`python -m unittest`) on push so test regressions are
      caught automatically.

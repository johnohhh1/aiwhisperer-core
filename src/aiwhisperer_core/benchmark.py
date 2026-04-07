from __future__ import annotations

import csv
import json
import statistics
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from aiwhisperer_core.models import BenchmarkConfig, BenchmarkRun
from aiwhisperer_core.pipeline import SyntheticPipeline
from aiwhisperer_core.profiles import load_profile
from aiwhisperer_core.workloads import build_inputs


def run_benchmark(config: BenchmarkConfig) -> dict[str, Any]:
    profile = load_profile(config.profile)
    pipeline = SyntheticPipeline(
        profile=profile,
        dedup_enabled=config.dedup_enabled,
        clustering_enabled=config.clustering_enabled,
        cache_enabled=config.cache_enabled,
    )

    results = []
    generation_cpu_ms = []
    processing_cpu_ms = []
    # Task 3: count sentinels directly from GeneratedInput.is_sentinel during run loop
    sentinel_total_direct = 0

    for item in build_inputs(
        profile=profile,
        workload=config.workload,
        total_inputs=config.total_inputs,
        input_rate=config.input_rate,
        sentinel_interval=config.sentinel_interval,
        seed=config.seed,
    ):
        if item.is_sentinel:
            sentinel_total_direct += 1
        generation_cpu_ms.append(_measure_generation_cpu(item.text))
        start = time.perf_counter()
        result = pipeline.process(item)
        processing_cpu_ms.append((time.perf_counter() - start) * 1000.0)
        results.append(result)

    run = BenchmarkRun(
        config=config,
        profile=profile,
        results=results,
        generation_cpu_ms=generation_cpu_ms,
        processing_cpu_ms=processing_cpu_ms,
    )
    return summarize_run(run, sentinel_total_direct=sentinel_total_direct)


def write_summary(summary: dict[str, Any], output_path: str | None) -> None:
    if not output_path:
        print(json.dumps(summary, indent=2))
        return
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2))


def summarize_run(run: BenchmarkRun, *, sentinel_total_direct: int | None = None) -> dict[str, Any]:
    accepted = [result for result in run.results if result.accepted]

    accepted_count = len(accepted)
    dedup_hits = sum(result.dedup_hit for result in run.results)
    cluster_hits = sum(result.cluster_hit for result in run.results)
    queue_depths = [result.queue_depth_at_arrival for result in run.results]
    scores = [result.classifier_score for result in accepted]

    # Task 3: exact sentinel counts — prefer the direct count from the run loop
    # when available; fall back to reading is_sentinel from PipelineResult.
    sentinel_results = [result for result in run.results if result.is_sentinel]
    sentinel_total = sentinel_total_direct if sentinel_total_direct is not None else len(sentinel_results)
    sentinel_kept = sum(1 for result in sentinel_results if result.sentinel_preserved)

    # Task 1: separate simulated processing cost and queue delay
    processing_costs = [result.processing_ms for result in run.results]
    queue_delays = [result.queue_delay_ms for result in run.results]

    # Task 2: p50/p95/max stats blocks for queue depth and classifier score
    queue_depth_stats = {
        "p50": _percentile(queue_depths, 0.50),
        "p95": _percentile(queue_depths, 0.95),
        "max": max(queue_depths, default=0),
    }
    classifier_score_stats = {
        "p50": round(_percentile(scores, 0.50), 4),
        "p95": round(_percentile(scores, 0.95), 4),
        "max": round(max(scores, default=0.0), 4),
    }

    # Task 4: sentinel false-negative rate — fraction of sentinel inputs that were
    # either not accepted or not assigned queue_priority == "high".
    sentinel_false_negatives = sum(
        1 for r in sentinel_results
        if not r.accepted or r.queue_priority in ("normal", "dropped")
    )
    sentinel_false_negative_rate = round(
        sentinel_false_negatives / max(sentinel_total, 1), 4
    )

    # Task 4: false-negative drift by load tercile
    sentinel_fn_by_load = _sentinel_fn_by_load(run.results)

    # Task 5: per-stage synthetic timing breakdown averages
    stage_timing_ms = {
        "intake_ms": round(_safe_mean([r.intake_ms for r in run.results]), 4),
        "prefilter_ms": round(_safe_mean([r.prefilter_ms for r in run.results]), 4),
        "feature_ms": round(_safe_mean([r.feature_ms for r in run.results]), 4),
        "classifier_ms": round(_safe_mean([r.classifier_ms for r in run.results]), 4),
    }

    return {
        "config": asdict(run.config),
        "profile": {
            "slug": run.profile.slug,
            "name": run.profile.name,
            "false_negative_cost": run.profile.false_negative_cost,
            "notes": run.profile.notes,
        },
        "metrics": {
            "total_inputs": len(run.results),
            "accepted_inputs": accepted_count,
            "accepted_input_rate": round(accepted_count / max(len(run.results), 1), 4),
            "dedup_hit_rate": round(dedup_hits / max(len(run.results), 1), 4),
            "cluster_hit_rate": round(cluster_hits / max(len(run.results), 1), 4),
            "avg_generation_cpu_ms": round(_safe_mean(run.generation_cpu_ms), 6),
            "avg_processing_cpu_ms": round(_safe_mean(run.processing_cpu_ms), 6),
            # Task 1: separate simulated processing cost vs simulated queue wait
            "avg_simulated_processing_ms": round(_safe_mean(processing_costs), 4),
            "avg_simulated_queue_delay_ms": round(_safe_mean(queue_delays), 4),
            # Keep legacy names for backward compat
            "avg_processing_cost_ms": round(_safe_mean(processing_costs), 4),
            "p95_processing_cost_ms": round(_percentile(processing_costs, 0.95), 4),
            "avg_queue_delay_ms": round(_safe_mean(queue_delays), 4),
            "p95_queue_delay_ms": round(_percentile(queue_delays, 0.95), 4),
            # Task 2: percentile stats for queue depth and classifier score
            "avg_queue_depth": round(_safe_mean(queue_depths), 4),
            "queue_depth_stats": queue_depth_stats,
            "avg_classifier_score": round(_safe_mean(scores), 4),
            "classifier_score_stats": classifier_score_stats,
            # Task 3: exact sentinel counts
            "sentinel_total": sentinel_total,
            "sentinel_preserved": sentinel_kept,
            "sentinel_preservation_rate": round(sentinel_kept / max(sentinel_total, 1), 4),
            # Task 4: flat false-negative rate for sentinels
            "sentinel_false_negative_rate": sentinel_false_negative_rate,
        },
        "priority_counts": {
            "high": sum(result.queue_priority == "high" for result in run.results),
            "normal": sum(result.queue_priority == "normal" for result in run.results),
            "dropped": sum(result.queue_priority == "dropped" for result in run.results),
        },
        "filtered_reasons": _count_values(
            [result.filtered_reason for result in run.results if result.filtered_reason]
        ),
        # Task 4: false-negative drift by load tercile
        "sentinel_fn_by_load": sentinel_fn_by_load,
        # Task 5: per-stage timing breakdown averages
        "stage_timing_ms": stage_timing_ms,
    }


def _sentinel_fn_by_load(results: list) -> dict[str, Any]:
    """Divide results into 3 load terciles by queue_depth_at_arrival.

    For each tercile report sentinel count and preservation rate to expose
    whether high queue load degrades sentinel handling (false-negative drift).
    """
    depths = [r.queue_depth_at_arrival for r in results]
    low_thresh = _percentile(depths, 1 / 3)
    high_thresh = _percentile(depths, 2 / 3)

    buckets: dict[str, list] = {"low": [], "mid": [], "high": []}
    for result in results:
        d = result.queue_depth_at_arrival
        if d <= low_thresh:
            buckets["low"].append(result)
        elif d <= high_thresh:
            buckets["mid"].append(result)
        else:
            buckets["high"].append(result)

    out: dict[str, Any] = {}
    for label, bucket in buckets.items():
        sentinels = [r for r in bucket if r.is_sentinel]
        sentinel_count = len(sentinels)
        preserved = sum(1 for r in sentinels if r.sentinel_preserved)
        out[label] = {
            "total_inputs": len(bucket),
            "sentinel_count": sentinel_count,
            "sentinel_preserved": preserved,
            "preservation_rate": round(preserved / max(sentinel_count, 1), 4),
        }
    return out


def _measure_generation_cpu(text: str) -> float:
    start = time.perf_counter()
    _ = sum(ord(char) for char in text)
    return (time.perf_counter() - start) * 1000.0


def _safe_mean(values: list[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def _percentile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * quantile))))
    return ordered[index]


def _count_values(values: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts



# ---------------------------------------------------------------------------
# Feature: Repeat-run support with aggregated summary statistics
# ---------------------------------------------------------------------------

def run_benchmark_repeated(config: BenchmarkConfig, repeat: int = 1) -> dict[str, Any]:
    """Run the benchmark *repeat* times with incrementing seeds.

    When repeat == 1 the output is identical to run_benchmark().
    When repeat > 1 an additional ``"aggregated"`` key is added with
    mean ± stdev for every numeric metric across all runs.
    """
    if repeat < 1:
        raise ValueError(f"repeat must be >= 1, got {repeat}")
    summaries: list[dict[str, Any]] = []
    for i in range(repeat):
        seeded = BenchmarkConfig(
            profile=config.profile,
            workload=config.workload,
            total_inputs=config.total_inputs,
            input_rate=config.input_rate,
            sentinel_interval=config.sentinel_interval,
            dedup_enabled=config.dedup_enabled,
            clustering_enabled=config.clustering_enabled,
            cache_enabled=config.cache_enabled,
            seed=config.seed + i,
        )
        summaries.append(run_benchmark(seeded))
    if repeat == 1:
        return summaries[0]
    base = dict(summaries[-1])
    base["aggregated"] = _aggregate_summaries(summaries)
    return base


def _aggregate_summaries(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute mean ± stdev for each numeric metric key."""
    numeric_keys = [
        "total_inputs",
        "accepted_inputs",
        "accepted_input_rate",
        "dedup_hit_rate",
        "cluster_hit_rate",
        "avg_generation_cpu_ms",
        "avg_processing_cpu_ms",
        "avg_processing_cost_ms",
        "p95_processing_cost_ms",
        "avg_queue_delay_ms",
        "p95_queue_delay_ms",
        "avg_queue_depth",
        "avg_classifier_score",
        "sentinel_total",
        "sentinel_preserved",
        "sentinel_preservation_rate",
    ]
    agg: dict[str, Any] = {"n_runs": len(summaries)}
    for key in numeric_keys:
        values = [s["metrics"][key] for s in summaries if key in s.get("metrics", {})]
        if not values:
            continue
        mean = statistics.fmean(values)
        stdev = statistics.pstdev(values) if len(values) > 1 else 0.0
        agg[key] = {"mean": round(mean, 6), "stdev": round(stdev, 6)}
    return agg


# ---------------------------------------------------------------------------
# Feature: CSV output alongside JSON summaries
# ---------------------------------------------------------------------------

def write_csv(results: "list[PipelineResult]", output_path: str) -> None:
    """Write one CSV row per PipelineResult to *output_path*."""
    fieldnames = [
        "input_id",
        "accepted",
        "dedup_hit",
        "cluster_hit",
        "classifier_score",
        "queue_priority",
        "processing_ms",
        "queue_depth_at_arrival",
        "sentinel_preserved",
        "filtered_reason",
    ]
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "input_id": r.input_id,
                "accepted": r.accepted,
                "dedup_hit": r.dedup_hit,
                "cluster_hit": r.cluster_hit,
                "classifier_score": r.classifier_score,
                "queue_priority": r.queue_priority,
                "processing_ms": r.processing_ms,
                "queue_depth_at_arrival": r.queue_depth_at_arrival,
                "sentinel_preserved": r.sentinel_preserved,
                "filtered_reason": r.filtered_reason if r.filtered_reason else "",
            })


def _run_benchmark_with_results(config: BenchmarkConfig) -> "tuple[dict[str, Any], list[PipelineResult]]":
    """Like run_benchmark() but also returns the raw PipelineResult list."""
    profile = load_profile(config.profile)
    pipeline = SyntheticPipeline(
        profile=profile,
        dedup_enabled=config.dedup_enabled,
        clustering_enabled=config.clustering_enabled,
        cache_enabled=config.cache_enabled,
    )
    results: list = []
    generation_cpu_ms: list[float] = []
    processing_cpu_ms: list[float] = []
    sentinel_total_direct = 0
    for item in build_inputs(
        profile=profile,
        workload=config.workload,
        total_inputs=config.total_inputs,
        input_rate=config.input_rate,
        sentinel_interval=config.sentinel_interval,
        seed=config.seed,
    ):
        if item.is_sentinel:
            sentinel_total_direct += 1
        generation_cpu_ms.append(_measure_generation_cpu(item.text))
        start = time.perf_counter()
        result = pipeline.process(item)
        processing_cpu_ms.append((time.perf_counter() - start) * 1000.0)
        results.append(result)
    run = BenchmarkRun(
        config=config,
        profile=profile,
        results=results,
        generation_cpu_ms=generation_cpu_ms,
        processing_cpu_ms=processing_cpu_ms,
    )
    return summarize_run(run, sentinel_total_direct=sentinel_total_direct), results


# ---------------------------------------------------------------------------
# Feature: Experiment manifest format for batch runs
# ---------------------------------------------------------------------------

def run_manifest(manifest_path: str) -> dict[str, Any]:
    """Load a JSON manifest and run all listed benchmark configs.

    Returns a dict keyed by the ``"label"`` field of each entry.

    Manifest format — a JSON array of objects::

        [
          {
            "label": "soc_dedup_off",
            "profile": "soc_triage",
            "workload": "templated_variation",
            "disable_dedup": true,
            "total_inputs": 200,
            "input_rate": 15.0,
            "sentinel_interval": 25,
            "seed": 7,
            "repeat": 1
          }
        ]

    All fields except ``"profile"`` and ``"workload"`` are optional and
    fall back to the same defaults as the CLI.
    """
    raw = json.loads(Path(manifest_path).read_text())
    manifest_results: dict[str, Any] = {}
    for entry in raw:
        label = entry.get("label", f"run_{len(manifest_results)}")
        config = BenchmarkConfig(
            profile=entry["profile"],
            workload=entry["workload"],
            total_inputs=entry.get("total_inputs", 200),
            input_rate=entry.get("input_rate", 15.0),
            sentinel_interval=entry.get("sentinel_interval", 25),
            dedup_enabled=not entry.get("disable_dedup", False),
            clustering_enabled=not entry.get("disable_clustering", False),
            cache_enabled=not entry.get("disable_cache", False),
            seed=entry.get("seed", 7),
        )
        repeat = entry.get("repeat", 1)
        manifest_results[label] = run_benchmark_repeated(config, repeat=repeat)
    return manifest_results

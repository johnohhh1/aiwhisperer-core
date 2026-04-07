from __future__ import annotations

import argparse
import json
import sys

from aiwhisperer_core.benchmark import (
    run_benchmark_repeated,
    run_manifest,
    write_csv,
    write_summary,
    _run_benchmark_with_results,
)
from aiwhisperer_core.models import BenchmarkConfig
from aiwhisperer_core.profiles import list_profiles


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the AI Whisperer synthetic benchmark.")
    # --manifest is a standalone mode; other flags are for single-run mode
    parser.add_argument(
        "--manifest",
        help="Path to a JSON manifest file for batch runs. When set, --profile and --workload are ignored.",
    )
    parser.add_argument("--profile", choices=list_profiles())
    parser.add_argument(
        "--workload",
        choices=[
            "benign_background",
            "exact_repetition",
            "templated_variation",
            "high_diversity",
            "mixed",
        ],
        help=(
            "Workload type to generate. 'mixed' cycles through all four base workload types "
            "in shuffled order, combining background, repetition, templated variation, and "
            "high-diversity inputs in a single run."
        ),
    )
    parser.add_argument("--total-inputs", type=int, default=200)
    parser.add_argument("--input-rate", type=float, default=15.0)
    parser.add_argument("--sentinel-interval", type=int, default=25)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--disable-dedup", action="store_true")
    parser.add_argument("--disable-clustering", action="store_true")
    parser.add_argument("--disable-cache", action="store_true")
    parser.add_argument("--output", help="Optional JSON output path.")
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        metavar="N",
        help=(
            "Run the benchmark N times with incrementing seeds and aggregate results. "
            "When N > 1 an 'aggregated' key with mean ± stdev per metric is added to the summary."
        ),
    )
    parser.add_argument(
        "--output-csv",
        metavar="PATH",
        help="Write per-input results as CSV to this path.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    # --- Manifest mode ---
    if args.manifest:
        results = run_manifest(args.manifest)
        if args.output:
            from pathlib import Path
            path = Path(args.output)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(results, indent=2))
        else:
            print(json.dumps(results, indent=2))
        return

    # --- Single-run mode ---
    if not args.profile or not args.workload:
        print("error: --profile and --workload are required unless --manifest is used.", file=sys.stderr)
        sys.exit(1)

    config = BenchmarkConfig(
        profile=args.profile,
        workload=args.workload,
        total_inputs=args.total_inputs,
        input_rate=args.input_rate,
        sentinel_interval=args.sentinel_interval,
        dedup_enabled=not args.disable_dedup,
        clustering_enabled=not args.disable_clustering,
        cache_enabled=not args.disable_cache,
        seed=args.seed,
    )

    if args.output_csv:
        # Need the raw results for CSV; run the last seed directly
        if args.repeat > 1:
            from aiwhisperer_core.benchmark import _aggregate_summaries
            summaries = []
            last_results = []
            for i in range(args.repeat):
                from aiwhisperer_core.models import BenchmarkConfig as BC
                seeded = BC(
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
                s, r = _run_benchmark_with_results(seeded)
                summaries.append(s)
                last_results = r
            summary = dict(summaries[-1])
            summary["aggregated"] = _aggregate_summaries(summaries)
        else:
            summary, last_results = _run_benchmark_with_results(config)
        write_csv(last_results, args.output_csv)
    else:
        summary = run_benchmark_repeated(config, repeat=args.repeat)

    write_summary(summary, args.output)


if __name__ == "__main__":
    main()

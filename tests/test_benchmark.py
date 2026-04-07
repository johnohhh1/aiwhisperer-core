from __future__ import annotations

import unittest

from aiwhisperer_core.benchmark import run_benchmark
from aiwhisperer_core.models import BenchmarkConfig
from aiwhisperer_core.profiles import list_profiles, load_profile


class BenchmarkSmokeTests(unittest.TestCase):
    def test_profiles_are_available(self) -> None:
        profiles = list_profiles()
        self.assertIn("soc_triage", profiles)
        self.assertIn("trust_safety", profiles)
        self.assertIn("fraud_abuse", profiles)
        self.assertIn("mass_surveillance", profiles)
        self.assertIn("auto_targeting", profiles)

    def test_profile_loader_returns_expected_slug(self) -> None:
        profile = load_profile("soc_triage")
        self.assertEqual(profile.slug, "soc_triage")
        self.assertGreater(profile.queue_priority_threshold, 0.0)

    def test_benchmark_runs_and_reports_metrics(self) -> None:
        summary = run_benchmark(
            BenchmarkConfig(
                profile="soc_triage",
                workload="templated_variation",
                total_inputs=30,
                input_rate=12.0,
                sentinel_interval=10,
                dedup_enabled=True,
                clustering_enabled=True,
                cache_enabled=True,
                seed=3,
            )
        )
        metrics = summary["metrics"]
        self.assertEqual(metrics["total_inputs"], 30)
        self.assertIn("high", summary["priority_counts"])

        # Task 1: separate simulated processing cost and queue delay
        self.assertIn("avg_simulated_processing_ms", metrics)
        self.assertIn("avg_simulated_queue_delay_ms", metrics)
        # Legacy names still present for backward compat
        self.assertIn("avg_processing_cost_ms", metrics)
        self.assertIn("avg_queue_delay_ms", metrics)
        self.assertIn("p95_processing_cost_ms", metrics)
        self.assertIn("p95_queue_delay_ms", metrics)
        # Values must be non-negative
        self.assertGreaterEqual(metrics["avg_simulated_processing_ms"], 0.0)
        self.assertGreaterEqual(metrics["avg_simulated_queue_delay_ms"], 0.0)

        # Task 2: p50/p95/max stats blocks
        self.assertIn("queue_depth_stats", metrics)
        self.assertIn("p50", metrics["queue_depth_stats"])
        self.assertIn("p95", metrics["queue_depth_stats"])
        self.assertIn("max", metrics["queue_depth_stats"])
        self.assertIn("classifier_score_stats", metrics)
        self.assertIn("p50", metrics["classifier_score_stats"])

        # Task 3: exact sentinel counts present
        self.assertIn("sentinel_total", metrics)
        self.assertGreater(metrics["sentinel_total"], 0)

        # Task 4: flat false-negative rate metric
        self.assertIn("sentinel_false_negative_rate", metrics)
        fnr = metrics["sentinel_false_negative_rate"]
        self.assertGreaterEqual(fnr, 0.0)
        self.assertLessEqual(fnr, 1.0)

        # Task 4: false-negative drift by load terciles
        self.assertIn("sentinel_fn_by_load", summary)
        fn_by_load = summary["sentinel_fn_by_load"]
        for label in ("low", "mid", "high"):
            self.assertIn(label, fn_by_load)
            self.assertIn("sentinel_count", fn_by_load[label])
            self.assertIn("preservation_rate", fn_by_load[label])

        # Task 5: per-stage timing breakdown
        self.assertIn("stage_timing_ms", summary)
        for stage in ("intake_ms", "prefilter_ms", "feature_ms", "classifier_ms"):
            self.assertIn(stage, summary["stage_timing_ms"])
            self.assertGreater(summary["stage_timing_ms"][stage], 0.0)

        # avg_queue_depth still present for backward compat
        self.assertIn("avg_queue_depth", metrics)


if __name__ == "__main__":
    unittest.main()


class MetricsTasksTests(unittest.TestCase):
    """Dedicated tests for the five Metrics TODO items."""

    _CFG = dict(
        profile="soc_triage",
        workload="templated_variation",
        total_inputs=40,
        input_rate=12.0,
        sentinel_interval=8,
        dedup_enabled=True,
        clustering_enabled=True,
        cache_enabled=True,
        seed=7,
    )

    def _run(self):
        return run_benchmark(BenchmarkConfig(**self._CFG))

    # ------------------------------------------------------------------
    # Task 1: avg_simulated_processing_ms and avg_simulated_queue_delay_ms
    # ------------------------------------------------------------------
    def test_task1_simulated_names_present(self):
        summary = self._run()
        m = summary["metrics"]
        self.assertIn("avg_simulated_processing_ms", m)
        self.assertIn("avg_simulated_queue_delay_ms", m)

    def test_task1_processing_ms_positive(self):
        summary = self._run()
        self.assertGreater(summary["metrics"]["avg_simulated_processing_ms"], 0.0)

    def test_task1_queue_delay_non_negative(self):
        summary = self._run()
        self.assertGreaterEqual(summary["metrics"]["avg_simulated_queue_delay_ms"], 0.0)

    def test_task1_simulated_names_match_legacy(self):
        """avg_simulated_processing_ms must equal avg_processing_cost_ms."""
        m = self._run()["metrics"]
        self.assertEqual(m["avg_simulated_processing_ms"], m["avg_processing_cost_ms"])
        self.assertEqual(m["avg_simulated_queue_delay_ms"], m["avg_queue_delay_ms"])

    # ------------------------------------------------------------------
    # Task 2: p50/p95/max for queue_depth and classifier_score
    # ------------------------------------------------------------------
    def test_task2_queue_depth_stats(self):
        m = self._run()["metrics"]
        for key in ("p50", "p95", "max"):
            self.assertIn(key, m["queue_depth_stats"])

    def test_task2_classifier_score_stats(self):
        m = self._run()["metrics"]
        for key in ("p50", "p95", "max"):
            self.assertIn(key, m["classifier_score_stats"])

    def test_task2_avg_queue_depth_present(self):
        self.assertIn("avg_queue_depth", self._run()["metrics"])

    # ------------------------------------------------------------------
    # Task 3: sentinel_total is a clean direct count
    # ------------------------------------------------------------------
    def test_task3_sentinel_total_present_and_positive(self):
        m = self._run()["metrics"]
        self.assertIn("sentinel_total", m)
        self.assertGreater(m["sentinel_total"], 0)

    def test_task3_sentinel_total_matches_interval(self):
        """With sentinel_interval=8 and 40 inputs we expect ~5 sentinels."""
        m = self._run()["metrics"]
        # total_inputs // sentinel_interval = 5
        self.assertEqual(m["sentinel_total"], 40 // 8)

    # ------------------------------------------------------------------
    # Task 4: sentinel_false_negative_rate
    # ------------------------------------------------------------------
    def test_task4_fnr_present(self):
        self.assertIn("sentinel_false_negative_rate", self._run()["metrics"])

    def test_task4_fnr_in_range(self):
        fnr = self._run()["metrics"]["sentinel_false_negative_rate"]
        self.assertGreaterEqual(fnr, 0.0)
        self.assertLessEqual(fnr, 1.0)

    def test_task4_fn_by_load_terciles(self):
        fn_by_load = self._run()["sentinel_fn_by_load"]
        for label in ("low", "mid", "high"):
            self.assertIn(label, fn_by_load)
            entry = fn_by_load[label]
            self.assertIn("sentinel_count", entry)
            self.assertIn("preservation_rate", entry)

    # ------------------------------------------------------------------
    # Task 5: per-stage timing
    # ------------------------------------------------------------------
    def test_task5_stage_timing_present(self):
        stages = self._run()["stage_timing_ms"]
        for stage in ("intake_ms", "prefilter_ms", "feature_ms", "classifier_ms"):
            self.assertIn(stage, stages)

    def test_task5_stage_timing_positive(self):
        stages = self._run()["stage_timing_ms"]
        for stage in ("intake_ms", "prefilter_ms", "feature_ms", "classifier_ms"):
            self.assertGreater(stages[stage], 0.0)


class HarnessFeaturesTests(unittest.TestCase):
    """Smoke tests for the five Harness TODO items."""

    _BASE_CONFIG = dict(
        profile="soc_triage",
        total_inputs=20,
        input_rate=12.0,
        sentinel_interval=10,
        dedup_enabled=True,
        clustering_enabled=True,
        cache_enabled=True,
        seed=42,
    )

    # ------------------------------------------------------------------
    # 1. Profile-specific workload fixtures from JSON
    # ------------------------------------------------------------------
    def test_profile_has_background_templates_from_json(self) -> None:
        profile = load_profile("soc_triage")
        self.assertGreater(len(profile.background_templates), 0)
        self.assertIsInstance(profile.background_templates[0], str)

    def test_profile_has_sentinel_inputs_from_json(self) -> None:
        for slug in ("soc_triage", "trust_safety", "fraud_abuse"):
            profile = load_profile(slug)
            self.assertGreater(len(profile.sentinel_inputs), 0,
                                msg=f"{slug} missing sentinel_inputs")

    def test_workload_uses_profile_templates(self) -> None:
        from aiwhisperer_core.workloads import build_inputs
        profile = load_profile("soc_triage")
        inputs = list(build_inputs(
            profile=profile,
            workload="benign_background",
            total_inputs=5,
            input_rate=10.0,
            sentinel_interval=0,
            seed=1,
        ))
        self.assertEqual(len(inputs), 5)

    # ------------------------------------------------------------------
    # 2. Mixed workload mode
    # ------------------------------------------------------------------
    def test_mixed_workload_runs(self) -> None:
        from aiwhisperer_core.benchmark import run_benchmark
        summary = run_benchmark(BenchmarkConfig(
            workload="mixed",
            **self._BASE_CONFIG,
        ))
        self.assertEqual(summary["metrics"]["total_inputs"], 20)

    def test_mixed_workload_uses_varied_types(self) -> None:
        from aiwhisperer_core.workloads import build_inputs
        profile = load_profile("soc_triage")
        inputs = list(build_inputs(
            profile=profile,
            workload="mixed",
            total_inputs=40,
            input_rate=10.0,
            sentinel_interval=0,
            seed=7,
        ))
        workload_types = {inp.workload for inp in inputs}
        # mixed should produce at least 2 different underlying workload types
        self.assertGreater(len(workload_types), 1)

    # ------------------------------------------------------------------
    # 3. Repeat-run support with aggregated statistics
    # ------------------------------------------------------------------
    def test_repeat_1_no_aggregated_key(self) -> None:
        from aiwhisperer_core.benchmark import run_benchmark_repeated
        summary = run_benchmark_repeated(
            BenchmarkConfig(workload="benign_background", **self._BASE_CONFIG),
            repeat=1,
        )
        self.assertNotIn("aggregated", summary)

    def test_repeat_3_adds_aggregated_key(self) -> None:
        from aiwhisperer_core.benchmark import run_benchmark_repeated
        summary = run_benchmark_repeated(
            BenchmarkConfig(workload="benign_background", **self._BASE_CONFIG),
            repeat=3,
        )
        self.assertIn("aggregated", summary)
        agg = summary["aggregated"]
        self.assertEqual(agg["n_runs"], 3)
        self.assertIn("accepted_input_rate", agg)
        self.assertIn("mean", agg["accepted_input_rate"])
        self.assertIn("stdev", agg["accepted_input_rate"])

    # ------------------------------------------------------------------
    # 4. CSV output
    # ------------------------------------------------------------------
    def test_csv_output_written(self) -> None:
        import csv
        import os
        import tempfile
        from aiwhisperer_core.benchmark import write_csv, _run_benchmark_with_results
        config = BenchmarkConfig(workload="templated_variation", **self._BASE_CONFIG)
        _, results = _run_benchmark_with_results(config)
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            write_csv(results, tmp_path)
            with open(tmp_path, newline="") as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual(len(rows), 20)
            expected_fields = {
                "input_id", "accepted", "dedup_hit", "cluster_hit",
                "classifier_score", "queue_priority", "processing_ms",
                "queue_depth_at_arrival", "sentinel_preserved", "filtered_reason",
            }
            self.assertEqual(set(rows[0].keys()), expected_fields)
        finally:
            os.unlink(tmp_path)

    # ------------------------------------------------------------------
    # 5. Experiment manifest
    # ------------------------------------------------------------------
    def test_manifest_runs_all_entries(self) -> None:
        import json
        import os
        import tempfile
        from aiwhisperer_core.benchmark import run_manifest
        manifest = [
            {
                "label": "soc_dedup_off",
                "profile": "soc_triage",
                "workload": "templated_variation",
                "total_inputs": 15,
                "disable_dedup": True,
            },
            {
                "label": "soc_baseline",
                "profile": "soc_triage",
                "workload": "templated_variation",
                "total_inputs": 15,
            },
        ]
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as tmp:
            json.dump(manifest, tmp)
            tmp_path = tmp.name
        try:
            results = run_manifest(tmp_path)
            self.assertIn("soc_dedup_off", results)
            self.assertIn("soc_baseline", results)
            self.assertEqual(results["soc_baseline"]["metrics"]["total_inputs"], 15)
        finally:
            os.unlink(tmp_path)

    def test_manifest_repeat_adds_aggregated(self) -> None:
        import json
        import os
        import tempfile
        from aiwhisperer_core.benchmark import run_manifest
        manifest = [
            {
                "label": "repeat_run",
                "profile": "fraud_abuse",
                "workload": "benign_background",
                "total_inputs": 10,
                "repeat": 3,
            },
        ]
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as tmp:
            json.dump(manifest, tmp)
            tmp_path = tmp.name
        try:
            results = run_manifest(tmp_path)
            self.assertIn("aggregated", results["repeat_run"])
            self.assertEqual(results["repeat_run"]["aggregated"]["n_runs"], 3)
        finally:
            os.unlink(tmp_path)

    # ------------------------------------------------------------------
    # 1 (extended). Fixture files and variation_snippets
    # ------------------------------------------------------------------
    def test_fixture_files_exist_for_all_profiles(self) -> None:
        """config/fixtures/<slug>.json must exist for every profile."""
        from pathlib import Path
        fixtures_dir = Path(__file__).resolve().parents[1] / "config" / "fixtures"
        for slug in ("soc_triage", "trust_safety", "fraud_abuse",
                     "mass_surveillance", "auto_targeting"):
            self.assertTrue(
                (fixtures_dir / f"{slug}.json").exists(),
                msg=f"Missing fixture file for {slug}",
            )

    def test_fixture_file_has_required_keys(self) -> None:
        """Each fixture file must contain all three template/snippet keys."""
        import json
        from pathlib import Path
        fixtures_dir = Path(__file__).resolve().parents[1] / "config" / "fixtures"
        for slug in ("soc_triage", "trust_safety", "fraud_abuse"):
            data = json.loads((fixtures_dir / f"{slug}.json").read_text())
            for key in ("background_templates", "variation_snippets", "sentinel_inputs"):
                self.assertIn(key, data, msg=f"{slug}.json missing '{key}'")
                self.assertGreater(len(data[key]), 0,
                                   msg=f"{slug}.json '{key}' must be non-empty")

    def test_profile_variation_snippets_loaded_from_fixture(self) -> None:
        """Profile.variation_snippets must be populated from the fixture file."""
        for slug in ("soc_triage", "trust_safety", "fraud_abuse"):
            profile = load_profile(slug)
            self.assertGreater(
                len(profile.variation_snippets), 0,
                msg=f"{slug} missing variation_snippets",
            )
            self.assertIsInstance(profile.variation_snippets[0], str)

    def test_variation_snippets_used_in_templated_variation(self) -> None:
        """Templated variation outputs must end with a snippet from the profile fixture."""
        from aiwhisperer_core.workloads import build_inputs
        profile = load_profile("soc_triage")
        inputs = list(build_inputs(
            profile=profile,
            workload="templated_variation",
            total_inputs=10,
            input_rate=10.0,
            sentinel_interval=0,
            seed=1,
        ))
        snippets = set(profile.variation_snippets)
        found = any(
            any(snippet in inp.text for snippet in snippets)
            for inp in inputs
        )
        self.assertTrue(found, "No profile variation_snippet found in templated_variation outputs")

    def test_all_profiles_load_successfully(self) -> None:
        """All five profiles must load without error after fixture loading is wired up."""
        for slug in ("soc_triage", "trust_safety", "fraud_abuse",
                     "mass_surveillance", "auto_targeting"):
            profile = load_profile(slug)
            self.assertEqual(profile.slug, slug)
            self.assertGreater(len(profile.background_templates), 0,
                               msg=f"{slug} missing background_templates")
            self.assertGreater(len(profile.sentinel_inputs), 0,
                               msg=f"{slug} missing sentinel_inputs")
            self.assertGreater(len(profile.variation_snippets), 0,
                               msg=f"{slug} missing variation_snippets")

    # ------------------------------------------------------------------
    # 5 (extended). Example manifest file is valid
    # ------------------------------------------------------------------
    def test_example_manifest_is_valid_json(self) -> None:
        """config/example_manifest.json must exist and be a non-empty JSON list."""
        import json
        from pathlib import Path
        manifest_path = Path(__file__).resolve().parents[1] / "config" / "example_manifest.json"
        self.assertTrue(manifest_path.exists(), "config/example_manifest.json not found")
        data = json.loads(manifest_path.read_text())
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        for entry in data:
            self.assertIn("label", entry)
            self.assertIn("profile", entry)
            self.assertIn("workload", entry)

    def test_example_manifest_runs_without_error(self) -> None:
        """The example manifest file must run successfully end-to-end."""
        from pathlib import Path
        from aiwhisperer_core.benchmark import run_manifest
        manifest_path = Path(__file__).resolve().parents[1] / "config" / "example_manifest.json"
        results = run_manifest(str(manifest_path))
        self.assertIsInstance(results, dict)
        self.assertGreater(len(results), 0)
        for label, summary in results.items():
            self.assertIn("metrics", summary, msg=f"Entry '{label}' missing 'metrics'")

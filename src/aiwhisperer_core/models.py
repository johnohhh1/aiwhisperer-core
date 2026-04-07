from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Profile:
    slug: str
    name: str
    classifier_bias: float
    classifier_scale: float
    prefilter_min_tokens: int
    prefilter_blocklist: tuple[str, ...]
    sentinel_keywords: tuple[str, ...]
    suspicious_keywords: tuple[str, ...]
    queue_priority_threshold: float
    false_negative_cost: float = 0.5
    notes: str = ""
    background_templates: tuple[str, ...] = field(default_factory=tuple)
    sentinel_inputs: tuple[str, ...] = field(default_factory=tuple)
    variation_snippets: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class GeneratedInput:
    input_id: str
    profile: str
    workload: str
    text: str
    arrival_ms: float
    is_sentinel: bool
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PipelineResult:
    input_id: str
    accepted: bool
    dedup_hit: bool
    cluster_hit: bool
    classifier_score: float
    queue_priority: str
    processing_ms: float
    queue_delay_ms: float
    queue_depth_at_arrival: int
    sentinel_preserved: bool
    is_sentinel: bool
    intake_ms: float
    prefilter_ms: float
    feature_ms: float
    classifier_ms: float
    filtered_reason: str | None = None


@dataclass(frozen=True)
class BenchmarkConfig:
    profile: str
    workload: str
    total_inputs: int
    input_rate: float
    sentinel_interval: int
    dedup_enabled: bool
    clustering_enabled: bool
    cache_enabled: bool
    seed: int


@dataclass(frozen=True)
class BenchmarkRun:
    config: BenchmarkConfig
    profile: Profile
    results: list[PipelineResult]
    generation_cpu_ms: list[float]
    processing_cpu_ms: list[float]


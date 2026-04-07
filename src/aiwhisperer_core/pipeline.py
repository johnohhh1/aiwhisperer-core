from __future__ import annotations

import hashlib
import math
import re
from collections import deque

from aiwhisperer_core.models import GeneratedInput, PipelineResult, Profile

TOKEN_RE = re.compile(r"[a-z0-9]+")


class SyntheticPipeline:
    def __init__(
        self,
        *,
        profile: Profile,
        dedup_enabled: bool,
        clustering_enabled: bool,
        cache_enabled: bool,
    ) -> None:
        self.profile = profile
        self.dedup_enabled = dedup_enabled
        self.clustering_enabled = clustering_enabled
        self.cache_enabled = cache_enabled
        self.exact_fingerprints: set[str] = set()
        self.cluster_fingerprints: deque[set[str]] = deque(maxlen=128)
        self.cache: dict[str, float] = {}
        self.processing_end_ms = 0.0

    def process(self, item: GeneratedInput) -> PipelineResult:
        tokens = tokenize(item.text)
        queue_depth = self._queue_depth(item.arrival_ms)
        filtered_reason = self._prefilter_reason(tokens)
        accepted = filtered_reason is None

        fingerprint = stable_fingerprint(item.text)
        dedup_hit = self.dedup_enabled and fingerprint in self.exact_fingerprints
        if accepted:
            self.exact_fingerprints.add(fingerprint)

        cluster_hit = False
        token_set = set(tokens)
        if accepted and self.clustering_enabled:
            cluster_hit = any(jaccard(token_set, existing) >= 0.82 for existing in self.cluster_fingerprints)
            self.cluster_fingerprints.append(token_set)

        classifier_score = 0.0
        if accepted:
            classifier_score = self._classify(tokens, item.is_sentinel, cluster_hit)

        queue_priority = "dropped"
        if accepted:
            queue_priority = "high" if classifier_score >= self.profile.queue_priority_threshold else "normal"

        stage_costs = self._processing_cost(tokens, dedup_hit, cluster_hit, fingerprint)
        processing_ms = stage_costs["total_ms"]

        queue_delay_ms = 0.0
        if accepted:
            start_ms = max(item.arrival_ms, self.processing_end_ms)
            queue_delay_ms = round(max(0.0, start_ms - item.arrival_ms), 4)
            self.processing_end_ms = start_ms + processing_ms

        sentinel_preserved = not item.is_sentinel or (accepted and queue_priority == "high")
        return PipelineResult(
            input_id=item.input_id,
            accepted=accepted,
            dedup_hit=dedup_hit,
            cluster_hit=cluster_hit,
            classifier_score=classifier_score,
            queue_priority=queue_priority,
            processing_ms=processing_ms,
            queue_delay_ms=queue_delay_ms,
            queue_depth_at_arrival=queue_depth,
            sentinel_preserved=sentinel_preserved,
            is_sentinel=item.is_sentinel,
            intake_ms=stage_costs["intake_ms"],
            prefilter_ms=stage_costs["prefilter_ms"],
            feature_ms=stage_costs["feature_ms"],
            classifier_ms=stage_costs["classifier_ms"],
            filtered_reason=filtered_reason,
        )

    def _prefilter_reason(self, tokens: list[str]) -> str | None:
        if len(tokens) < self.profile.prefilter_min_tokens:
            return "too_short"
        lowered = set(tokens)
        if any(token in lowered for token in self.profile.prefilter_blocklist):
            return "blocked_token"
        return None

    def _classify(self, tokens: list[str], is_sentinel: bool, cluster_hit: bool) -> float:
        suspicious_hits = sum(token in self.profile.suspicious_keywords for token in tokens)
        sentinel_hits = sum(token in self.profile.sentinel_keywords for token in tokens)
        diversity_bonus = min(len(set(tokens)) / max(len(tokens), 1), 1.0) * 0.18
        raw_score = self.profile.classifier_bias
        raw_score += suspicious_hits * self.profile.classifier_scale
        raw_score += sentinel_hits * (self.profile.classifier_scale + 0.06)
        raw_score += diversity_bonus
        if cluster_hit:
            raw_score -= 0.15
        if is_sentinel:
            raw_score += 0.2
        return max(0.0, min(1.0, raw_score))

    def _processing_cost(
        self,
        tokens: list[str],
        dedup_hit: bool,
        cluster_hit: bool,
        fingerprint: str,
    ) -> dict[str, float]:
        token_count = len(tokens)
        unique_count = len(set(tokens))

        # Per-stage costs (work only, no queue wait)
        intake_ms = 0.3 + token_count * 0.005
        prefilter_ms = 0.4 + token_count * 0.008
        feature_ms = math.log2(max(token_count, 2)) * 0.6 + unique_count * 0.07
        classifier_ms = (token_count ** 1.08) * 0.035 + self.profile.classifier_bias * 0.2

        total_ms = intake_ms + prefilter_ms + feature_ms + classifier_ms
        # The original formula included a base offset; preserve equivalent total
        total_ms += 0.7  # small constant to keep totals consistent with original

        if dedup_hit:
            scale = 0.32
        elif cluster_hit:
            scale = 0.61
        else:
            scale = 1.0

        if scale != 1.0:
            intake_ms *= scale
            prefilter_ms *= scale
            feature_ms *= scale
            classifier_ms *= scale
            total_ms *= scale

        if self.cache_enabled:
            if fingerprint in self.cache:
                cached = self.cache[fingerprint]
                # Return cached costs proportionally scaled
                ratio = cached / max(total_ms, 1e-9)
                intake_ms = round(intake_ms * ratio, 4)
                prefilter_ms = round(prefilter_ms * ratio, 4)
                feature_ms = round(feature_ms * ratio, 4)
                classifier_ms = round(classifier_ms * ratio, 4)
                total_ms = cached
            else:
                self.cache[fingerprint] = round(total_ms * 0.44, 4)

        return {
            "intake_ms": round(intake_ms, 4),
            "prefilter_ms": round(prefilter_ms, 4),
            "feature_ms": round(feature_ms, 4),
            "classifier_ms": round(classifier_ms, 4),
            "total_ms": round(total_ms, 4),
        }

    def _queue_depth(self, arrival_ms: float) -> int:
        if self.processing_end_ms <= arrival_ms:
            return 0
        backlog_ms = self.processing_end_ms - arrival_ms
        return max(1, math.ceil(backlog_ms / 8.0))


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def stable_fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


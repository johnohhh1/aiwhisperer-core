from __future__ import annotations

import random
from collections.abc import Iterator

from aiwhisperer_core.models import GeneratedInput, Profile


# Fallback templates used when a profile does not define its own fixtures.
_FALLBACK_BACKGROUND_TEMPLATES: dict[str, list[str]] = {
    "soc_triage": [
        "Routine endpoint note: host {host} observed normal patching behavior during {window}.",
        "Analyst summary: login sequence from {region} matched baseline for account cohort {cohort}.",
        "Ticket note: email gateway alert closed as informational after review of {artifact}.",
    ],
    "trust_safety": [
        "User report summary: content on thread {thread} was reviewed and found low-severity context.",
        "Moderation queue note: account {account} triggered duplicate low-confidence spam signal from {region}.",
        "Reviewer summary: report category {category} lacked corroborating evidence after policy scan.",
    ],
    "fraud_abuse": [
        "Risk note: transaction batch {batch} matched routine spending pattern for segment {segment}.",
        "Case summary: device {device} produced low-confidence anomaly during {window}.",
        "Review note: refund request from merchant class {merchant} aligned with expected seasonal behavior.",
    ],
}

_FALLBACK_SENTINEL_INPUTS: dict[str, list[str]] = {
    "soc_triage": [
        "High-confidence malware detection summary: privilege escalation observed after suspicious service installation on host atlas-7.",
        "Security alert: repeated anomalous authentication followed by impossible travel on identity piper-admin.",
        "Incident note: outbound beaconing and lateral movement indicators aligned across two endpoints in finance subnet.",
    ],
    "trust_safety": [
        "Critical moderation report: repeated credible self-harm escalation references in live content stream require urgent review.",
        "High-severity abuse report: coordinated harassment campaign targeting a single victim across multiple accounts.",
        "Urgent child-safety report: explicit exploitation indicators surfaced with corroborating account-behavior flags.",
    ],
    "fraud_abuse": [
        "High-risk takeover case: device fingerprint changed alongside password reset and payout reroute attempt on account cedar-55.",
        "Fraud escalation: transaction narrative shows stacked anomaly flags, new payee burst, and geo-velocity mismatch.",
        "Abuse alert: repeated refund exploitation pattern confirmed across linked accounts and payment instruments.",
    ],
}

VARIATION_SNIPPETS = [
    "manual follow-up not yet required",
    "requires lightweight triage only",
    "low actionability despite coherent context",
    "retain for batch review if related evidence appears",
    "insufficient corroboration for escalation",
]

_BASE_WORKLOADS = [
    "benign_background",
    "exact_repetition",
    "templated_variation",
    "high_diversity",
]


def _get_background_templates(profile: Profile) -> list[str]:
    if profile.background_templates:
        return list(profile.background_templates)
    return _FALLBACK_BACKGROUND_TEMPLATES.get(profile.slug, [
        "Routine note: item {host} processed during {window}."
    ])


def _get_sentinel_inputs(profile: Profile) -> list[str]:
    if profile.sentinel_inputs:
        return list(profile.sentinel_inputs)
    return _FALLBACK_SENTINEL_INPUTS.get(profile.slug, [
        "High-priority alert requiring immediate attention."
    ])


def build_inputs(
    *,
    profile: Profile,
    workload: str,
    total_inputs: int,
    input_rate: float,
    sentinel_interval: int,
    seed: int,
) -> Iterator[GeneratedInput]:
    rng = random.Random(seed)
    interval_ms = 1000.0 / input_rate
    profile_templates = _get_background_templates(profile)
    sentinels = _get_sentinel_inputs(profile)
    snippets = _get_variation_snippets(profile)
    repeated_text = _render_background(profile_templates[0], rng, variation_snippets=snippets)

    # For mixed workload, pre-shuffle a cycle of base workload types
    mixed_cycle: list[str] = []

    for index in range(total_inputs):
        is_sentinel = sentinel_interval > 0 and (index + 1) % sentinel_interval == 0
        if is_sentinel:
            text = sentinels[(index // sentinel_interval) % len(sentinels)]
            effective_workload = workload
        elif workload == "benign_background":
            text = _render_background(rng.choice(profile_templates), rng, variation_snippets=snippets)
            effective_workload = workload
        elif workload == "exact_repetition":
            text = repeated_text
            effective_workload = workload
        elif workload == "templated_variation":
            text = _render_background(rng.choice(profile_templates), rng, vary=True, variation_snippets=snippets)
            effective_workload = workload
        elif workload == "high_diversity":
            text = _render_high_diversity(profile_templates, rng, variation_snippets=snippets)
            effective_workload = workload
        elif workload == "mixed":
            # Cycle through base workloads in shuffled order; reshuffle when exhausted
            if not mixed_cycle:
                mixed_cycle = _BASE_WORKLOADS[:]
                rng.shuffle(mixed_cycle)
            selected = mixed_cycle.pop()
            effective_workload = selected
            if selected == "benign_background":
                text = _render_background(rng.choice(profile_templates), rng, variation_snippets=snippets)
            elif selected == "exact_repetition":
                text = repeated_text
            elif selected == "templated_variation":
                text = _render_background(rng.choice(profile_templates), rng, vary=True, variation_snippets=snippets)
            else:  # high_diversity
                text = _render_high_diversity(profile_templates, rng, variation_snippets=snippets)
        else:
            raise ValueError(
                "Unknown workload "
                f"'{workload}'. Expected benign_background, exact_repetition, "
                "templated_variation, high_diversity, or mixed."
            )

        yield GeneratedInput(
            input_id=f"{profile.slug}-{workload}-{index + 1:05d}",
            profile=profile.slug,
            workload=effective_workload,
            text=text,
            arrival_ms=index * interval_ms,
            is_sentinel=is_sentinel,
            metadata={"index": index + 1},
        )


def _get_variation_snippets(profile: Profile) -> list[str]:
    if profile.variation_snippets:
        return list(profile.variation_snippets)
    return VARIATION_SNIPPETS


def _render_background(template: str, rng: random.Random, vary: bool = False, variation_snippets: list[str] | None = None) -> str:
    if variation_snippets is None:
        variation_snippets = VARIATION_SNIPPETS
    values = {
        # SOC triage / general
        "host": rng.choice(["atlas-7", "delta-2", "juniper-4", "nimbus-9"]),
        "window": rng.choice(["overnight maintenance", "the last review window", "scheduled monitoring"]),
        "cohort": rng.choice(["eng-west", "retail-east", "ops-night"]),
        "artifact": rng.choice(["domain cluster", "attachment family", "sender path"]),
        "region": rng.choice(["us-east", "emea", "apac"]),
        # Trust and safety
        "thread": rng.choice(["T-42", "T-51", "T-77"]),
        "account": rng.choice(["orchid-15", "mesa-31", "cedar-55"]),
        "category": rng.choice(["spam", "abuse", "impersonation"]),
        # Fraud / abuse
        "batch": rng.choice(["B-110", "B-204", "B-887"]),
        "segment": rng.choice(["retail", "enterprise", "creator"]),
        "device": rng.choice(["DV-1A", "DV-88", "DV-403"]),
        "merchant": rng.choice(["travel", "gaming", "digital_goods"]),
        # Mass surveillance
        "entity": rng.choice(["hawk-29", "sparrow-77", "crane-04", "wren-51"]),
        "score": str(round(rng.uniform(0.12, 0.45), 2)),
        "msg_count": str(rng.randint(3, 48)),
        "cluster": rng.choice(["C-07", "C-19", "C-33", "C-88"]),
        # Automated targeting
        "signal_count": str(rng.randint(2, 12)),
    }
    text = template.format(**values)
    if vary:
        text += " Context: " + rng.choice(variation_snippets) + "."
    return text


def _render_high_diversity(templates: list[str], rng: random.Random, variation_snippets: list[str] | None = None) -> str:
    base = _render_background(rng.choice(templates), rng, vary=True, variation_snippets=variation_snippets)
    fragments = [
        rng.choice(
            [
                "cross-correlation remained inconclusive",
                "adjacent evidence increased semantic plausibility",
                "downstream routing confidence stayed unstable",
                "feature enrichment produced mixed confidence cues",
            ]
        ),
        rng.choice(
            [
                "triage summary deferred for queue balancing",
                "signal coherence remained above lightweight filter thresholds",
                "cluster assignment shifted after enrichment pass",
                "review priority remained below urgent threshold",
            ]
        ),
    ]
    rng.shuffle(fragments)
    return f"{base} Supplemental note: {'; '.join(fragments)}."

from __future__ import annotations

import json
from pathlib import Path

from aiwhisperer_core.models import Profile


def _config_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "config" / "profiles"


def _fixtures_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "config" / "fixtures"


def list_profiles() -> list[str]:
    return sorted(path.stem for path in _config_dir().glob("*.json"))


def _load_fixture(slug: str) -> dict:
    """Load per-profile fixture JSON from config/fixtures/<slug>.json.

    Returns an empty dict when no fixture file exists for the slug so that
    callers can safely use .get() with a fallback.
    """
    fixture_path = _fixtures_dir() / f"{slug}.json"
    if fixture_path.exists():
        return json.loads(fixture_path.read_text())
    return {}


def load_profile(slug: str) -> Profile:
    path = _config_dir() / f"{slug}.json"
    if not path.exists():
        available = ", ".join(list_profiles())
        raise ValueError(f"Unknown profile '{slug}'. Available profiles: {available}")

    data = json.loads(path.read_text())

    # Per-profile fixture file takes precedence over inline profile-JSON fields,
    # which in turn take precedence over empty defaults.  This allows the fixture
    # files to be the authoritative source while keeping backwards compatibility
    # with profiles that embed the data directly.
    fixture = _load_fixture(slug)

    background_templates = tuple(
        fixture.get("background_templates")
        or data.get("background_templates")
        or []
    )
    sentinel_inputs = tuple(
        fixture.get("sentinel_inputs")
        or data.get("sentinel_inputs")
        or []
    )
    variation_snippets = tuple(
        fixture.get("variation_snippets")
        or data.get("variation_snippets")
        or []
    )

    return Profile(
        slug=data["slug"],
        name=data["name"],
        classifier_bias=data["classifier_bias"],
        classifier_scale=data["classifier_scale"],
        prefilter_min_tokens=data["prefilter_min_tokens"],
        prefilter_blocklist=tuple(data["prefilter_blocklist"]),
        sentinel_keywords=tuple(data["sentinel_keywords"]),
        suspicious_keywords=tuple(data["suspicious_keywords"]),
        queue_priority_threshold=data["queue_priority_threshold"],
        false_negative_cost=float(data.get("false_negative_cost", 0.5)),
        notes=data.get("notes", data.get("domain_notes", "")),
        background_templates=background_templates,
        sentinel_inputs=sentinel_inputs,
        variation_snippets=variation_snippets,
    )


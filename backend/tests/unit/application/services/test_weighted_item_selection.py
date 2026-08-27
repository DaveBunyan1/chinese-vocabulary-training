import random
from datetime import UTC, datetime, timedelta

import pytest

from chinese_learning.application.services.weighted_item_selection import (
    WeightConfig,
    compute_weight,
    select_weighted,
    weighted_sample_without_replacement,
)
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus

FIXED_NOW = datetime(2026, 8, 27, 12, 0, 0, tzinfo=UTC)


def test_new_weighs_more_than_known() -> None:
    w_new = compute_weight(status=KnowledgeStatus.NEW, as_of=FIXED_NOW)
    w_known = compute_weight(status=KnowledgeStatus.KNOWN, as_of=FIXED_NOW)
    assert w_new > w_known


def test_failures_increase_weight() -> None:
    base = compute_weight(
        status=KnowledgeStatus.LEARNING, failed_attempts=0, as_of=FIXED_NOW
    )
    more = compute_weight(
        status=KnowledgeStatus.LEARNING, failed_attempts=3, as_of=FIXED_NOW
    )
    assert more > base


def test_never_practised_boosts() -> None:
    never = compute_weight(
        status=KnowledgeStatus.LEARNING,
        last_practised_at=None,
        as_of=FIXED_NOW,
    )
    recent = compute_weight(
        status=KnowledgeStatus.LEARNING,
        last_practised_at=FIXED_NOW - timedelta(hours=1),
        as_of=FIXED_NOW,
    )
    assert never > recent


def test_stale_items_weigh_more() -> None:
    stale = compute_weight(
        status=KnowledgeStatus.LEARNING,
        last_practised_at=FIXED_NOW - timedelta(days=7),
        as_of=FIXED_NOW,
    )
    fresh = compute_weight(
        status=KnowledgeStatus.LEARNING,
        last_practised_at=FIXED_NOW - timedelta(hours=1),
        as_of=FIXED_NOW,
    )
    assert stale > fresh


def test_due_boost() -> None:
    due = compute_weight(
        status=KnowledgeStatus.KNOWN,
        next_review_at=FIXED_NOW - timedelta(hours=1),
        last_practised_at=FIXED_NOW - timedelta(days=1),
        as_of=FIXED_NOW,
    )
    not_due = compute_weight(
        status=KnowledgeStatus.KNOWN,
        next_review_at=FIXED_NOW + timedelta(days=3),
        last_practised_at=FIXED_NOW - timedelta(days=1),
        as_of=FIXED_NOW,
    )
    assert due > not_due


def test_min_weight_floor() -> None:
    cfg = WeightConfig(
        status_known=0.0,
        failure_boost=0.0,
        never_practised_boost=0.0,
        due_boost=0.0,
        min_weight=0.05,
    )
    w = compute_weight(
        status=KnowledgeStatus.KNOWN,
        as_of=FIXED_NOW,
        config=cfg,
    )
    assert w == 0.05


def test_weighted_sample_respects_k() -> None:
    items = ["a", "b", "c", "d"]
    weights = [1.0, 1.0, 1.0, 1.0]
    chosen = weighted_sample_without_replacement(
        items, weights, k=2, rng=random.Random(0)
    )
    assert len(chosen) == 2
    assert len(set(chosen)) == 2
    assert all(c in items for c in chosen)


def test_weighted_sample_empty() -> None:
    assert weighted_sample_without_replacement([], [], k=3) == []


def test_weighted_sample_k_larger_than_pool() -> None:
    items = ["a", "b"]
    weights = [1.0, 2.0]
    chosen = weighted_sample_without_replacement(items, weights, k=10)
    assert len(chosen) == 2


def test_select_weighted_prefers_high_weight() -> None:
    candidates = ["low", "high"]
    counts = {"low": 0, "high": 0}
    rng = random.Random(42)
    for _ in range(50):
        picked = select_weighted(
            candidates,
            weight_fn=lambda x: 100.0 if x == "high" else 0.1,
            k=1,
            rng=rng,
        )
        counts[picked[0]] += 1
    assert counts["high"] > counts["low"]


def test_invalid_k_raises() -> None:
    with pytest.raises(ValueError, match="k must be at least 1"):
        weighted_sample_without_replacement(["a"], [1.0], k=0)

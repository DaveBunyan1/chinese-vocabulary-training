"""
Weighted sampling for practice item selection.

Higher weight ⇒ more likely to appear in the next exercise.

Factors (tunable via WeightConfig):
- knowledge status (NEW > LEARNING > KNOWN)
- recent failures
- time since last practice (or never practised)
- explicitly due (next_review_at <= now)
"""

import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol, TypeVar

from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus


@dataclass(frozen=True, slots=True)
class WeightConfig:
    """Relative multipliers; all must be > 0."""

    status_new: float = 4.0
    status_learning: float = 2.5
    status_known: float = 1.0
    # Per failed attempt (capped)
    failure_boost: float = 0.75
    max_failure_boost: float = 3.0
    # Hours since last practice → boost = min(hours / scale, max)
    recency_hours_scale: float = 24.0
    max_recency_boost: float = 3.0
    never_practised_boost: float = 2.0
    # Explicit SRS due flag
    due_boost: float = 3.0
    # Floor so nothing has zero probability
    min_weight: float = 0.1


DEFAULT_WEIGHT_CONFIG = WeightConfig()


class KnowledgeFeatures(Protocol):
    """Minimal surface needed to score a knowledge record."""

    @property
    def status(self) -> KnowledgeStatus: ...

    @property
    def failed_attempts(self) -> int: ...

    @property
    def last_practised_at(self) -> datetime | None: ...

    @property
    def next_review_at(self) -> datetime | None: ...


T = TypeVar("T")


def compute_weight(
    *,
    status: KnowledgeStatus,
    failed_attempts: int = 0,
    last_practised_at: datetime | None = None,
    next_review_at: datetime | None = None,
    as_of: datetime | None = None,
    config: WeightConfig = DEFAULT_WEIGHT_CONFIG,
) -> float:
    """Return a positive weight for one knowledge record."""
    now = as_of or datetime.now(UTC)

    if status is KnowledgeStatus.NEW:
        status_w = config.status_new
    elif status is KnowledgeStatus.LEARNING:
        status_w = config.status_learning
    else:
        status_w = config.status_known

    failures = max(0, failed_attempts)
    failure_w = 1.0 + min(failures * config.failure_boost, config.max_failure_boost)

    if last_practised_at is None:
        recency_w = config.never_practised_boost
    else:
        practised = last_practised_at
        if practised.tzinfo is None:
            practised = practised.replace(tzinfo=UTC)
        hours = max(0.0, (now - practised).total_seconds() / 3600.0)
        recency_w = 1.0 + min(
            hours / config.recency_hours_scale, config.max_recency_boost
        )

    due_w = 1.0
    if next_review_at is not None:
        nr = next_review_at
        if nr.tzinfo is None:
            nr = nr.replace(tzinfo=UTC)
        if nr <= now:
            due_w = config.due_boost

    weight = status_w * failure_w * recency_w * due_w
    return max(weight, config.min_weight)


def weighted_sample_without_replacement[T](
    items: Sequence[T],
    weights: Sequence[float],
    k: int,
    rng: random.Random | None = None,
) -> list[T]:
    """
    Sample up to k items without replacement, proportional to weights.

    Uses repeated weighted choice (simple, fine for MVP pool sizes).
    """
    if k < 1:
        raise ValueError("k must be at least 1")
    if len(items) != len(weights):
        raise ValueError("items and weights must have the same length")
    if not items:
        return []

    sampler = rng or random.Random()
    pool_items = list(items)
    pool_weights = [max(float(w), 0.0) for w in weights]
    take = min(k, len(pool_items))
    chosen: list[T] = []

    for _ in range(take):
        total = sum(pool_weights)
        if total <= 0:
            idx = sampler.randrange(len(pool_items))
        else:
            r = sampler.random() * total
            cumulative = 0.0
            idx = len(pool_items) - 1
            for i, w in enumerate(pool_weights):
                cumulative += w
                if r <= cumulative:
                    idx = i
                    break
        chosen.append(pool_items.pop(idx))
        pool_weights.pop(idx)

    return chosen


def select_weighted[T](
    candidates: Sequence[T],
    weight_fn: Callable[[T], float],
    k: int,
    rng: random.Random | None = None,
) -> list[T]:
    """
    Score each candidate with weight_fn(candidate) -> float and sample k items.
    """
    if not candidates:
        return []
    weights = [float(weight_fn(c)) for c in candidates]
    return weighted_sample_without_replacement(candidates, weights, k, rng=rng)

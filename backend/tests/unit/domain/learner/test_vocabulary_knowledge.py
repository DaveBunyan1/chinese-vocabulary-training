from datetime import UTC, datetime
from typing import Any

import pytest

from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.learner.vocabulary_knowledge import VocabularyKnowledge
from chinese_learning.domain.vocabulary.vocabulary_item import VocabularyId


def make_knowledge(**overrides: Any) -> VocabularyKnowledge:
    defaults = {
        "learner_id": LearnerId("learner-1"),
        "vocabulary_id": VocabularyId("vocab-1"),
        "status": KnowledgeStatus.NEW,
        "successful_recalls": 0,
        "failed_recalls": 0,
        "times_seen": 0,
        "times_produced": 0,
        "first_seen_at": None,
        "last_practised_at": None,
        "last_seen_at": None,
        "next_review_at": None,
        "ease_factor": None,
        "interval_days": None,
    }
    defaults.update(overrides)
    return VocabularyKnowledge(**defaults)


NOW = datetime(2026, 8, 20, 12, 0, 0, tzinfo=UTC)


class TestVocabularyKnowledgeInvariants:
    def test_negative_successful_recalls_raises(self):
        with pytest.raises(ValueError, match="cannot be negative"):
            make_knowledge(successful_recalls=-1)

    def test_negative_failed_recalls_raises(self):
        with pytest.raises(ValueError, match="cannot be negative"):
            make_knowledge(failed_recalls=-1)

    def test_negative_times_seen_raises(self):
        with pytest.raises(ValueError, match="cannot be negative"):
            make_knowledge(times_seen=-1)


class TestVocabularyKnowledgeWithSuccess:
    def test_new_becomes_learning_on_first_success(self):
        knowledge = make_knowledge(status=KnowledgeStatus.NEW)
        updated = knowledge.with_success(NOW)

        assert updated.status == KnowledgeStatus.LEARNING
        assert updated.successful_recalls == 1
        assert updated.failed_recalls == 0
        assert updated.times_produced == 1
        assert updated.first_seen_at == NOW
        assert updated.last_practised_at == NOW
        assert updated.last_seen_at == NOW

    def test_learning_stays_learning_before_threshold(self):
        knowledge = make_knowledge(
            status=KnowledgeStatus.LEARNING,
            successful_recalls=1,
        )
        updated = knowledge.with_success(NOW)

        assert updated.status == KnowledgeStatus.LEARNING
        assert updated.successful_recalls == 2

    def test_learning_becomes_known_after_three_successes(self):
        knowledge = make_knowledge(
            status=KnowledgeStatus.LEARNING,
            successful_recalls=2,
        )
        updated = knowledge.with_success(NOW)

        assert updated.status == KnowledgeStatus.KNOWN
        assert updated.successful_recalls == 3

    def test_known_stays_known_on_success(self):
        knowledge = make_knowledge(
            status=KnowledgeStatus.KNOWN,
            successful_recalls=5,
        )
        updated = knowledge.with_success(NOW)

        assert updated.status == KnowledgeStatus.KNOWN
        assert updated.successful_recalls == 6

    def test_original_instance_is_unchanged(self):
        knowledge = make_knowledge(status=KnowledgeStatus.NEW)
        knowledge.with_success(NOW)

        assert knowledge.status == KnowledgeStatus.NEW
        assert knowledge.successful_recalls == 0


class TestVocabularyKnowledgeWithFailure:
    def test_new_stays_new_on_failure(self):
        knowledge = make_knowledge(status=KnowledgeStatus.NEW)
        updated = knowledge.with_failure(NOW)

        assert updated.status == KnowledgeStatus.NEW
        assert updated.failed_recalls == 1
        assert updated.times_produced == 1

    def test_learning_stays_learning_on_failure(self):
        knowledge = make_knowledge(status=KnowledgeStatus.LEARNING)
        updated = knowledge.with_failure(NOW)

        assert updated.status == KnowledgeStatus.LEARNING
        assert updated.failed_recalls == 1

    def test_known_drops_to_learning_on_failure(self):
        knowledge = make_knowledge(status=KnowledgeStatus.KNOWN)
        updated = knowledge.with_failure(NOW)

        assert updated.status == KnowledgeStatus.LEARNING
        assert updated.failed_recalls == 1


class TestVocabularyKnowledgeWithExposure:
    def test_exposure_increments_times_seen_only(self):
        knowledge = make_knowledge(
            status=KnowledgeStatus.LEARNING,
            successful_recalls=2,
            times_seen=3,
        )
        updated = knowledge.with_exposure(NOW)

        assert updated.status == KnowledgeStatus.LEARNING
        assert updated.successful_recalls == 2
        assert updated.times_seen == 4
        assert updated.times_produced == 0
        assert updated.last_practised_at is None
        assert updated.last_seen_at == NOW
        assert updated.first_seen_at == NOW

    def test_first_seen_at_is_set_only_once(self):
        earlier = datetime(2026, 1, 1, tzinfo=UTC)
        knowledge = make_knowledge(first_seen_at=earlier, times_seen=1)

        updated = knowledge.with_exposure(NOW)

        assert updated.first_seen_at == earlier
        assert updated.times_seen == 2


class TestVocabularyKnowledgeProperties:
    def test_total_attempts(self):
        knowledge = make_knowledge(successful_recalls=4, failed_recalls=2)
        assert knowledge.total_attempts == 6

from collections.abc import Callable
from datetime import UTC, datetime

import pytest

from chinese_learning.domain.learner.character_knowledge import CharacterKnowledge
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus

NOW = datetime(2026, 8, 20, 12, 0, 0, tzinfo=UTC)


class TestCharacterKnowledgeInvariants:
    def test_negative_successful_recognitions_raises(
        self, make_character_knowledge: Callable[..., CharacterKnowledge]
    ) -> None:
        with pytest.raises(ValueError, match="cannot be negative"):
            make_character_knowledge(successful_recognitions=-1)

    def test_negative_failed_recognitions_raises(
        self, make_character_knowledge: Callable[..., CharacterKnowledge]
    ) -> None:
        with pytest.raises(ValueError, match="cannot be negative"):
            make_character_knowledge(failed_recognitions=-1)

    def test_negative_correct_pinyin_count_raises(
        self, make_character_knowledge: Callable[..., CharacterKnowledge]
    ) -> None:
        with pytest.raises(ValueError, match="cannot be negative"):
            make_character_knowledge(correct_pinyin_count=-1)

    def test_negative_times_seen_count_raises(
        self, make_character_knowledge: Callable[..., CharacterKnowledge]
    ) -> None:
        with pytest.raises(ValueError, match="cannot be negative"):
            make_character_knowledge(times_seen=-1)


class TestCharacterKnowledgeWithSuccess:
    def test_new_becomes_learning_on_first_success(
        self, make_character_knowledge: Callable[..., CharacterKnowledge]
    ) -> None:
        knowledge = make_character_knowledge(status=KnowledgeStatus.NEW)
        updated = knowledge.with_success(NOW)

        assert updated.status == KnowledgeStatus.LEARNING
        assert updated.successful_recognitions == 1
        assert updated.correct_pinyin_count == 1  # default pinyin_correct=True
        assert updated.first_seen_at == NOW
        assert updated.last_practised_at == NOW

    def test_success_with_incorrect_pinyin(
        self, make_character_knowledge: Callable[..., CharacterKnowledge]
    ) -> None:
        knowledge = make_character_knowledge(status=KnowledgeStatus.NEW)
        updated = knowledge.with_success(NOW, pinyin_correct=False)

        assert updated.successful_recognitions == 1
        assert updated.correct_pinyin_count == 0

    def test_learning_becomes_known_after_three_successes(
        self, make_character_knowledge: Callable[..., CharacterKnowledge]
    ) -> None:
        knowledge = make_character_knowledge(
            status=KnowledgeStatus.LEARNING,
            successful_recognitions=2,
        )
        updated = knowledge.with_success(NOW)

        assert updated.status == KnowledgeStatus.KNOWN
        assert updated.successful_recognitions == 3

    def test_original_instance_is_unchanged(
        self, make_character_knowledge: Callable[..., CharacterKnowledge]
    ) -> None:
        knowledge = make_character_knowledge(status=KnowledgeStatus.NEW)
        knowledge.with_success(NOW)

        assert knowledge.status == KnowledgeStatus.NEW
        assert knowledge.successful_recognitions == 0

    def test_learning_doesnt_update_before_3(
        self, make_character_knowledge: Callable[..., CharacterKnowledge]
    ) -> None:
        knowledge = make_character_knowledge(
            status=KnowledgeStatus.LEARNING, successful_recognitions=1
        )

        updated = knowledge.with_success(NOW)

        assert updated.status == KnowledgeStatus.LEARNING
        assert updated.successful_recognitions == 2


class TestCharacterKnowledgeWithFailure:
    def test_known_drops_to_learning_on_failure(
        self, make_character_knowledge: Callable[..., CharacterKnowledge]
    ) -> None:
        knowledge = make_character_knowledge(status=KnowledgeStatus.KNOWN)
        updated = knowledge.with_failure(NOW)

        assert updated.status == KnowledgeStatus.LEARNING
        assert updated.failed_recognitions == 1
        assert updated.correct_pinyin_count == 0

    def test_learning_remains_on_failure(
        self, make_character_knowledge: Callable[..., CharacterKnowledge]
    ) -> None:
        knowledge = make_character_knowledge(status=KnowledgeStatus.LEARNING)
        updated = knowledge.with_failure(NOW)

        assert updated.status == KnowledgeStatus.LEARNING
        assert updated.failed_recognitions == 1
        assert updated.correct_pinyin_count == 0


class TestCharacterKnowledgeWithExposure:
    def test_exposure_increments_times_seen_only(
        self, make_character_knowledge: Callable[..., CharacterKnowledge]
    ) -> None:
        knowledge = make_character_knowledge(
            status=KnowledgeStatus.LEARNING,
            successful_recognitions=2,
            times_seen=5,
        )
        updated = knowledge.with_exposure(NOW)

        assert updated.status == KnowledgeStatus.LEARNING
        assert updated.successful_recognitions == 2
        assert updated.times_seen == 6
        assert updated.last_practised_at is None
        assert updated.last_seen_at == NOW


class TestCharacterKnowledgeProperties:
    def test_total_attempts(
        self, make_character_knowledge: Callable[..., CharacterKnowledge]
    ) -> None:
        knowledge = make_character_knowledge(
            successful_recognitions=3,
            failed_recognitions=1,
        )
        assert knowledge.total_attempts == 4

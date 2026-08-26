from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from chinese_learning.application.use_cases.get_progress_stats import GetProgressStats
from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.character_knowledge import CharacterKnowledge
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.learner.vocabulary_knowledge import VocabularyKnowledge
from chinese_learning.domain.text_analysis.character import Character
from chinese_learning.domain.vocabulary.vocabulary_item import VocabularyId


@pytest.fixture
def learner_id() -> LearnerId:
    return LearnerId(str(uuid4()))


@pytest.fixture
def vocab_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def char_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def use_case(vocab_repo: AsyncMock, char_repo: AsyncMock) -> GetProgressStats:
    return GetProgressStats(
        vocabulary_knowledge_repo=vocab_repo,
        character_knowledge_repo=char_repo,
    )


@pytest.mark.asyncio
async def test_aggregates_vocab_and_character_stats(
    use_case: GetProgressStats,
    vocab_repo: AsyncMock,
    char_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    vocab_repo.count_by_status.return_value = {
        KnowledgeStatus.NEW: 2,
        KnowledgeStatus.LEARNING: 3,
        KnowledgeStatus.KNOWN: 1,
    }
    char_repo.count_by_status.return_value = {
        KnowledgeStatus.LEARNING: 4,
        KnowledgeStatus.KNOWN: 2,
    }

    vocab_repo.get_all_for_learner.return_value = [
        VocabularyKnowledge(
            learner_id=learner_id,
            vocabulary_id=VocabularyId(str(uuid4())),
            status=KnowledgeStatus.LEARNING,
            successful_recalls=2,
            failed_recalls=1,
            times_seen=5,
        ),
        VocabularyKnowledge(
            learner_id=learner_id,
            vocabulary_id=VocabularyId(str(uuid4())),
            status=KnowledgeStatus.NEW,
            successful_recalls=0,
            failed_recalls=0,
            times_seen=1,
        ),
    ]
    char_repo.get_all_for_learner.return_value = [
        CharacterKnowledge(
            learner_id=learner_id,
            character=Character("学"),
            status=KnowledgeStatus.KNOWN,
            successful_recognitions=3,
            failed_recognitions=0,
            times_seen=4,
        ),
    ]

    result = await use_case.execute(learner_id)

    assert result.vocabulary.by_status.new == 2
    assert result.vocabulary.by_status.learning == 3
    assert result.vocabulary.by_status.known == 1
    assert result.vocabulary.by_status.total == 6
    assert result.vocabulary.total_successful_recalls == 2
    assert result.vocabulary.total_failed_recalls == 1
    assert result.vocabulary.total_times_seen == 6
    assert result.vocabulary.items_practised == 1

    assert result.characters.by_status.learning == 4
    assert result.characters.by_status.known == 2
    assert result.characters.by_status.new == 0
    assert result.characters.total_successful_recognitions == 3
    assert result.characters.items_practised == 1


@pytest.mark.asyncio
async def test_empty_profile(
    use_case: GetProgressStats,
    vocab_repo: AsyncMock,
    char_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    vocab_repo.count_by_status.return_value = {}
    char_repo.count_by_status.return_value = {}
    vocab_repo.get_all_for_learner.return_value = []
    char_repo.get_all_for_learner.return_value = []

    result = await use_case.execute(learner_id)

    assert result.vocabulary.by_status.total == 0
    assert result.characters.by_status.total == 0
    assert result.vocabulary.items_practised == 0

# tests/unit/application/use_cases/test_update_knowledge_on_exposure.py

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from chinese_learning.application.use_cases.update_knowledge_on_exposure import (
    UpdateKnowledgeOnExposure,
    UpdateKnowledgeOnExposureResult,
)
from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.character_knowledge import CharacterKnowledge
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.learner.vocabulary_knowledge import VocabularyKnowledge
from chinese_learning.domain.text_analysis.character import Character
from chinese_learning.domain.vocabulary.vocabulary_item import VocabularyId

FIXED_NOW = datetime(2026, 8, 22, 12, 0, 0, tzinfo=UTC)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_character_knowledge(
    learner_id: LearnerId,
    symbol: str = "学",
    times_seen: int = 0,
) -> CharacterKnowledge:
    return CharacterKnowledge(
        learner_id=learner_id,
        character=Character(symbol),
        status=KnowledgeStatus.NEW,
        times_seen=times_seen,
        first_seen_at=FIXED_NOW if times_seen else None,
        last_seen_at=FIXED_NOW if times_seen else None,
    )


def make_vocabulary_knowledge(
    learner_id: LearnerId,
    vocabulary_id: VocabularyId | None = None,
    times_seen: int = 0,
) -> VocabularyKnowledge:
    return VocabularyKnowledge(
        learner_id=learner_id,
        vocabulary_id=vocabulary_id or VocabularyId(str(uuid4())),
        status=KnowledgeStatus.NEW,
        times_seen=times_seen,
        first_seen_at=FIXED_NOW if times_seen else None,
        last_seen_at=FIXED_NOW if times_seen else None,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def learner_id() -> LearnerId:
    return LearnerId(str(uuid4()))


@pytest.fixture
def character_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def vocabulary_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def use_case(
    character_repo: AsyncMock,
    vocabulary_repo: AsyncMock,
) -> UpdateKnowledgeOnExposure:
    return UpdateKnowledgeOnExposure(
        character_knowledge_repo=character_repo,
        vocabulary_knowledge_repo=vocabulary_repo,
    )


# ===========================================================================
# Character knowledge
# ===========================================================================


@pytest.mark.asyncio
async def test_creates_new_character_knowledge_on_first_exposure(
    use_case: UpdateKnowledgeOnExposure,
    character_repo: AsyncMock,
    vocabulary_repo: AsyncMock,
    learner_id: LearnerId,
):
    character_repo.get_many.return_value = []
    chars = [Character("学"), Character("习")]

    result = await use_case.execute(
        learner_id=learner_id,
        characters=chars,
        vocabulary_ids=[],
        at=FIXED_NOW,
    )

    assert result.character_knowledge_updated == 2
    assert result.vocabulary_knowledge_updated == 0

    character_repo.save_many.assert_awaited_once()
    saved = character_repo.save_many.call_args[0][0]
    assert len(saved) == 2
    assert all(k.times_seen == 1 for k in saved)
    assert all(k.status is KnowledgeStatus.NEW for k in saved)
    assert all(k.first_seen_at == FIXED_NOW for k in saved)
    assert all(k.last_seen_at == FIXED_NOW for k in saved)

    vocabulary_repo.save_many.assert_not_awaited()


@pytest.mark.asyncio
async def test_updates_existing_character_knowledge(
    use_case: UpdateKnowledgeOnExposure,
    character_repo: AsyncMock,
    learner_id: LearnerId,
):
    existing = make_character_knowledge(learner_id, "学", times_seen=3)
    character_repo.get_many.return_value = [existing]

    result = await use_case.execute(
        learner_id=learner_id,
        characters=[Character("学")],
        vocabulary_ids=[],
        at=FIXED_NOW,
    )

    assert result.character_knowledge_updated == 1

    saved = character_repo.save_many.call_args[0][0]
    assert len(saved) == 1
    assert saved[0].times_seen == 4
    assert saved[0].last_seen_at == FIXED_NOW
    # status and recognition counts stay the same on pure exposure
    assert saved[0].status is KnowledgeStatus.NEW
    assert saved[0].successful_recognitions == 0


@pytest.mark.asyncio
async def test_mixed_new_and_existing_characters(
    use_case: UpdateKnowledgeOnExposure,
    character_repo: AsyncMock,
    learner_id: LearnerId,
):
    existing = make_character_knowledge(learner_id, "学", times_seen=2)
    character_repo.get_many.return_value = [existing]

    result = await use_case.execute(
        learner_id=learner_id,
        characters=[Character("学"), Character("习")],
        vocabulary_ids=[],
        at=FIXED_NOW,
    )

    assert result.character_knowledge_updated == 2
    saved = character_repo.save_many.call_args[0][0]
    by_symbol = {str(k.character): k for k in saved}

    assert by_symbol["学"].times_seen == 3
    assert by_symbol["习"].times_seen == 1


# ===========================================================================
# Vocabulary knowledge
# ===========================================================================


@pytest.mark.asyncio
async def test_creates_new_vocabulary_knowledge_on_first_exposure(
    use_case: UpdateKnowledgeOnExposure,
    character_repo: AsyncMock,
    vocabulary_repo: AsyncMock,
    learner_id: LearnerId,
):
    vocabulary_repo.get_many.return_value = []
    vids = [VocabularyId(str(uuid4())), VocabularyId(str(uuid4()))]

    result = await use_case.execute(
        learner_id=learner_id,
        characters=[],
        vocabulary_ids=vids,
        at=FIXED_NOW,
    )

    assert result.character_knowledge_updated == 0
    assert result.vocabulary_knowledge_updated == 2

    vocabulary_repo.save_many.assert_awaited_once()
    saved = vocabulary_repo.save_many.call_args[0][0]
    assert len(saved) == 2
    assert all(k.times_seen == 1 for k in saved)
    assert all(k.status is KnowledgeStatus.NEW for k in saved)

    character_repo.save_many.assert_not_awaited()


@pytest.mark.asyncio
async def test_updates_existing_vocabulary_knowledge(
    use_case: UpdateKnowledgeOnExposure,
    vocabulary_repo: AsyncMock,
    learner_id: LearnerId,
):
    vid = VocabularyId(str(uuid4()))
    existing = make_vocabulary_knowledge(learner_id, vid, times_seen=5)
    vocabulary_repo.get_many.return_value = [existing]

    result = await use_case.execute(
        learner_id=learner_id,
        characters=[],
        vocabulary_ids=[vid],
        at=FIXED_NOW,
    )

    assert result.vocabulary_knowledge_updated == 1
    saved = vocabulary_repo.save_many.call_args[0][0]
    assert saved[0].times_seen == 6
    assert saved[0].last_seen_at == FIXED_NOW


# ===========================================================================
# Combined / edge cases
# ===========================================================================


@pytest.mark.asyncio
async def test_empty_inputs_do_nothing(
    use_case: UpdateKnowledgeOnExposure,
    character_repo: AsyncMock,
    vocabulary_repo: AsyncMock,
    learner_id: LearnerId,
):
    result = await use_case.execute(
        learner_id=learner_id,
        characters=[],
        vocabulary_ids=[],
        at=FIXED_NOW,
    )

    assert result == UpdateKnowledgeOnExposureResult(0, 0)
    character_repo.get_many.assert_not_awaited()
    vocabulary_repo.get_many.assert_not_awaited()
    character_repo.save_many.assert_not_awaited()
    vocabulary_repo.save_many.assert_not_awaited()


@pytest.mark.asyncio
async def test_both_characters_and_vocabulary_are_updated(
    use_case: UpdateKnowledgeOnExposure,
    character_repo: AsyncMock,
    vocabulary_repo: AsyncMock,
    learner_id: LearnerId,
):
    character_repo.get_many.return_value = []
    vocabulary_repo.get_many.return_value = []

    chars = [Character("中"), Character("文")]
    vids = [VocabularyId(str(uuid4()))]

    result = await use_case.execute(
        learner_id=learner_id,
        characters=chars,
        vocabulary_ids=vids,
        at=FIXED_NOW,
    )

    assert result.character_knowledge_updated == 2
    assert result.vocabulary_knowledge_updated == 1
    character_repo.save_many.assert_awaited_once()
    vocabulary_repo.save_many.assert_awaited_once()

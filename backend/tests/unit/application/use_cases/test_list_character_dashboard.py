from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from chinese_learning.application.use_cases.list_character_dashboard import (
    ListCharacterDashboard,
)
from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.character_knowledge import CharacterKnowledge
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.text_analysis.character import Character
from chinese_learning.domain.vocabulary.vocabulary_item import (
    VocabularyId,
    VocabularyItem,
)

FIXED_NOW = datetime(2026, 8, 26, 19, 0, 0, tzinfo=UTC)


def _knowledge(
    learner_id: LearnerId,
    symbol: str,
    status: KnowledgeStatus = KnowledgeStatus.LEARNING,
) -> CharacterKnowledge:
    return CharacterKnowledge(
        learner_id=learner_id,
        character=Character(symbol),
        status=status,
        successful_recognitions=1,
        failed_recognitions=0,
        correct_pinyin_count=1,
        times_seen=3,
        last_seen_at=FIXED_NOW,
    )


def _entry(text: str, pinyin: str, meaning: str) -> VocabularyItem:
    return VocabularyItem(
        id=VocabularyId(str(uuid4())),
        text=text,
        pinyin=pinyin,
        meaning=meaning,
    )


@pytest.fixture
def learner_id() -> LearnerId:
    return LearnerId(str(uuid4()))


@pytest.fixture
def knowledge_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def dictionary() -> MagicMock:
    mock = MagicMock()

    def lookup(text: str) -> VocabularyItem:
        data = {
            "学": ("xué", "study; learn"),
            "习": ("xí", "practice"),
            "中": ("zhōng", "middle"),
        }
        pinyin, meaning = data.get(text, ("xx", "unknown"))
        return _entry(text, pinyin, meaning)

    mock.lookup.side_effect = lookup
    return mock


@pytest.fixture
def use_case(
    knowledge_repo: AsyncMock,
    dictionary: MagicMock,
) -> ListCharacterDashboard:
    return ListCharacterDashboard(
        character_knowledge_repo=knowledge_repo,
        dictionary=dictionary,
    )


@pytest.mark.asyncio
async def test_lists_all_characters(
    use_case: ListCharacterDashboard,
    knowledge_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    knowledge_repo.get_all_for_learner.return_value = [
        _knowledge(learner_id, "学"),
        _knowledge(learner_id, "习", KnowledgeStatus.KNOWN),
    ]
    knowledge_repo.count_by_status.return_value = {
        KnowledgeStatus.LEARNING: 1,
        KnowledgeStatus.KNOWN: 1,
    }

    result = await use_case.execute(learner_id)

    assert result.total == 2
    assert result.items[0].character == "习"  # sorted
    assert result.items[1].character == "学"
    assert result.items[1].pinyin == "xué"
    assert result.status_counts["learning"] == 1
    assert result.status_counts["known"] == 1


@pytest.mark.asyncio
async def test_filters_by_status(
    use_case: ListCharacterDashboard,
    knowledge_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    knowledge_repo.get_all_for_learner.return_value = [
        _knowledge(learner_id, "学", KnowledgeStatus.NEW),
        _knowledge(learner_id, "习", KnowledgeStatus.LEARNING),
    ]
    knowledge_repo.count_by_status.return_value = {
        KnowledgeStatus.NEW: 1,
        KnowledgeStatus.LEARNING: 1,
    }

    result = await use_case.execute(learner_id, knowledge_status=KnowledgeStatus.NEW)

    assert result.total == 1
    assert result.items[0].character == "学"
    assert result.items[0].status == "new"


@pytest.mark.asyncio
async def test_search_filters(
    use_case: ListCharacterDashboard,
    knowledge_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    knowledge_repo.get_all_for_learner.return_value = [
        _knowledge(learner_id, "学"),
        _knowledge(learner_id, "习"),
    ]
    knowledge_repo.count_by_status.return_value = {}

    result = await use_case.execute(learner_id, search="study")

    assert result.total == 1
    assert result.items[0].character == "学"


@pytest.mark.asyncio
async def test_empty_knowledge(
    use_case: ListCharacterDashboard,
    knowledge_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    knowledge_repo.get_all_for_learner.return_value = []
    knowledge_repo.count_by_status.return_value = {}

    result = await use_case.execute(learner_id)

    assert result.total == 0
    assert result.items == ()

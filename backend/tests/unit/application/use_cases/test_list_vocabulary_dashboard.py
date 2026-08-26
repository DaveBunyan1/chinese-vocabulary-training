from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from chinese_learning.application.use_cases.list_vocabulary_dashboard import (
    ListVocabularyDashboard,
)
from chinese_learning.domain.category.category import (
    Category,
    CategoryId,
    CategoryType,
)
from chinese_learning.domain.category.category_assignment import CategoryAssignment
from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.learner.vocabulary_knowledge import VocabularyKnowledge
from chinese_learning.domain.vocabulary.vocabulary_item import (
    VocabularyId,
    VocabularyItem,
)

FIXED_NOW = datetime(2026, 8, 26, 18, 0, 0, tzinfo=UTC)


def _vid(s: str | None = None) -> VocabularyId:
    return VocabularyId(s or str(uuid4()))


def _item(vid: VocabularyId, text: str, meaning: str = "m") -> VocabularyItem:
    return VocabularyItem(id=vid, text=text, pinyin="p", meaning=meaning)


def _knowledge(
    learner_id: LearnerId,
    vid: VocabularyId,
    status: KnowledgeStatus = KnowledgeStatus.LEARNING,
) -> VocabularyKnowledge:
    return VocabularyKnowledge(
        learner_id=learner_id,
        vocabulary_id=vid,
        status=status,
        successful_recalls=1,
        times_seen=2,
        last_seen_at=FIXED_NOW,
    )


@pytest.fixture
def learner_id() -> LearnerId:
    return LearnerId(str(uuid4()))


@pytest.fixture
def knowledge_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def item_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def category_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def assignment_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def use_case(
    knowledge_repo: AsyncMock,
    item_repo: AsyncMock,
    category_repo: AsyncMock,
    assignment_repo: AsyncMock,
) -> ListVocabularyDashboard:
    return ListVocabularyDashboard(
        vocabulary_knowledge_repo=knowledge_repo,
        vocabulary_item_repo=item_repo,
        category_repo=category_repo,
        category_assignment_repo=assignment_repo,
    )


@pytest.mark.asyncio
async def test_lists_all_knowledge(
    use_case: ListVocabularyDashboard,
    knowledge_repo: AsyncMock,
    item_repo: AsyncMock,
    category_repo: AsyncMock,
    assignment_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    v1, v2 = _vid("v1"), _vid("v2")
    knowledge_repo.get_all_for_learner.return_value = [
        _knowledge(learner_id, v1),
        _knowledge(learner_id, v2, KnowledgeStatus.KNOWN),
    ]
    knowledge_repo.count_by_status.return_value = {
        KnowledgeStatus.LEARNING: 1,
        KnowledgeStatus.KNOWN: 1,
    }
    item_repo.get_many.return_value = [
        _item(v1, "你好", "hello"),
        _item(v2, "谢谢", "thanks"),
    ]
    category_repo.get_all.return_value = []
    assignment_repo.get_by_vocabulary.return_value = []

    result = await use_case.execute(learner_id)

    assert result.total == 2
    assert result.items[0].text == "你好"
    assert result.items[1].text == "谢谢"
    assert result.status_counts["learning"] == 1
    assert result.status_counts["known"] == 1
    assert result.status_counts["new"] == 0


@pytest.mark.asyncio
async def test_filters_by_status(
    use_case: ListVocabularyDashboard,
    knowledge_repo: AsyncMock,
    item_repo: AsyncMock,
    category_repo: AsyncMock,
    assignment_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    v1 = _vid("v1")
    knowledge_repo.get_by_status.return_value = [
        _knowledge(learner_id, v1, KnowledgeStatus.NEW)
    ]
    knowledge_repo.count_by_status.return_value = {KnowledgeStatus.NEW: 1}
    item_repo.get_many.return_value = [_item(v1, "学")]
    category_repo.get_all.return_value = []
    assignment_repo.get_by_vocabulary.return_value = []

    result = await use_case.execute(learner_id, knowledge_status=KnowledgeStatus.NEW)

    assert result.total == 1
    assert result.items[0].status == "new"
    knowledge_repo.get_by_status.assert_awaited_once_with(
        learner_id, KnowledgeStatus.NEW.value
    )


@pytest.mark.asyncio
async def test_filters_by_category(
    use_case: ListVocabularyDashboard,
    knowledge_repo: AsyncMock,
    item_repo: AsyncMock,
    category_repo: AsyncMock,
    assignment_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    v1, v2 = _vid("v1"), _vid("v2")
    cat = CategoryId("cat-food")
    knowledge_repo.get_all_for_learner.return_value = [
        _knowledge(learner_id, v1),
        _knowledge(learner_id, v2),
    ]
    knowledge_repo.count_by_status.return_value = {KnowledgeStatus.LEARNING: 2}
    item_repo.get_many.return_value = [_item(v1, "苹果"), _item(v2, "车")]
    category_repo.get_all.return_value = [
        Category(
            id=cat,
            name="Food",
            type=CategoryType.TOPIC,
        )
    ]
    assignment_repo.get_by_category.return_value = [
        CategoryAssignment(category_id=cat, vocabulary_id=v1)
    ]
    assignment_repo.get_by_vocabulary.return_value = [
        CategoryAssignment(category_id=cat, vocabulary_id=v1)
    ]

    result = await use_case.execute(learner_id, category_id=cat)

    assert result.total == 1
    assert result.items[0].text == "苹果"
    assert result.items[0].categories[0].name == "Food"


@pytest.mark.asyncio
async def test_filters_by_hsk_level(
    use_case: ListVocabularyDashboard,
    knowledge_repo: AsyncMock,
    item_repo: AsyncMock,
    category_repo: AsyncMock,
    assignment_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    v1, v2 = _vid("v1"), _vid("v2")
    hsk1 = CategoryId("hsk-1")
    hsk2 = CategoryId("hsk-2")
    knowledge_repo.get_all_for_learner.return_value = [
        _knowledge(learner_id, v1),
        _knowledge(learner_id, v2),
    ]
    knowledge_repo.count_by_status.return_value = {}
    item_repo.get_many.return_value = [_item(v1, "一"), _item(v2, "两")]
    category_repo.get_all.return_value = [
        Category(id=hsk1, name="HSK 1", type=CategoryType.HSK, hsk_level=1),
        Category(id=hsk2, name="HSK 2", type=CategoryType.HSK, hsk_level=2),
    ]

    async def assignments_for(vid: VocabularyId):
        if str(vid) == "v1":
            return [CategoryAssignment(category_id=hsk1, vocabulary_id=v1)]
        return [CategoryAssignment(category_id=hsk2, vocabulary_id=v2)]

    assignment_repo.get_by_vocabulary.side_effect = assignments_for

    result = await use_case.execute(learner_id, hsk_level=1)

    assert result.total == 1
    assert result.items[0].text == "一"
    assert result.items[0].hsk_level == 1


@pytest.mark.asyncio
async def test_search_filters_text_pinyin_meaning(
    use_case: ListVocabularyDashboard,
    knowledge_repo: AsyncMock,
    item_repo: AsyncMock,
    category_repo: AsyncMock,
    assignment_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    v1, v2 = _vid("v1"), _vid("v2")
    knowledge_repo.get_all_for_learner.return_value = [
        _knowledge(learner_id, v1),
        _knowledge(learner_id, v2),
    ]
    knowledge_repo.count_by_status.return_value = {}
    item_repo.get_many.return_value = [
        VocabularyItem(id=v1, text="你好", pinyin="nǐhǎo", meaning="hello"),
        VocabularyItem(id=v2, text="再见", pinyin="zàijiàn", meaning="goodbye"),
    ]
    category_repo.get_all.return_value = []
    assignment_repo.get_by_vocabulary.return_value = []

    result = await use_case.execute(learner_id, search="hello")

    assert result.total == 1
    assert result.items[0].text == "你好"


@pytest.mark.asyncio
async def test_empty_knowledge_returns_empty(
    use_case: ListVocabularyDashboard,
    knowledge_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    knowledge_repo.get_all_for_learner.return_value = []
    knowledge_repo.count_by_status.return_value = {}

    result = await use_case.execute(learner_id)

    assert result.total == 0
    assert result.items == ()

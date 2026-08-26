from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from chinese_learning.application.use_cases.get_review_queue import (
    GetReviewQueue,
    ReviewItemKind,
    ReviewReason,
)
from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.character_knowledge import CharacterKnowledge
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.learner.vocabulary_knowledge import VocabularyKnowledge
from chinese_learning.domain.text_analysis.character import Character
from chinese_learning.domain.vocabulary.vocabulary_item import (
    VocabularyId,
    VocabularyItem,
)

FIXED_NOW = datetime(2026, 8, 26, 20, 0, 0, tzinfo=UTC)


def _vid(s: str | None = None) -> VocabularyId:
    return VocabularyId(s or str(uuid4()))


def _vocab_knowledge(
    learner_id: LearnerId,
    vid: VocabularyId,
    *,
    status: KnowledgeStatus = KnowledgeStatus.LEARNING,
    next_review_at: datetime | None = None,
) -> VocabularyKnowledge:
    return VocabularyKnowledge(
        learner_id=learner_id,
        vocabulary_id=vid,
        status=status,
        successful_recalls=1,
        failed_recalls=0,
        next_review_at=next_review_at,
    )


def _char_knowledge(
    learner_id: LearnerId,
    symbol: str,
    *,
    status: KnowledgeStatus = KnowledgeStatus.LEARNING,
    next_review_at: datetime | None = None,
) -> CharacterKnowledge:
    return CharacterKnowledge(
        learner_id=learner_id,
        character=Character(symbol),
        status=status,
        successful_recognitions=1,
        next_review_at=next_review_at,
    )


@pytest.fixture
def learner_id() -> LearnerId:
    return LearnerId(str(uuid4()))


@pytest.fixture
def vocab_knowledge_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def char_knowledge_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def item_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def use_case(
    vocab_knowledge_repo: AsyncMock,
    char_knowledge_repo: AsyncMock,
    item_repo: AsyncMock,
) -> GetReviewQueue:
    return GetReviewQueue(
        vocabulary_knowledge_repo=vocab_knowledge_repo,
        character_knowledge_repo=char_knowledge_repo,
        vocabulary_item_repo=item_repo,
    )


@pytest.mark.asyncio
async def test_due_vocabulary_items_first(
    use_case: GetReviewQueue,
    vocab_knowledge_repo: AsyncMock,
    char_knowledge_repo: AsyncMock,
    item_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    v_due = _vid("due")
    v_new = _vid("new")
    vocab_knowledge_repo.get_due_for_review.return_value = [
        _vocab_knowledge(
            learner_id, v_due, next_review_at=FIXED_NOW - timedelta(hours=1)
        )
    ]
    vocab_knowledge_repo.get_all_for_learner.return_value = [
        _vocab_knowledge(
            learner_id, v_due, next_review_at=FIXED_NOW - timedelta(hours=1)
        ),
        _vocab_knowledge(learner_id, v_new, status=KnowledgeStatus.NEW),
    ]
    char_knowledge_repo.get_due_for_review.return_value = []
    char_knowledge_repo.get_all_for_learner.return_value = []
    item_repo.get_many.return_value = [
        VocabularyItem(id=v_due, text="复习", pinyin="fùxí", meaning="review"),
        VocabularyItem(id=v_new, text="新", pinyin="xīn", meaning="new"),
    ]

    result = await use_case.execute(learner_id, as_of=FIXED_NOW, limit=10)

    assert result.due_vocabulary_count == 1
    assert result.unscheduled_vocabulary_count == 1
    assert result.total == 2
    assert result.items[0].reason is ReviewReason.DUE
    assert result.items[0].text == "复习"
    assert result.items[1].reason is ReviewReason.UNSCHEDULED
    assert result.items[1].text == "新"


@pytest.mark.asyncio
async def test_character_queue(
    use_case: GetReviewQueue,
    vocab_knowledge_repo: AsyncMock,
    char_knowledge_repo: AsyncMock,
    item_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    vocab_knowledge_repo.get_due_for_review.return_value = []
    vocab_knowledge_repo.get_all_for_learner.return_value = []
    char_knowledge_repo.get_due_for_review.return_value = [
        _char_knowledge(learner_id, "学", next_review_at=FIXED_NOW - timedelta(days=1))
    ]
    char_knowledge_repo.get_all_for_learner.return_value = [
        _char_knowledge(learner_id, "学", next_review_at=FIXED_NOW - timedelta(days=1)),
        _char_knowledge(learner_id, "习", status=KnowledgeStatus.LEARNING),
    ]
    item_repo.get_many.return_value = []

    result = await use_case.execute(
        learner_id, as_of=FIXED_NOW, include_vocabulary=False
    )

    assert result.due_character_count == 1
    assert result.unscheduled_character_count == 1
    assert all(i.kind is ReviewItemKind.CHARACTER for i in result.items)
    assert result.items[0].character == "学"
    assert result.items[0].reason is ReviewReason.DUE


@pytest.mark.asyncio
async def test_limit_applied(
    use_case: GetReviewQueue,
    vocab_knowledge_repo: AsyncMock,
    char_knowledge_repo: AsyncMock,
    item_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    vids = [_vid(f"v{i}") for i in range(5)]
    vocab_knowledge_repo.get_due_for_review.return_value = [
        _vocab_knowledge(learner_id, v, next_review_at=FIXED_NOW - timedelta(hours=1))
        for v in vids
    ]
    vocab_knowledge_repo.get_all_for_learner.return_value = []
    char_knowledge_repo.get_due_for_review.return_value = []
    char_knowledge_repo.get_all_for_learner.return_value = []
    item_repo.get_many.return_value = [
        VocabularyItem(id=v, text=f"字{i}", pinyin="x", meaning="m")
        for i, v in enumerate(vids)
    ]

    result = await use_case.execute(learner_id, as_of=FIXED_NOW, limit=2)

    assert result.due_vocabulary_count == 5
    assert result.total == 2


@pytest.mark.asyncio
async def test_skip_unscheduled_when_disabled(
    use_case: GetReviewQueue,
    vocab_knowledge_repo: AsyncMock,
    char_knowledge_repo: AsyncMock,
    item_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    v1 = _vid("v1")
    vocab_knowledge_repo.get_due_for_review.return_value = []
    vocab_knowledge_repo.get_all_for_learner.return_value = [
        _vocab_knowledge(learner_id, v1, status=KnowledgeStatus.NEW)
    ]
    char_knowledge_repo.get_due_for_review.return_value = []
    char_knowledge_repo.get_all_for_learner.return_value = []
    item_repo.get_many.return_value = []

    result = await use_case.execute(
        learner_id, as_of=FIXED_NOW, include_unscheduled=False
    )

    assert result.total == 0
    assert result.unscheduled_vocabulary_count == 0


@pytest.mark.asyncio
async def test_invalid_limit_raises(
    use_case: GetReviewQueue,
    learner_id: LearnerId,
) -> None:
    with pytest.raises(ValueError, match="limit"):
        await use_case.execute(learner_id, limit=0)

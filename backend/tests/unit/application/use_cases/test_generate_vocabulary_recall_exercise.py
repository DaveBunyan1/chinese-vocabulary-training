from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from chinese_learning.application.use_cases.generate_vocabulary_recall_exercise import (
    GenerateVocabularyRecallExercise,
    RecallDirection,
)
from chinese_learning.domain.category.category import CategoryId
from chinese_learning.domain.category.category_assignment import CategoryAssignment
from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.learner.vocabulary_knowledge import VocabularyKnowledge
from chinese_learning.domain.practice.exercise import ExerciseStatus, ExerciseType
from chinese_learning.domain.practice.question import QuestionType
from chinese_learning.domain.vocabulary.vocabulary_item import (
    VocabularyId,
    VocabularyItem,
)

FIXED_NOW = datetime(2026, 8, 26, 15, 0, 0, tzinfo=UTC)


def _vid(value: str | None = None) -> VocabularyId:
    return VocabularyId(value or str(uuid4()))


def _item(
    *,
    vid: VocabularyId | None = None,
    text: str = "你好",
    pinyin: str = "nǐhǎo",
    meaning: str = "hello",
) -> VocabularyItem:
    return VocabularyItem(
        id=vid or _vid(),
        text=text,
        pinyin=pinyin,
        meaning=meaning,
    )


def _knowledge(
    learner_id: LearnerId,
    vid: VocabularyId,
    status: KnowledgeStatus = KnowledgeStatus.LEARNING,
) -> VocabularyKnowledge:
    return VocabularyKnowledge(
        learner_id=learner_id,
        vocabulary_id=vid,
        status=status,
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
def assignment_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def use_case(
    knowledge_repo: AsyncMock,
    item_repo: AsyncMock,
    assignment_repo: AsyncMock,
) -> GenerateVocabularyRecallExercise:
    return GenerateVocabularyRecallExercise(
        vocabulary_knowledge_repo=knowledge_repo,
        vocabulary_item_repo=item_repo,
        category_assignment_repo=assignment_repo,
    )


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generates_exercise_from_all_learner_knowledge(
    use_case: GenerateVocabularyRecallExercise,
    knowledge_repo: AsyncMock,
    item_repo: AsyncMock,
    assignment_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    v1, v2, v3 = _vid("v1"), _vid("v2"), _vid("v3")
    knowledge_repo.get_all_for_learner.return_value = [
        _knowledge(learner_id, v1),
        _knowledge(learner_id, v2),
        _knowledge(learner_id, v3),
    ]
    items = [
        _item(vid=v1, text="你好", meaning="hello"),
        _item(vid=v2, text="谢谢", meaning="thanks"),
        _item(vid=v3, text="再见", meaning="goodbye"),
    ]
    item_repo.get_many.return_value = items

    # Deterministic sampling
    import random

    rng = random.Random(42)

    result = await use_case.execute(
        learner_id,
        count=2,
        created_at=FIXED_NOW,
        rng=rng,
    )

    exercise = result.exercise
    assert exercise.learner_id == learner_id
    assert exercise.type is ExerciseType.VOCABULARY_RECALL
    assert exercise.status is ExerciseStatus.PENDING
    assert exercise.question_count == 2
    assert exercise.created_at == FIXED_NOW
    assert exercise.category_id is None
    assert exercise.knowledge_status_filter is None
    assert result.candidate_count == 3

    for q in exercise.questions:
        assert q.type is QuestionType.VOCABULARY_RECALL
        assert q.vocabulary_id is not None
        assert q.character is None
        assert len(q.correct_answers) == 1

    knowledge_repo.get_all_for_learner.assert_awaited_once_with(learner_id)
    knowledge_repo.get_by_status.assert_not_awaited()
    assignment_repo.get_by_category.assert_not_awaited()


@pytest.mark.asyncio
async def test_filters_by_knowledge_status(
    use_case: GenerateVocabularyRecallExercise,
    knowledge_repo: AsyncMock,
    item_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    v1 = _vid("v1")
    knowledge_repo.get_by_status.return_value = [
        _knowledge(learner_id, v1, KnowledgeStatus.NEW)
    ]
    item_repo.get_many.return_value = [_item(vid=v1)]

    result = await use_case.execute(
        learner_id,
        count=5,
        knowledge_status=KnowledgeStatus.NEW,
        created_at=FIXED_NOW,
    )

    assert result.exercise.question_count == 1
    assert result.exercise.knowledge_status_filter is KnowledgeStatus.NEW
    assert result.candidate_count == 1
    knowledge_repo.get_by_status.assert_awaited_once_with(
        learner_id, KnowledgeStatus.NEW.value
    )
    knowledge_repo.get_all_for_learner.assert_not_awaited()


@pytest.mark.asyncio
async def test_filters_by_category(
    use_case: GenerateVocabularyRecallExercise,
    knowledge_repo: AsyncMock,
    item_repo: AsyncMock,
    assignment_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    v1, v2, v3 = _vid("v1"), _vid("v2"), _vid("v3")
    cat_id = CategoryId("cat-food")

    knowledge_repo.get_all_for_learner.return_value = [
        _knowledge(learner_id, v1),
        _knowledge(learner_id, v2),
        _knowledge(learner_id, v3),
    ]
    # Only v1 and v3 are in the category
    assignment_repo.get_by_category.return_value = [
        CategoryAssignment(category_id=cat_id, vocabulary_id=v1),
        CategoryAssignment(category_id=cat_id, vocabulary_id=v3),
    ]
    item_repo.get_many.return_value = [
        _item(vid=v1, text="苹果", meaning="apple"),
        _item(vid=v3, text="香蕉", meaning="banana"),
    ]

    result = await use_case.execute(
        learner_id,
        count=10,
        category_id=cat_id,
        created_at=FIXED_NOW,
    )

    assert result.candidate_count == 2
    assert result.exercise.question_count == 2
    assert result.exercise.category_id == cat_id
    assignment_repo.get_by_category.assert_awaited_once_with(cat_id)


@pytest.mark.asyncio
async def test_filters_by_status_and_category(
    use_case: GenerateVocabularyRecallExercise,
    knowledge_repo: AsyncMock,
    item_repo: AsyncMock,
    assignment_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    v1, v2 = _vid("v1"), _vid("v2")
    cat_id = CategoryId("cat-hsk1")

    knowledge_repo.get_by_status.return_value = [
        _knowledge(learner_id, v1, KnowledgeStatus.LEARNING),
        _knowledge(learner_id, v2, KnowledgeStatus.LEARNING),
    ]
    assignment_repo.get_by_category.return_value = [
        CategoryAssignment(category_id=cat_id, vocabulary_id=v1),
    ]
    item_repo.get_many.return_value = [_item(vid=v1)]

    result = await use_case.execute(
        learner_id,
        count=5,
        category_id=cat_id,
        knowledge_status=KnowledgeStatus.LEARNING,
        created_at=FIXED_NOW,
    )

    assert result.candidate_count == 1
    assert result.exercise.question_count == 1
    assert result.exercise.knowledge_status_filter is KnowledgeStatus.LEARNING
    assert result.exercise.category_id == cat_id


# ---------------------------------------------------------------------------
# Recall directions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_meaning_to_hanzi_direction(
    use_case: GenerateVocabularyRecallExercise,
    knowledge_repo: AsyncMock,
    item_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    v1 = _vid("v1")
    knowledge_repo.get_all_for_learner.return_value = [_knowledge(learner_id, v1)]
    item_repo.get_many.return_value = [
        _item(vid=v1, text="你好", meaning="hello", pinyin="nǐhǎo")
    ]

    result = await use_case.execute(
        learner_id,
        count=1,
        direction=RecallDirection.MEANING_TO_HANZI,
        created_at=FIXED_NOW,
    )

    q = result.exercise.questions[0]
    assert q.prompt == "hello"
    assert q.correct_answers == ("你好",)


@pytest.mark.asyncio
async def test_hanzi_to_meaning_direction(
    use_case: GenerateVocabularyRecallExercise,
    knowledge_repo: AsyncMock,
    item_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    v1 = _vid("v1")
    knowledge_repo.get_all_for_learner.return_value = [_knowledge(learner_id, v1)]
    item_repo.get_many.return_value = [_item(vid=v1, text="你好", meaning="hello")]

    result = await use_case.execute(
        learner_id,
        count=1,
        direction=RecallDirection.HANZI_TO_MEANING,
        created_at=FIXED_NOW,
    )

    q = result.exercise.questions[0]
    assert q.prompt == "你好"
    assert q.correct_answers == ("hello",)


@pytest.mark.asyncio
async def test_pinyin_to_hanzi_direction(
    use_case: GenerateVocabularyRecallExercise,
    knowledge_repo: AsyncMock,
    item_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    v1 = _vid("v1")
    knowledge_repo.get_all_for_learner.return_value = [_knowledge(learner_id, v1)]
    item_repo.get_many.return_value = [
        _item(vid=v1, text="你好", meaning="hello", pinyin="nǐhǎo")
    ]

    result = await use_case.execute(
        learner_id,
        count=1,
        direction=RecallDirection.PINYIN_TO_HANZI,
        created_at=FIXED_NOW,
    )

    q = result.exercise.questions[0]
    assert q.prompt == "nǐhǎo"
    assert q.correct_answers == ("你好",)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_count_less_than_one_raises(
    use_case: GenerateVocabularyRecallExercise,
    learner_id: LearnerId,
) -> None:
    with pytest.raises(ValueError, match="count must be at least 1"):
        await use_case.execute(learner_id, count=0)


@pytest.mark.asyncio
async def test_no_matching_knowledge_raises(
    use_case: GenerateVocabularyRecallExercise,
    knowledge_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    knowledge_repo.get_all_for_learner.return_value = []

    with pytest.raises(ValueError, match="No vocabulary items could be loaded"):
        await use_case.execute(learner_id, count=5)


@pytest.mark.asyncio
async def test_category_filter_with_no_overlap_raises(
    use_case: GenerateVocabularyRecallExercise,
    knowledge_repo: AsyncMock,
    assignment_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    v1 = _vid("v1")
    knowledge_repo.get_all_for_learner.return_value = [_knowledge(learner_id, v1)]
    assignment_repo.get_by_category.return_value = []  # nothing in category

    with pytest.raises(ValueError, match="No vocabulary items could be loaded"):
        await use_case.execute(
            learner_id,
            count=5,
            category_id=CategoryId("empty-cat"),
        )


@pytest.mark.asyncio
async def test_requested_count_larger_than_candidates_returns_all(
    use_case: GenerateVocabularyRecallExercise,
    knowledge_repo: AsyncMock,
    item_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    v1, v2 = _vid("v1"), _vid("v2")
    knowledge_repo.get_all_for_learner.return_value = [
        _knowledge(learner_id, v1),
        _knowledge(learner_id, v2),
    ]
    item_repo.get_many.return_value = [_item(vid=v1), _item(vid=v2)]

    result = await use_case.execute(learner_id, count=50, created_at=FIXED_NOW)

    assert result.candidate_count == 2
    assert result.exercise.question_count == 2


@pytest.mark.asyncio
async def test_questions_have_unique_orders(
    use_case: GenerateVocabularyRecallExercise,
    knowledge_repo: AsyncMock,
    item_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    vids = [_vid(f"v{i}") for i in range(5)]
    knowledge_repo.get_all_for_learner.return_value = [
        _knowledge(learner_id, v) for v in vids
    ]
    item_repo.get_many.return_value = [
        _item(vid=v, text=f"字{i}") for i, v in enumerate(vids)
    ]

    result = await use_case.execute(learner_id, count=5, created_at=FIXED_NOW)

    orders = [q.order for q in result.exercise.questions]
    assert orders == list(range(5))

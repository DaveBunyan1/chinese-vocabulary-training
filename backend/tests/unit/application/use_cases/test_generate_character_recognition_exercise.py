from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from chinese_learning.application.use_cases.generate_character_recognition_exercise import (
    GenerateCharacterRecognitionExercise,
    RecognitionDirection,
)
from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.character_knowledge import CharacterKnowledge
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.practice.exercise import ExerciseStatus, ExerciseType
from chinese_learning.domain.practice.question import QuestionType
from chinese_learning.domain.text_analysis.character import Character
from chinese_learning.domain.vocabulary.vocabulary_item import (
    VocabularyId,
    VocabularyItem,
)

FIXED_NOW = datetime(2026, 8, 26, 16, 0, 0, tzinfo=UTC)


def _knowledge(
    learner_id: LearnerId,
    symbol: str,
    status: KnowledgeStatus = KnowledgeStatus.LEARNING,
) -> CharacterKnowledge:
    return CharacterKnowledge(
        learner_id=learner_id,
        character=Character(symbol),
        status=status,
    )


def _dict_entry(text: str, pinyin: str, meaning: str) -> VocabularyItem:
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

    def _lookup(text: str) -> VocabularyItem:
        defaults = {
            "学": ("xué", "study; learn"),
            "习": ("xí", "practice; habit"),
            "中": ("zhōng", "middle; China"),
            "文": ("wén", "language; literature"),
            "好": ("hǎo", "good"),
        }
        pinyin, meaning = defaults.get(text, ("xx", "unknown"))
        return _dict_entry(text, pinyin, meaning)

    mock.lookup.side_effect = _lookup
    return mock


@pytest.fixture
def use_case(
    knowledge_repo: AsyncMock,
    dictionary: MagicMock,
) -> GenerateCharacterRecognitionExercise:
    return GenerateCharacterRecognitionExercise(
        character_knowledge_repo=knowledge_repo,
        dictionary=dictionary,
    )


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generates_exercise_from_all_learner_knowledge(
    use_case: GenerateCharacterRecognitionExercise,
    knowledge_repo: AsyncMock,
    dictionary: MagicMock,
    learner_id: LearnerId,
) -> None:
    knowledge_repo.get_all_for_learner.return_value = [
        _knowledge(learner_id, "学"),
        _knowledge(learner_id, "习"),
        _knowledge(learner_id, "中"),
    ]

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
    assert exercise.type is ExerciseType.CHARACTER_RECOGNITION
    assert exercise.status is ExerciseStatus.PENDING
    assert exercise.question_count == 2
    assert exercise.created_at == FIXED_NOW
    assert exercise.category_id is None
    assert exercise.knowledge_status_filter is None
    assert result.candidate_count == 3

    for q in exercise.questions:
        assert q.type is QuestionType.CHARACTER_RECOGNITION
        assert q.character is not None
        assert q.vocabulary_id is None
        assert len(q.correct_answers) == 1

    knowledge_repo.get_all_for_learner.assert_awaited_once_with(learner_id)
    knowledge_repo.get_by_status.assert_not_awaited()
    assert dictionary.lookup.call_count == 2


@pytest.mark.asyncio
async def test_filters_by_knowledge_status(
    use_case: GenerateCharacterRecognitionExercise,
    knowledge_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    knowledge_repo.get_by_status.return_value = [
        _knowledge(learner_id, "学", KnowledgeStatus.NEW),
    ]

    result = await use_case.execute(
        learner_id,
        count=5,
        knowledge_status=KnowledgeStatus.NEW,
        created_at=FIXED_NOW,
    )

    assert result.exercise.question_count == 1
    assert result.exercise.knowledge_status_filter is KnowledgeStatus.NEW
    assert result.candidate_count == 1
    # Character repo takes the enum, not .value
    knowledge_repo.get_by_status.assert_awaited_once_with(
        learner_id, KnowledgeStatus.NEW
    )
    knowledge_repo.get_all_for_learner.assert_not_awaited()


# ---------------------------------------------------------------------------
# Recognition directions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_character_to_meaning_direction(
    use_case: GenerateCharacterRecognitionExercise,
    knowledge_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    knowledge_repo.get_all_for_learner.return_value = [
        _knowledge(learner_id, "学"),
    ]

    result = await use_case.execute(
        learner_id,
        count=1,
        direction=RecognitionDirection.CHARACTER_TO_MEANING,
        created_at=FIXED_NOW,
    )

    q = result.exercise.questions[0]
    assert q.prompt == "学"
    assert q.correct_answers == ("study; learn",)
    assert q.character == Character("学")


@pytest.mark.asyncio
async def test_character_to_pinyin_direction(
    use_case: GenerateCharacterRecognitionExercise,
    knowledge_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    knowledge_repo.get_all_for_learner.return_value = [
        _knowledge(learner_id, "学"),
    ]

    result = await use_case.execute(
        learner_id,
        count=1,
        direction=RecognitionDirection.CHARACTER_TO_PINYIN,
        created_at=FIXED_NOW,
    )

    q = result.exercise.questions[0]
    assert q.prompt == "学"
    assert q.correct_answers == ("xué",)


@pytest.mark.asyncio
async def test_meaning_to_character_direction(
    use_case: GenerateCharacterRecognitionExercise,
    knowledge_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    knowledge_repo.get_all_for_learner.return_value = [
        _knowledge(learner_id, "学"),
    ]

    result = await use_case.execute(
        learner_id,
        count=1,
        direction=RecognitionDirection.MEANING_TO_CHARACTER,
        created_at=FIXED_NOW,
    )

    q = result.exercise.questions[0]
    assert q.prompt == "study; learn"
    assert q.correct_answers == ("学",)


@pytest.mark.asyncio
async def test_pinyin_to_character_direction(
    use_case: GenerateCharacterRecognitionExercise,
    knowledge_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    knowledge_repo.get_all_for_learner.return_value = [
        _knowledge(learner_id, "学"),
    ]

    result = await use_case.execute(
        learner_id,
        count=1,
        direction=RecognitionDirection.PINYIN_TO_CHARACTER,
        created_at=FIXED_NOW,
    )

    q = result.exercise.questions[0]
    assert q.prompt == "xué"
    assert q.correct_answers == ("学",)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_count_less_than_one_raises(
    use_case: GenerateCharacterRecognitionExercise,
    learner_id: LearnerId,
) -> None:
    with pytest.raises(ValueError, match="count must be at least 1"):
        await use_case.execute(learner_id, count=0)


@pytest.mark.asyncio
async def test_no_matching_knowledge_raises(
    use_case: GenerateCharacterRecognitionExercise,
    knowledge_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    knowledge_repo.get_all_for_learner.return_value = []

    with pytest.raises(ValueError, match="No characters match"):
        await use_case.execute(learner_id, count=5)


@pytest.mark.asyncio
async def test_requested_count_larger_than_candidates_returns_all(
    use_case: GenerateCharacterRecognitionExercise,
    knowledge_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    knowledge_repo.get_all_for_learner.return_value = [
        _knowledge(learner_id, "学"),
        _knowledge(learner_id, "习"),
    ]

    result = await use_case.execute(learner_id, count=50, created_at=FIXED_NOW)

    assert result.candidate_count == 2
    assert result.exercise.question_count == 2


@pytest.mark.asyncio
async def test_questions_have_unique_orders(
    use_case: GenerateCharacterRecognitionExercise,
    knowledge_repo: AsyncMock,
    learner_id: LearnerId,
) -> None:
    symbols = ["学", "习", "中", "文", "好"]
    knowledge_repo.get_all_for_learner.return_value = [
        _knowledge(learner_id, s) for s in symbols
    ]

    result = await use_case.execute(learner_id, count=5, created_at=FIXED_NOW)

    orders = [q.order for q in result.exercise.questions]
    assert orders == list(range(5))


@pytest.mark.asyncio
async def test_dictionary_lookup_called_for_each_selected_character(
    use_case: GenerateCharacterRecognitionExercise,
    knowledge_repo: AsyncMock,
    dictionary: MagicMock,
    learner_id: LearnerId,
) -> None:
    knowledge_repo.get_all_for_learner.return_value = [
        _knowledge(learner_id, "学"),
        _knowledge(learner_id, "习"),
    ]

    await use_case.execute(learner_id, count=2, created_at=FIXED_NOW)

    looked_up = {call.args[0] for call in dictionary.lookup.call_args_list}
    assert looked_up == {"学", "习"}

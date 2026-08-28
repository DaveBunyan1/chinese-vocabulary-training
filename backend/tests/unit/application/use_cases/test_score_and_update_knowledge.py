from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from chinese_learning.application.use_cases.score_and_update_knowledge import (
    ScoreAndUpdateKnowledge,
)
from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.character_knowledge import CharacterKnowledge
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.learner.vocabulary_knowledge import VocabularyKnowledge
from chinese_learning.domain.practice.exercise import ExerciseId
from chinese_learning.domain.practice.question import (
    Question,
    QuestionId,
    QuestionType,
)
from chinese_learning.domain.text_analysis.character import Character
from chinese_learning.domain.vocabulary.vocabulary_item import VocabularyId

FIXED_NOW = datetime(2026, 8, 26, 17, 0, 0, tzinfo=UTC)


def _vocab_question(
    *,
    vocabulary_id: VocabularyId | None = None,
    prompt: str = "hello",
    correct_answers: tuple[str, ...] = ("你好",),
) -> Question:
    return Question(
        id=QuestionId(str(uuid4())),
        type=QuestionType.VOCABULARY_RECALL,
        order=0,
        prompt=prompt,
        correct_answers=correct_answers,
        vocabulary_id=vocabulary_id or VocabularyId(str(uuid4())),
        character=None,
    )


def _char_question(
    *,
    character: Character | None = None,
    prompt: str = "学",
    correct_answers: tuple[str, ...] = ("study; learn",),
) -> Question:
    return Question(
        id=QuestionId(str(uuid4())),
        type=QuestionType.CHARACTER_RECOGNITION,
        order=0,
        prompt=prompt,
        correct_answers=correct_answers,
        vocabulary_id=None,
        character=character or Character("学"),
    )


@pytest.fixture
def learner_id() -> LearnerId:
    return LearnerId(str(uuid4()))


@pytest.fixture
def exercise_id() -> ExerciseId:
    return ExerciseId(str(uuid4()))


@pytest.fixture
def vocab_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def char_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def use_case(
    vocab_repo: AsyncMock,
    char_repo: AsyncMock,
) -> ScoreAndUpdateKnowledge:
    return ScoreAndUpdateKnowledge(
        vocabulary_knowledge_repo=vocab_repo,
        character_knowledge_repo=char_repo,
    )


# ---------------------------------------------------------------------------
# Scoring logic
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_correct_answer_exact_match(
    use_case: ScoreAndUpdateKnowledge,
    vocab_repo: AsyncMock,
    learner_id: LearnerId,
    exercise_id: ExerciseId,
) -> None:
    vid = VocabularyId("v1")
    question = _vocab_question(vocabulary_id=vid, correct_answers=("你好",))
    vocab_repo.get.return_value = None

    result = await use_case.execute(
        learner_id=learner_id,
        exercise_id=exercise_id,
        question=question,
        raw_answer="你好",
        answered_at=FIXED_NOW,
    )

    assert result.is_correct is True
    assert result.attempt.is_correct is True
    assert result.attempt.raw_answer == "你好"
    assert result.attempt.learner_id == learner_id
    assert result.attempt.exercise_id == exercise_id
    assert result.attempt.question_id == question.id


@pytest.mark.asyncio
async def test_correct_answer_case_insensitive(
    use_case: ScoreAndUpdateKnowledge,
    vocab_repo: AsyncMock,
    learner_id: LearnerId,
    exercise_id: ExerciseId,
) -> None:
    question = _vocab_question(correct_answers=("Hello",))
    vocab_repo.get.return_value = None

    result = await use_case.execute(
        learner_id=learner_id,
        exercise_id=exercise_id,
        question=question,
        raw_answer="  HELLO  ",
        answered_at=FIXED_NOW,
    )

    assert result.is_correct is True


@pytest.mark.asyncio
async def test_incorrect_answer(
    use_case: ScoreAndUpdateKnowledge,
    vocab_repo: AsyncMock,
    learner_id: LearnerId,
    exercise_id: ExerciseId,
) -> None:
    question = _vocab_question(correct_answers=("你好",))
    vocab_repo.get.return_value = None

    result = await use_case.execute(
        learner_id=learner_id,
        exercise_id=exercise_id,
        question=question,
        raw_answer="再见",
        answered_at=FIXED_NOW,
    )

    assert result.is_correct is False
    assert result.attempt.is_correct is False


@pytest.mark.asyncio
async def test_any_correct_answer_accepted(
    use_case: ScoreAndUpdateKnowledge,
    vocab_repo: AsyncMock,
    learner_id: LearnerId,
    exercise_id: ExerciseId,
) -> None:
    question = _vocab_question(correct_answers=("hello", "hi", "hey"))
    vocab_repo.get.return_value = None

    result = await use_case.execute(
        learner_id=learner_id,
        exercise_id=exercise_id,
        question=question,
        raw_answer="Hi",
        answered_at=FIXED_NOW,
    )

    assert result.is_correct is True


# ---------------------------------------------------------------------------
# Vocabulary knowledge updates
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_vocab_success_creates_new_knowledge_and_promotes_to_learning(
    use_case: ScoreAndUpdateKnowledge,
    vocab_repo: AsyncMock,
    learner_id: LearnerId,
    exercise_id: ExerciseId,
) -> None:
    vid = VocabularyId("v1")
    question = _vocab_question(vocabulary_id=vid, correct_answers=("你好",))
    vocab_repo.get.return_value = None

    result = await use_case.execute(
        learner_id=learner_id,
        exercise_id=exercise_id,
        question=question,
        raw_answer="你好",
        answered_at=FIXED_NOW,
    )

    assert result.previous_status is KnowledgeStatus.NEW
    assert result.new_status is KnowledgeStatus.LEARNING

    vocab_repo.save.assert_awaited_once()
    saved: VocabularyKnowledge = vocab_repo.save.call_args[0][0]
    assert saved.vocabulary_id == vid
    assert saved.successful_recalls == 1
    assert saved.failed_recalls == 0
    assert saved.status is KnowledgeStatus.LEARNING
    assert saved.last_practised_at == FIXED_NOW


@pytest.mark.asyncio
async def test_vocab_success_promotes_learning_to_known_after_threshold(
    use_case: ScoreAndUpdateKnowledge,
    vocab_repo: AsyncMock,
    learner_id: LearnerId,
    exercise_id: ExerciseId,
) -> None:
    vid = VocabularyId("v1")
    existing = VocabularyKnowledge(
        learner_id=learner_id,
        vocabulary_id=vid,
        status=KnowledgeStatus.LEARNING,
        successful_recalls=2,  # third success → KNOWN
    )
    vocab_repo.get.return_value = existing
    question = _vocab_question(vocabulary_id=vid, correct_answers=("你好",))

    result = await use_case.execute(
        learner_id=learner_id,
        exercise_id=exercise_id,
        question=question,
        raw_answer="你好",
        answered_at=FIXED_NOW,
    )

    assert result.previous_status is KnowledgeStatus.LEARNING
    assert result.new_status is KnowledgeStatus.KNOWN
    saved: VocabularyKnowledge = vocab_repo.save.call_args[0][0]
    assert saved.successful_recalls == 3
    assert saved.status is KnowledgeStatus.KNOWN


@pytest.mark.asyncio
async def test_vocab_failure_demotes_known_to_learning(
    use_case: ScoreAndUpdateKnowledge,
    vocab_repo: AsyncMock,
    learner_id: LearnerId,
    exercise_id: ExerciseId,
) -> None:
    vid = VocabularyId("v1")
    existing = VocabularyKnowledge(
        learner_id=learner_id,
        vocabulary_id=vid,
        status=KnowledgeStatus.KNOWN,
        successful_recalls=5,
    )
    vocab_repo.get.return_value = existing
    question = _vocab_question(vocabulary_id=vid, correct_answers=("你好",))

    result = await use_case.execute(
        learner_id=learner_id,
        exercise_id=exercise_id,
        question=question,
        raw_answer="wrong",
        answered_at=FIXED_NOW,
    )

    assert result.previous_status is KnowledgeStatus.KNOWN
    assert result.new_status is KnowledgeStatus.LEARNING
    saved: VocabularyKnowledge = vocab_repo.save.call_args[0][0]
    assert saved.failed_recalls == 1
    assert saved.status is KnowledgeStatus.LEARNING


@pytest.mark.asyncio
async def test_vocab_path_does_not_touch_character_repo(
    use_case: ScoreAndUpdateKnowledge,
    vocab_repo: AsyncMock,
    char_repo: AsyncMock,
    learner_id: LearnerId,
    exercise_id: ExerciseId,
) -> None:
    vocab_repo.get.return_value = None
    question = _vocab_question(correct_answers=("你好",))

    await use_case.execute(
        learner_id=learner_id,
        exercise_id=exercise_id,
        question=question,
        raw_answer="你好",
        answered_at=FIXED_NOW,
    )

    char_repo.get.assert_not_awaited()
    char_repo.save.assert_not_awaited()


# ---------------------------------------------------------------------------
# Character knowledge updates
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_char_success_creates_new_knowledge_and_promotes_to_learning(
    use_case: ScoreAndUpdateKnowledge,
    char_repo: AsyncMock,
    learner_id: LearnerId,
    exercise_id: ExerciseId,
) -> None:
    question = _char_question(
        character=Character("学"),
        correct_answers=("study; learn",),
    )
    char_repo.get.return_value = None

    result = await use_case.execute(
        learner_id=learner_id,
        exercise_id=exercise_id,
        question=question,
        raw_answer="study; learn",
        answered_at=FIXED_NOW,
    )

    assert result.is_correct is True
    assert result.previous_status is KnowledgeStatus.NEW
    assert result.new_status is KnowledgeStatus.LEARNING

    char_repo.save.assert_awaited_once()
    saved: CharacterKnowledge = char_repo.save.call_args[0][0]
    assert saved.character == Character("学")
    assert saved.successful_recognitions == 1
    assert saved.correct_pinyin_count == 1
    assert saved.status is KnowledgeStatus.LEARNING


@pytest.mark.asyncio
async def test_char_failure_increments_failed_recognitions(
    use_case: ScoreAndUpdateKnowledge,
    char_repo: AsyncMock,
    learner_id: LearnerId,
    exercise_id: ExerciseId,
) -> None:
    existing = CharacterKnowledge(
        learner_id=learner_id,
        character=Character("学"),
        status=KnowledgeStatus.LEARNING,
        successful_recognitions=1,
    )
    char_repo.get.return_value = existing
    question = _char_question(
        character=Character("学"),
        correct_answers=("study; learn",),
    )

    result = await use_case.execute(
        learner_id=learner_id,
        exercise_id=exercise_id,
        question=question,
        raw_answer="wrong",
        answered_at=FIXED_NOW,
    )

    assert result.is_correct is False
    assert result.new_status is KnowledgeStatus.LEARNING
    saved: CharacterKnowledge = char_repo.save.call_args[0][0]
    assert saved.failed_recognitions == 1
    assert saved.successful_recognitions == 1


@pytest.mark.asyncio
async def test_char_path_does_not_touch_vocab_repo(
    use_case: ScoreAndUpdateKnowledge,
    vocab_repo: AsyncMock,
    char_repo: AsyncMock,
    learner_id: LearnerId,
    exercise_id: ExerciseId,
) -> None:
    char_repo.get.return_value = None
    question = _char_question(correct_answers=("study; learn",))

    await use_case.execute(
        learner_id=learner_id,
        exercise_id=exercise_id,
        question=question,
        raw_answer="study; learn",
        answered_at=FIXED_NOW,
    )

    vocab_repo.get.assert_not_awaited()
    vocab_repo.save.assert_not_awaited()


# ---------------------------------------------------------------------------
# Attempt metadata
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_response_time_is_recorded(
    use_case: ScoreAndUpdateKnowledge,
    vocab_repo: AsyncMock,
    learner_id: LearnerId,
    exercise_id: ExerciseId,
) -> None:
    vocab_repo.get.return_value = None
    question = _vocab_question(correct_answers=("你好",))

    result = await use_case.execute(
        learner_id=learner_id,
        exercise_id=exercise_id,
        question=question,
        raw_answer="你好",
        answered_at=FIXED_NOW,
        response_time_ms=1500,
    )

    assert result.attempt.response_time_ms == 1500
    assert result.attempt.answered_at == FIXED_NOW


@pytest.mark.asyncio
async def test_multi_sense_definition_accepts_any_term(
    use_case: ScoreAndUpdateKnowledge,
    vocab_repo: AsyncMock,
    learner_id: LearnerId,
    exercise_id: ExerciseId,
) -> None:
    """ "I" should pass when the target gloss is "I; me; my"."""
    question = _vocab_question(correct_answers=("I; me; my",))
    vocab_repo.get.return_value = None

    for answer in ("I", "me", "my", "ME", "  my  "):
        result = await use_case.execute(
            learner_id=learner_id,
            exercise_id=exercise_id,
            question=question,
            raw_answer=answer,
            answered_at=FIXED_NOW,
        )
        assert result.is_correct is True, answer


@pytest.mark.asyncio
async def test_multi_sense_rejects_unrelated_term(
    use_case: ScoreAndUpdateKnowledge,
    vocab_repo: AsyncMock,
    learner_id: LearnerId,
    exercise_id: ExerciseId,
) -> None:
    question = _vocab_question(correct_answers=("I; me; my",))
    vocab_repo.get.return_value = None

    result = await use_case.execute(
        learner_id=learner_id,
        exercise_id=exercise_id,
        question=question,
        raw_answer="you",
        answered_at=FIXED_NOW,
    )
    assert result.is_correct is False


@pytest.mark.asyncio
async def test_verb_gloss_accepts_without_leading_to(
    use_case: ScoreAndUpdateKnowledge,
    vocab_repo: AsyncMock,
    learner_id: LearnerId,
    exercise_id: ExerciseId,
) -> None:
    question = _vocab_question(correct_answers=("to study; to learn",))
    vocab_repo.get.return_value = None

    for answer in ("to study", "study", "learn", "to learn"):
        result = await use_case.execute(
            learner_id=learner_id,
            exercise_id=exercise_id,
            question=question,
            raw_answer=answer,
            answered_at=FIXED_NOW,
        )
        assert result.is_correct is True, answer


def test_expand_accepted_answers_splits_senses() -> None:
    terms = ScoreAndUpdateKnowledge._expand_accepted_answers(("he; him; his", "to go"))  # pyright: ignore[reportPrivateUsage]
    assert "he" in terms
    assert "him" in terms
    assert "his" in terms
    assert "he; him; his" in terms  # full gloss still accepted
    assert "to go" in terms
    assert "go" in terms


@pytest.mark.asyncio
async def test_full_multi_sense_string_still_accepted(
    use_case: ScoreAndUpdateKnowledge,
    vocab_repo: AsyncMock,
    learner_id: LearnerId,
    exercise_id: ExerciseId,
) -> None:
    """Answering with the entire gloss must still count as correct."""
    question = _vocab_question(correct_answers=("study; learn",))
    vocab_repo.get.return_value = None

    result = await use_case.execute(
        learner_id=learner_id,
        exercise_id=exercise_id,
        question=question,
        raw_answer="study; learn",
        answered_at=FIXED_NOW,
    )
    assert result.is_correct is True


@pytest.mark.asyncio
async def test_pinyin_tone_number_matches_diacritics(
    use_case: ScoreAndUpdateKnowledge,
    vocab_repo: AsyncMock,
    learner_id: LearnerId,
    exercise_id: ExerciseId,
) -> None:
    question = _vocab_question(correct_answers=("ni3 hao3",))
    vocab_repo.get.return_value = None

    for answer in ("ni3 hao3", "nǐ hǎo", "ni3hao3", "NǏ HǍO"):
        result = await use_case.execute(
            learner_id=learner_id,
            exercise_id=exercise_id,
            question=question,
            raw_answer=answer,
            answered_at=FIXED_NOW,
        )
        assert result.is_correct is True, answer


@pytest.mark.asyncio
async def test_pinyin_wrong_tone_rejected(
    use_case: ScoreAndUpdateKnowledge,
    vocab_repo: AsyncMock,
    learner_id: LearnerId,
    exercise_id: ExerciseId,
) -> None:
    question = _vocab_question(correct_answers=("ni3 hao3",))
    vocab_repo.get.return_value = None

    result = await use_case.execute(
        learner_id=learner_id,
        exercise_id=exercise_id,
        question=question,
        raw_answer="ni2 hao3",
        answered_at=FIXED_NOW,
    )
    assert result.is_correct is False

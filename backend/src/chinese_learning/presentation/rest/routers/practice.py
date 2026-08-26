"""REST endpoints for vocabulary recall and character recognition practice."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.application.use_cases.generate_character_recognition_exercise import (
    GenerateCharacterRecognitionExercise,
    RecognitionDirection,
)
from chinese_learning.application.use_cases.generate_vocabulary_recall_exercise import (
    GenerateVocabularyRecallExercise,
    RecallDirection,
)
from chinese_learning.application.use_cases.score_and_update_knowledge import (
    ScoreAndUpdateKnowledge,
)
from chinese_learning.domain.category.category import CategoryId
from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.practice.exercise import Exercise, ExerciseId
from chinese_learning.domain.practice.question import (
    Question,
    QuestionId,
    QuestionType,
)
from chinese_learning.domain.text_analysis.character import Character
from chinese_learning.domain.vocabulary.vocabulary_item import VocabularyId
from chinese_learning.infrastructure.nlp.cedict_dictionary import CedictDictionary
from chinese_learning.infrastructure.persistence.database import get_db_session
from chinese_learning.infrastructure.persistence.repositories.learner.character_knowledge_repository import (
    CharacterKnowledgeRepository,
)
from chinese_learning.infrastructure.persistence.repositories.learner.vocabulary_knowledge_repository import (
    VocabularyKnowledgeRepository,
)
from chinese_learning.infrastructure.persistence.repositories.linguistic.category_assignment_repository import (
    CategoryAssignmentRepository,
)
from chinese_learning.infrastructure.persistence.repositories.linguistic.vocabulary_item_repository import (
    VocabularyItemRepository,
)
from chinese_learning.presentation.rest.schemas.practice import (
    AnswerOptionSchema,
    ExerciseSchema,
    GenerateCharacterRecognitionRequest,
    GenerateVocabularyRecallRequest,
    QuestionSchema,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)

router = APIRouter(prefix="/practice", tags=["Practice"])

DEFAULT_LEARNER_ID = LearnerId(value="00000000-0000-0000-0000-000000000001")


def get_current_learner_id() -> LearnerId:
    # Hardcoded for single-user vertical slice (same as text import)
    return DEFAULT_LEARNER_ID


def get_cedict_dictionary() -> CedictDictionary:
    dict_path = (
        Path(__file__).resolve().parents[3]
        / "infrastructure"
        / "nlp"
        / "data"
        / "cedict.txt"
    )
    return CedictDictionary(dict_path)


def _parse_knowledge_status(value: str | None) -> KnowledgeStatus | None:
    if value is None:
        return None
    try:
        return KnowledgeStatus(value.lower())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid knowledge_status: {value}. Use new|learning|known.",
        ) from exc


def _question_to_schema(q: Question) -> QuestionSchema:
    return QuestionSchema(
        id=str(q.id),
        type=q.type.value,
        order=q.order,
        prompt=q.prompt,
        correct_answers=list(q.correct_answers),
        vocabulary_id=str(q.vocabulary_id) if q.vocabulary_id else None,
        character=str(q.character) if q.character else None,
        options=[
            AnswerOptionSchema(text=o.text, is_correct=o.is_correct) for o in q.options
        ],
        is_multiple_choice=q.is_multiple_choice,
    )


def _exercise_to_schema(exercise: Exercise, candidate_count: int) -> ExerciseSchema:
    return ExerciseSchema(
        id=str(exercise.id),
        learner_id=str(exercise.learner_id),
        type=exercise.type.value,
        status=exercise.status.value,
        questions=[_question_to_schema(q) for q in exercise.ordered_questions()],
        category_id=str(exercise.category_id) if exercise.category_id else None,
        knowledge_status_filter=(
            exercise.knowledge_status_filter.value
            if exercise.knowledge_status_filter
            else None
        ),
        question_count=exercise.question_count,
        candidate_count=candidate_count,
        created_at=exercise.created_at.isoformat(),
    )


@router.post(
    "/vocabulary-recall",
    response_model=ExerciseSchema,
    status_code=status.HTTP_200_OK,
    summary="Generate a vocabulary recall exercise",
)
async def generate_vocabulary_recall(
    payload: GenerateVocabularyRecallRequest,
    learner_id: LearnerId = Depends(get_current_learner_id),
    session: AsyncSession = Depends(get_db_session),
) -> ExerciseSchema:
    try:
        direction = RecallDirection(payload.direction)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Invalid direction: {payload.direction}. "
                "Use meaning_to_hanzi|hanzi_to_meaning|pinyin_to_hanzi."
            ),
        ) from exc

    knowledge_status = _parse_knowledge_status(payload.knowledge_status)
    category_id = CategoryId(payload.category_id) if payload.category_id else None

    use_case = GenerateVocabularyRecallExercise(
        vocabulary_knowledge_repo=VocabularyKnowledgeRepository(session),
        vocabulary_item_repo=VocabularyItemRepository(session),
        category_assignment_repo=CategoryAssignmentRepository(session),
    )

    try:
        result = await use_case.execute(
            learner_id,
            count=payload.count,
            category_id=category_id,
            knowledge_status=knowledge_status,
            direction=direction,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return _exercise_to_schema(result.exercise, result.candidate_count)


@router.post(
    "/character-recognition",
    response_model=ExerciseSchema,
    status_code=status.HTTP_200_OK,
    summary="Generate a character recognition exercise",
)
async def generate_character_recognition(
    payload: GenerateCharacterRecognitionRequest,
    learner_id: LearnerId = Depends(get_current_learner_id),
    session: AsyncSession = Depends(get_db_session),
    dictionary: CedictDictionary = Depends(get_cedict_dictionary),
) -> ExerciseSchema:
    try:
        direction = RecognitionDirection(payload.direction)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Invalid direction: {payload.direction}. "
                "Use character_to_meaning|character_to_pinyin|"
                "meaning_to_character|pinyin_to_character."
            ),
        ) from exc

    knowledge_status = _parse_knowledge_status(payload.knowledge_status)

    use_case = GenerateCharacterRecognitionExercise(
        character_knowledge_repo=CharacterKnowledgeRepository(session),
        dictionary=dictionary,
    )

    try:
        result = await use_case.execute(
            learner_id,
            count=payload.count,
            knowledge_status=knowledge_status,
            direction=direction,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return _exercise_to_schema(result.exercise, result.candidate_count)


@router.post(
    "/answers",
    response_model=SubmitAnswerResponse,
    status_code=status.HTTP_200_OK,
    summary="Score an answer and update learner knowledge",
)
async def submit_answer(
    payload: SubmitAnswerRequest,
    learner_id: LearnerId = Depends(get_current_learner_id),
    session: AsyncSession = Depends(get_db_session),
) -> SubmitAnswerResponse:
    try:
        question_type = QuestionType(payload.question_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Invalid question_type: {payload.question_type}. "
                "Use vocabulary_recall|character_recognition."
            ),
        ) from exc

    try:
        if question_type is QuestionType.VOCABULARY_RECALL:
            if not payload.vocabulary_id:
                raise ValueError(
                    "vocabulary_id is required for vocabulary_recall questions"
                )
            # TODO: clean up prompt field
            question = Question(
                id=QuestionId(payload.question_id),
                type=question_type,
                order=0,
                prompt="(scored)",  # scoring does not use prompt
                correct_answers=tuple(payload.correct_answers),
                vocabulary_id=VocabularyId(payload.vocabulary_id),
                character=None,
            )
        else:
            if not payload.character:
                raise ValueError(
                    "character is required for character_recognition questions"
                )
            # TODO: cleanup prompt field
            question = Question(
                id=QuestionId(payload.question_id),
                type=question_type,
                order=0,
                prompt="(scored)",  # scoring does not use prompt
                correct_answers=tuple(payload.correct_answers),
                vocabulary_id=None,
                character=Character(payload.character),
            )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    use_case = ScoreAndUpdateKnowledge(
        vocabulary_knowledge_repo=VocabularyKnowledgeRepository(session),
        character_knowledge_repo=CharacterKnowledgeRepository(session),
    )

    result = await use_case.execute(
        learner_id=learner_id,
        exercise_id=ExerciseId(payload.exercise_id),
        question=question,
        raw_answer=payload.raw_answer,
        response_time_ms=payload.response_time_ms,
    )

    await session.commit()

    return SubmitAnswerResponse(
        attempt_id=str(result.attempt.id),
        is_correct=result.is_correct,
        previous_status=(
            result.previous_status.value if result.previous_status else None
        ),
        new_status=result.new_status.value if result.new_status else None,
        raw_answer=result.attempt.raw_answer,
        response_time_ms=result.attempt.response_time_ms,
    )

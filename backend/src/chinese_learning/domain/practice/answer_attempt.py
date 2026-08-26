"""
Domain model for a single answer attempt.

An AnswerAttempt is an immutable record of one learner response to a Question
within an Exercise. Scoring (comparing the answer to correct_answers) and
knowledge updates (with_success / with_failure) are handled by application
services and are intentionally out of scope here.
"""

from dataclasses import dataclass
from datetime import datetime

from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.practice.exercise import ExerciseId
from chinese_learning.domain.practice.question import QuestionId


@dataclass(frozen=True, slots=True)
class AnswerAttemptId:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("AnswerAttemptId cannot be empty")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class AnswerAttempt:
    """
    Immutable learning event: one response to one question.

    Invariants:
    - raw_answer is non-empty (after stripping).
    - response_time_ms, when provided, is non-negative.
    """

    id: AnswerAttemptId
    exercise_id: ExerciseId
    question_id: QuestionId
    learner_id: LearnerId
    raw_answer: str
    is_correct: bool
    answered_at: datetime
    response_time_ms: int | None = None

    def __post_init__(self) -> None:
        if not self.raw_answer.strip():
            raise ValueError("raw_answer cannot be empty")

        if self.response_time_ms is not None and self.response_time_ms < 0:
            raise ValueError("response_time_ms cannot be negative")

    @classmethod
    def create(
        cls,
        *,
        id: AnswerAttemptId,
        exercise_id: ExerciseId,
        question_id: QuestionId,
        learner_id: LearnerId,
        raw_answer: str,
        is_correct: bool,
        answered_at: datetime,
        response_time_ms: int | None = None,
    ) -> AnswerAttempt:
        """Factory for a new attempt. Same as the constructor; kept for consistency."""
        return cls(
            id=id,
            exercise_id=exercise_id,
            question_id=question_id,
            learner_id=learner_id,
            raw_answer=raw_answer,
            is_correct=is_correct,
            answered_at=answered_at,
            response_time_ms=response_time_ms,
        )

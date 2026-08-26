"""
Domain model for a practice Exercise.

An Exercise is the aggregate root for a set of Questions presented to a learner
in one practice session. Generation of the question list is handled by
application-layer services; this model only owns the resulting structure and
lifecycle status.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from chinese_learning.domain.category.category import CategoryId
from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.practice.question import Question, QuestionId


class ExerciseType(StrEnum):
    VOCABULARY_RECALL = "vocabulary_recall"  # meaning/pinyin → hanzi (or reverse)
    CHARACTER_RECOGNITION = "character_recognition"  # show character → meaning/pinyin


class ExerciseStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass(frozen=True, slots=True)
class ExerciseId:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("ExerciseId cannot be empty")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Exercise:
    """
    Domain model for a practice Exercise.

    An Exercise is the aggregate root for a set of Questions presented to a learner
    in one practice session. Generation of the question list is handled by
    application-layer services; this model only owns the resulting structure and
    lifecycle status.
    """

    id: ExerciseId
    learner_id: LearnerId
    type: ExerciseType
    status: ExerciseStatus
    questions: tuple[Question, ...]
    created_at: datetime

    category_id: CategoryId | None = None
    knowledge_status_filter: KnowledgeStatus | None = None

    started_at: datetime | None = None
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.questions:
            raise ValueError("Exercise must contain at least one question")

        ids = [q.id for q in self.questions]

        if len(ids) != len(set(ids)):
            raise ValueError("Exercise questions must have unique IDs")

        orders = [q.order for q in self.questions]

        if len(orders) != len(set(orders)):
            raise ValueError("Exercise questions must have unique order values")

        expected = self.type.value
        for q in self.questions:
            if q.type != expected:
                raise ValueError(
                    f"Question type {q.type} does not match exercise type {self.type}"
                )

    def __repr__(self) -> str:
        return (
            f"Exercise("
            f"id={self.id!r}, "
            f"learner_id={self.learner_id!r}, "
            f"type={self.type!r}, "
            f"status={self.status!r}, "
            f"question_count={self.question_count!r}, "
            f"category_id={self.category_id!r}, "
            f"knowledge_status_filter={self.knowledge_status_filter!r}, "
            f"created_at={self.created_at!r}, "
            f"started_at={self.started_at!r}, "
            f"completed_at={self.completed_at!r}"
            f")"
        )

    def start(self, at: datetime) -> Exercise:
        if self.status is not ExerciseStatus.PENDING:
            raise ValueError(f"Cannot start exercise in status {self.status.value}")
        return Exercise(
            id=self.id,
            learner_id=self.learner_id,
            type=self.type,
            status=ExerciseStatus.IN_PROGRESS,
            questions=self.questions,
            created_at=self.created_at,
            category_id=self.category_id,
            knowledge_status_filter=self.knowledge_status_filter,
            started_at=at,
            completed_at=None,
        )

    def complete(self, at: datetime) -> Exercise:
        if self.status is not ExerciseStatus.IN_PROGRESS:
            raise ValueError(f"Cannot complete exercise in status {self.status.value}")
        return Exercise(
            id=self.id,
            learner_id=self.learner_id,
            type=self.type,
            status=ExerciseStatus.COMPLETED,
            questions=self.questions,
            created_at=self.created_at,
            category_id=self.category_id,
            knowledge_status_filter=self.knowledge_status_filter,
            started_at=self.started_at,
            completed_at=at,
        )

    def question_by_id(self, question_id: QuestionId) -> Question:
        for q in self.questions:
            if q.id == question_id:
                return q
        raise ValueError(f"Question with id {question_id} not found.")

    def ordered_questions(self) -> tuple[Question, ...]:
        return tuple(sorted(self.questions, key=lambda q: q.order))

    @property
    def question_count(self) -> int:
        return len(self.questions)

    @classmethod
    def create(
        cls,
        *,
        id: ExerciseId,
        learner_id: LearnerId,
        type: ExerciseType,
        questions: Sequence[Question],
        created_at: datetime,
        category_id: CategoryId | None = None,
        knowledge_status_filter: KnowledgeStatus | None = None,
    ) -> Exercise:
        """Factory that always starts in PENDING status."""
        return cls(
            id=id,
            learner_id=learner_id,
            type=type,
            status=ExerciseStatus.PENDING,
            questions=tuple(questions),
            created_at=created_at,
            category_id=category_id,
            knowledge_status_filter=knowledge_status_filter,
            started_at=None,
            completed_at=None,
        )

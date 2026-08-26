from collections.abc import Callable
from datetime import UTC, datetime

import pytest

from chinese_learning.domain.category.category import CategoryId
from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.practice.exercise import (
    Exercise,
    ExerciseId,
    ExerciseStatus,
    ExerciseType,
)
from chinese_learning.domain.practice.question import (
    Question,
    QuestionId,
    QuestionType,
)
from chinese_learning.domain.text_analysis.character import Character

NOW = datetime(2026, 8, 26, 12, 0, 0, tzinfo=UTC)
LATER = datetime(2026, 8, 26, 12, 30, 0, tzinfo=UTC)


class TestExerciseId:
    def test_valid_id(self) -> None:
        eid = ExerciseId("ex-1")
        assert str(eid) == "ex-1"

    def test_empty_id_raises(self) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            ExerciseId("")


class TestExerciseSpecialMethods:
    def test_exercise_repr(self, make_exercise: Callable[..., Exercise]) -> None:
        exercise = make_exercise(
            id=ExerciseId(value="ea37ed6c-ff4a-4e7b-9914-0848af10619e")
        )

        assert (
            repr(exercise) == "Exercise("
            "id=ExerciseId(value='ea37ed6c-ff4a-4e7b-9914-0848af10619e'), "
            "learner_id=LearnerId(value='learner-1'), "
            "type=<ExerciseType.VOCABULARY_RECALL: 'vocabulary_recall'>, "
            "status=<ExerciseStatus.PENDING: 'pending'>, "
            "question_count=1, "
            "category_id=None, "
            "knowledge_status_filter=None, "
            "created_at=datetime.datetime(2026, 8, 26, 12, 0, tzinfo=datetime.timezone.utc), "
            "started_at=None, "
            "completed_at=None"
            ")"
        )


class TestExerciseInvariants:
    def test_valid_exercise(self, make_exercise: Callable[..., Exercise]) -> None:
        exercise = make_exercise()
        assert exercise.status is ExerciseStatus.PENDING
        assert exercise.question_count == 1
        assert exercise.started_at is None
        assert exercise.completed_at is None

    def test_empty_questions_raises(
        self, make_exercise: Callable[..., Exercise]
    ) -> None:
        with pytest.raises(ValueError, match="at least one question"):
            make_exercise(questions=())

    def test_duplicate_question_ids_raise(
        self,
        make_exercise: Callable[..., Exercise],
        make_question: Callable[..., Question],
    ) -> None:
        q1 = make_question(id=QuestionId("same"), order=0)
        q2 = make_question(id=QuestionId("same"), order=1)
        with pytest.raises(ValueError, match="unique IDs"):
            make_exercise(questions=(q1, q2))

    def test_duplicate_orders_raise(
        self,
        make_exercise: Callable[..., Exercise],
        make_question: Callable[..., Question],
    ) -> None:
        q1 = make_question(id=QuestionId("q1"), order=0)
        q2 = make_question(id=QuestionId("q2"), order=0)
        with pytest.raises(ValueError, match="unique order"):
            make_exercise(questions=(q1, q2))

    def test_mismatched_question_type_raises(
        self,
        make_exercise: Callable[..., Exercise],
        make_question: Callable[..., Question],
    ) -> None:
        # Character question inside a vocabulary exercise
        char_q = make_question(
            id=QuestionId("cq"),
            type=QuestionType.CHARACTER_RECOGNITION,
            vocabulary_id=None,
            character=Character("学"),
            order=0,
        )
        with pytest.raises(ValueError, match="does not match exercise type"):
            make_exercise(
                type=ExerciseType.VOCABULARY_RECALL,
                questions=(char_q,),
            )


class TestExerciseLifecycle:
    def test_start_from_pending(self, make_exercise: Callable[..., Exercise]) -> None:
        exercise = make_exercise(status=ExerciseStatus.PENDING)
        started = exercise.start(NOW)

        assert started.status is ExerciseStatus.IN_PROGRESS
        assert started.started_at == NOW
        assert started.completed_at is None
        # Original unchanged
        assert exercise.status is ExerciseStatus.PENDING
        assert exercise.started_at is None

    def test_start_from_in_progress_raises(
        self, make_exercise: Callable[..., Exercise]
    ) -> None:
        exercise = make_exercise(status=ExerciseStatus.IN_PROGRESS, started_at=NOW)
        with pytest.raises(ValueError, match="Cannot start"):
            exercise.start(LATER)

    def test_start_from_completed_raises(
        self, make_exercise: Callable[..., Exercise]
    ) -> None:
        exercise = make_exercise(
            status=ExerciseStatus.COMPLETED,
            started_at=NOW,
            completed_at=LATER,
        )
        with pytest.raises(ValueError, match="Cannot start"):
            exercise.start(LATER)

    def test_complete_from_in_progress(
        self, make_exercise: Callable[..., Exercise]
    ) -> None:
        exercise = make_exercise(status=ExerciseStatus.IN_PROGRESS, started_at=NOW)
        completed = exercise.complete(LATER)

        assert completed.status is ExerciseStatus.COMPLETED
        assert completed.started_at == NOW
        assert completed.completed_at == LATER
        # Original unchanged
        assert exercise.status is ExerciseStatus.IN_PROGRESS
        assert exercise.completed_at is None

    def test_complete_from_pending_raises(
        self, make_exercise: Callable[..., Exercise]
    ) -> None:
        exercise = make_exercise(status=ExerciseStatus.PENDING)
        with pytest.raises(ValueError, match="Cannot complete"):
            exercise.complete(NOW)

    def test_complete_from_completed_raises(
        self, make_exercise: Callable[..., Exercise]
    ) -> None:
        exercise = make_exercise(
            status=ExerciseStatus.COMPLETED,
            started_at=NOW,
            completed_at=LATER,
        )
        with pytest.raises(ValueError, match="Cannot complete"):
            exercise.complete(LATER)


class TestExerciseQueries:
    def test_question_by_id(
        self,
        make_exercise: Callable[..., Exercise],
        make_question: Callable[..., Question],
    ) -> None:
        q1 = make_question(id=QuestionId("q1"), order=0)
        q2 = make_question(id=QuestionId("q2"), order=1)
        exercise = make_exercise(questions=(q1, q2))

        assert exercise.question_by_id(QuestionId("q2")) == q2

    def test_question_by_id_missing_raises(
        self, make_exercise: Callable[..., Exercise]
    ) -> None:
        exercise = make_exercise()
        with pytest.raises(ValueError, match="not found"):
            exercise.question_by_id(QuestionId("missing"))

    def test_ordered_questions(
        self,
        make_exercise: Callable[..., Exercise],
        make_question: Callable[..., Question],
    ) -> None:
        q2 = make_question(id=QuestionId("q2"), order=2)
        q0 = make_question(id=QuestionId("q0"), order=0)
        q1 = make_question(id=QuestionId("q1"), order=1)
        exercise = make_exercise(questions=(q2, q0, q1))

        ordered = exercise.ordered_questions()
        assert [q.order for q in ordered] == [0, 1, 2]
        assert [q.id.value for q in ordered] == ["q0", "q1", "q2"]

    def test_create_factory(self, make_question: Callable[..., Question]) -> None:
        q = make_question()
        exercise = Exercise.create(
            id=ExerciseId("ex-new"),
            learner_id=LearnerId("learner-1"),
            type=ExerciseType.VOCABULARY_RECALL,
            questions=(q,),
            created_at=NOW,
            category_id=CategoryId("cat-1"),
            knowledge_status_filter=KnowledgeStatus.LEARNING,
        )
        assert exercise.status is ExerciseStatus.PENDING
        assert exercise.category_id == CategoryId("cat-1")
        assert exercise.knowledge_status_filter is KnowledgeStatus.LEARNING
        assert exercise.started_at is None
        assert exercise.completed_at is None

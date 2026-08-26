from collections.abc import Callable
from datetime import UTC, datetime

import pytest

from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.practice.answer_attempt import (
    AnswerAttempt,
    AnswerAttemptId,
)
from chinese_learning.domain.practice.exercise import ExerciseId
from chinese_learning.domain.practice.question import QuestionId

NOW = datetime(2026, 8, 26, 14, 0, 0, tzinfo=UTC)


class TestAnswerAttemptId:
    def test_valid_id(self) -> None:
        aid = AnswerAttemptId("attempt-1")
        assert str(aid) == "attempt-1"

    def test_empty_id_raises(self) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            AnswerAttemptId("")

    def test_whitespace_id_raises(self) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            AnswerAttemptId("   ")


class TestAnswerAttemptInvariants:
    def test_valid_attempt(
        self, make_answer_attempt: Callable[..., AnswerAttempt]
    ) -> None:
        attempt = make_answer_attempt()
        assert attempt.raw_answer == "hello"
        assert attempt.is_correct is True
        assert attempt.response_time_ms is None
        assert attempt.answered_at == NOW

    def test_valid_attempt_with_response_time(
        self, make_answer_attempt: Callable[..., AnswerAttempt]
    ) -> None:
        attempt = make_answer_attempt(response_time_ms=1250)
        assert attempt.response_time_ms == 1250

    def test_empty_raw_answer_raises(
        self, make_answer_attempt: Callable[..., AnswerAttempt]
    ) -> None:
        with pytest.raises(ValueError, match="raw_answer cannot be empty"):
            make_answer_attempt(raw_answer="")

    def test_whitespace_raw_answer_raises(
        self, make_answer_attempt: Callable[..., AnswerAttempt]
    ) -> None:
        with pytest.raises(ValueError, match="raw_answer cannot be empty"):
            make_answer_attempt(raw_answer="   ")

    def test_negative_response_time_raises(
        self, make_answer_attempt: Callable[..., AnswerAttempt]
    ) -> None:
        with pytest.raises(ValueError, match="cannot be negative"):
            make_answer_attempt(response_time_ms=-1)

    def test_zero_response_time_is_allowed(
        self, make_answer_attempt: Callable[..., AnswerAttempt]
    ) -> None:
        attempt = make_answer_attempt(response_time_ms=0)
        assert attempt.response_time_ms == 0


class TestAnswerAttemptCreate:
    def test_create_factory(self) -> None:
        attempt = AnswerAttempt.create(
            id=AnswerAttemptId("a1"),
            exercise_id=ExerciseId("ex-1"),
            question_id=QuestionId("q-1"),
            learner_id=LearnerId("learner-1"),
            raw_answer="你好",
            is_correct=False,
            answered_at=NOW,
            response_time_ms=800,
        )
        assert attempt.id == AnswerAttemptId("a1")
        assert attempt.exercise_id == ExerciseId("ex-1")
        assert attempt.question_id == QuestionId("q-1")
        assert attempt.learner_id == LearnerId("learner-1")
        assert attempt.raw_answer == "你好"
        assert attempt.is_correct is False
        assert attempt.answered_at == NOW
        assert attempt.response_time_ms == 800

    def test_create_without_response_time(self) -> None:
        attempt = AnswerAttempt.create(
            id=AnswerAttemptId("a2"),
            exercise_id=ExerciseId("ex-1"),
            question_id=QuestionId("q-1"),
            learner_id=LearnerId("learner-1"),
            raw_answer="hello",
            is_correct=True,
            answered_at=NOW,
        )
        assert attempt.response_time_ms is None


class TestAnswerAttemptImmutability:
    def test_is_frozen(self, make_answer_attempt: Callable[..., AnswerAttempt]) -> None:
        attempt = make_answer_attempt()
        with pytest.raises(AttributeError):
            attempt.is_correct = False  # type: ignore[misc]

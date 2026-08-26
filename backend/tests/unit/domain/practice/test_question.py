from collections.abc import Callable

import pytest

from chinese_learning.domain.practice.question import (
    AnswerOption,
    Question,
    QuestionId,
    QuestionType,
)
from chinese_learning.domain.text_analysis.character import Character
from chinese_learning.domain.vocabulary.vocabulary_item import VocabularyId


class TestQuestionId:
    def test_valid_id(self) -> None:
        qid = QuestionId("q-1")
        assert str(qid) == "q-1"

    def test_empty_id_raises(self) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            QuestionId("")

    def test_whitespace_id_raises(self) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            QuestionId("   ")


class TestAnswerOption:
    def test_valid_option(self) -> None:
        opt = AnswerOption(text="hello", is_correct=True)
        assert opt.text == "hello"
        assert opt.is_correct is True

    def test_empty_text_raises(self) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            AnswerOption(text="", is_correct=False)


class TestQuestionSpecialMethods:
    def test_question_repr(self) -> None:
        question = Question(
            id=QuestionId("q1"),
            type=QuestionType.VOCABULARY_RECALL,
            order=0,
            prompt="What does 你好 mean?",
            correct_answers=("hello",),
            vocabulary_id=VocabularyId("v1"),
            options=(
                AnswerOption("hello", True),
                AnswerOption("goodbye", False),
            ),
        )

        assert repr(question) == (
            "Question("
            "id=QuestionId(value='q1'), "
            "type=<QuestionType.VOCABULARY_RECALL: 'vocabulary_recall'>, "
            "order=0, "
            "prompt='What does 你好 mean?', "
            "correct_answers=('hello',), "
            "options=2"
            ")"
        )


class TestQuestionInvariants:
    def test_valid_vocabulary_recall(
        self, make_question: Callable[..., Question]
    ) -> None:
        q = make_question(
            type=QuestionType.VOCABULARY_RECALL,
            vocabulary_id=VocabularyId("vocab-1"),
            character=None,
            prompt="What does 你好 mean?",
            correct_answers=("hello", "hi"),
        )
        assert q.type is QuestionType.VOCABULARY_RECALL
        assert q.vocabulary_id == VocabularyId("vocab-1")
        assert q.character is None
        assert q.is_multiple_choice is False

    def test_valid_character_recognition(
        self, make_question: Callable[..., Question]
    ) -> None:
        q = make_question(
            type=QuestionType.CHARACTER_RECOGNITION,
            vocabulary_id=None,
            character=Character("学"),
            prompt="学",
            correct_answers=("study", "learn"),
        )
        assert q.type is QuestionType.CHARACTER_RECOGNITION
        assert q.character == Character("学")
        assert q.vocabulary_id is None

    def test_negative_order_raises(
        self, make_question: Callable[..., Question]
    ) -> None:
        with pytest.raises(ValueError, match="order cannot be negative"):
            make_question(order=-1)

    def test_empty_prompt_raises(self, make_question: Callable[..., Question]) -> None:
        with pytest.raises(ValueError, match="prompt cannot be empty"):
            make_question(prompt="")

    def test_empty_correct_answers_raises(
        self, make_question: Callable[..., Question]
    ) -> None:
        with pytest.raises(ValueError, match="at least one correct answer"):
            make_question(correct_answers=())

    def test_blank_correct_answer_raises(
        self, make_question: Callable[..., Question]
    ) -> None:
        with pytest.raises(ValueError, match="empty strings"):
            make_question(correct_answers=("hello", "  "))

    def test_vocabulary_recall_requires_vocabulary_id(
        self, make_question: Callable[..., Question]
    ) -> None:
        with pytest.raises(ValueError, match="require vocabulary_id"):
            make_question(
                type=QuestionType.VOCABULARY_RECALL,
                vocabulary_id=None,
                character=None,
            )

    def test_vocabulary_recall_rejects_character(
        self, make_question: Callable[..., Question]
    ) -> None:
        with pytest.raises(ValueError, match="must not have character"):
            make_question(
                type=QuestionType.VOCABULARY_RECALL,
                vocabulary_id=VocabularyId("v1"),
                character=Character("学"),
            )

    def test_character_recognition_requires_character(
        self, make_question: Callable[..., Question]
    ) -> None:
        with pytest.raises(ValueError, match="require character"):
            make_question(
                type=QuestionType.CHARACTER_RECOGNITION,
                vocabulary_id=None,
                character=None,
            )

    def test_character_recognition_rejects_vocabulary_id(
        self, make_question: Callable[..., Question]
    ) -> None:
        with pytest.raises(ValueError, match="must not have vocabulary_id"):
            make_question(
                type=QuestionType.CHARACTER_RECOGNITION,
                vocabulary_id=VocabularyId("v1"),
                character=Character("学"),
            )

    def test_mcq_without_correct_option_raises(
        self, make_question: Callable[..., Question]
    ) -> None:
        with pytest.raises(ValueError, match="at least one correct option"):
            make_question(
                options=(
                    AnswerOption(text="a", is_correct=False),
                    AnswerOption(text="b", is_correct=False),
                )
            )

    def test_mcq_with_correct_option_is_valid(
        self, make_question: Callable[..., Question]
    ) -> None:
        q = make_question(
            options=(
                AnswerOption(text="hello", is_correct=True),
                AnswerOption(text="goodbye", is_correct=False),
            )
        )
        assert q.is_multiple_choice is True
        assert len(q.options) == 2

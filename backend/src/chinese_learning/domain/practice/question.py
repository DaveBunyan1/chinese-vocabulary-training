"""
Domain models for practice questions.

A Question is an entity that belongs to an Exercise aggregate. It represents
one item the learner must answer (vocabulary recall or character recognition).

Answer recording lives in a separate concept (AnswerAttempt) and is intentionally
out of scope for this module.
"""

from dataclasses import dataclass
from enum import StrEnum

from chinese_learning.domain.text_analysis.character import Character
from chinese_learning.domain.vocabulary.vocabulary_item import VocabularyId


class QuestionType(StrEnum):
    VOCABULARY_RECALL = "vocabulary_recall"
    CHARACTER_RECOGNITION = "character_recognition"


@dataclass(frozen=True, slots=True)
class QuestionId:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("QuestionId cannot be empty")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class AnswerOption:
    """
    A single multiple-choice option.

    For free-text / typed-answer questions the options tuple is empty.
    """

    text: str
    is_correct: bool

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("AnswerOption text cannot be empty")


@dataclass(frozen=True, slots=True)
class Question:
    """
    One practice item inside an Exercise.

    Invariants:
    - Exactly one of vocabulary_id / character is set, matching the type.
    - correct_answers is non-empty.
    - order is non-negative.
    - For MCQ, at least one option is marked correct.
    """

    id: QuestionId
    type: QuestionType
    order: int
    prompt: str
    correct_answers: tuple[str, ...]

    vocabulary_id: VocabularyId | None = None
    character: Character | None = None
    options: tuple[AnswerOption, ...] = ()

    def __post_init__(self) -> None:
        if self.order < 0:
            raise ValueError("Question order cannot be negative")

        if not self.prompt.strip():
            raise ValueError("Question prompt cannot be empty")

        if not self.correct_answers:
            raise ValueError("Question must have at least one correct answer")

        for answer in self.correct_answers:
            if not answer.strip():
                raise ValueError("Correct answers cannot be empty strings")

        if self.type is QuestionType.VOCABULARY_RECALL:
            if self.vocabulary_id is None:
                raise ValueError("VOCABULARY_RECALL questions require vocabulary_id")
            if self.character is not None:
                raise ValueError("VOCABULARY_RECALL questions must not have character")
        elif self.type is QuestionType.CHARACTER_RECOGNITION:
            if self.character is None:
                raise ValueError("CHARACTER_RECOGNITION questions require character")
            if self.vocabulary_id is not None:
                raise ValueError(
                    "CHARACTER_RECOGNITION questions must not have vocabulary_id"
                )

        if self.options:
            if not any(opt.is_correct for opt in self.options):
                raise ValueError(
                    "Multiple-choice questions must have at least one correct option"
                )

    def __repr__(self) -> str:
        return (
            f"Question("
            f"id={self.id!r}, "
            f"type={self.type!r}, "
            f"order={self.order!r}, "
            f"prompt={self.prompt!r}, "
            f"correct_answers={self.correct_answers!r}, "
            f"options={len(self.options)!r}"
            f")"
        )

    @property
    def is_multiple_choice(self) -> bool:
        return len(self.options) > 0

"""
Score a learner's answer to a Question and update the corresponding knowledge.

- Compares the raw answer against Question.correct_answers (normalised).
- Creates an immutable AnswerAttempt.
- Calls with_success / with_failure on VocabularyKnowledge or CharacterKnowledge.
- Persists the updated knowledge record.

Exercise lifecycle (start/complete) is left to the caller / API layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.character_knowledge import CharacterKnowledge
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.learner.vocabulary_knowledge import VocabularyKnowledge
from chinese_learning.domain.practice.answer_attempt import (
    AnswerAttempt,
    AnswerAttemptId,
)
from chinese_learning.domain.practice.exercise import ExerciseId
from chinese_learning.domain.practice.question import Question, QuestionType
from chinese_learning.domain.text_analysis.character import Character
from chinese_learning.domain.vocabulary.vocabulary_item import VocabularyId
from chinese_learning.infrastructure.persistence.repositories.learner.character_knowledge_repository import (
    CharacterKnowledgeRepository,
)
from chinese_learning.infrastructure.persistence.repositories.learner.vocabulary_knowledge_repository import (
    VocabularyKnowledgeRepository,
)


def _split_senses(text: str) -> list[str]:
    """Split a gloss on ``;`` / ``/`` while keeping each piece intact."""
    # Normalise separators then split
    unified = text.replace("/", ";")
    return [p for p in unified.split(";") if p.strip()]


@dataclass(frozen=True, slots=True)
class ScoreAndUpdateKnowledgeResult:
    attempt: AnswerAttempt
    is_correct: bool
    # Status after the update (None if somehow no knowledge was touched)
    previous_status: KnowledgeStatus | None
    new_status: KnowledgeStatus | None


class ScoreAndUpdateKnowledge:
    """
    Score one answer and update the learner's knowledge for that item.
    """

    def __init__(
        self,
        vocabulary_knowledge_repo: VocabularyKnowledgeRepository,
        character_knowledge_repo: CharacterKnowledgeRepository,
    ) -> None:
        self._vocab_repo = vocabulary_knowledge_repo
        self._char_repo = character_knowledge_repo

    async def execute(
        self,
        *,
        learner_id: LearnerId,
        exercise_id: ExerciseId,
        question: Question,
        raw_answer: str,
        answered_at: datetime | None = None,
        response_time_ms: int | None = None,
    ) -> ScoreAndUpdateKnowledgeResult:
        now = answered_at or datetime.now(UTC)
        is_correct = self._is_correct(raw_answer, question.correct_answers)

        attempt = AnswerAttempt.create(
            id=AnswerAttemptId(str(uuid4())),
            exercise_id=exercise_id,
            question_id=question.id,
            learner_id=learner_id,
            raw_answer=raw_answer,
            is_correct=is_correct,
            answered_at=now,
            response_time_ms=response_time_ms,
        )

        if question.type is QuestionType.VOCABULARY_RECALL:
            previous, new = await self._update_vocabulary_knowledge(
                learner_id=learner_id,
                vocabulary_id=question.vocabulary_id,  # type: ignore[arg-type]
                is_correct=is_correct,
                at=now,
            )
        elif question.type is QuestionType.CHARACTER_RECOGNITION:
            previous, new = await self._update_character_knowledge(
                learner_id=learner_id,
                character=question.character,  # type: ignore[arg-type]
                is_correct=is_correct,
                at=now,
            )
        else:
            raise ValueError(f"Unsupported question type: {question.type}")

        return ScoreAndUpdateKnowledgeResult(
            attempt=attempt,
            is_correct=is_correct,
            previous_status=previous,
            new_status=new,
        )

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    @staticmethod
    def _is_correct(raw_answer: str, correct_answers: tuple[str, ...]) -> bool:
        """
        Normalised comparison: strip + casefold.

        Accepts any entry in ``correct_answers``. Multi-sense targets such as
        ``"I; me; my"`` or ``"to study; to learn"`` are split so a single
        accepted term (e.g. ``"I"`` or ``"learn"``) counts as correct.
        """
        normalised = raw_answer.strip().casefold()
        if not normalised:
            return False
        accepted = ScoreAndUpdateKnowledge._expand_accepted_answers(correct_answers)
        return normalised in accepted

    @staticmethod
    def _expand_accepted_answers(correct_answers: tuple[str, ...]) -> set[str]:
        """Flatten multi-sense glosses into individual acceptable terms.

        Always keeps the full original string as well, so answering with the
        complete gloss (e.g. ``"study; learn"``) remains valid.
        """
        terms: set[str] = set()
        for answer in correct_answers:
            full = answer.strip().casefold()
            if full:
                terms.add(full)
            for part in _split_senses(answer):
                term = part.strip().casefold()
                if term:
                    terms.add(term)
                    # Also accept without a leading "to " (common in CEDICT verbs)
                    if term.startswith("to ") and len(term) > 3:
                        terms.add(term[3:].strip())
        return terms

    # ------------------------------------------------------------------
    # Knowledge updates
    # ------------------------------------------------------------------

    async def _update_vocabulary_knowledge(
        self,
        *,
        learner_id: LearnerId,
        vocabulary_id: VocabularyId,
        is_correct: bool,
        at: datetime,
    ) -> tuple[KnowledgeStatus | None, KnowledgeStatus | None]:
        existing = await self._vocab_repo.get(learner_id, vocabulary_id)

        if existing is None:
            # First active practice on an item never seen before
            base = VocabularyKnowledge(
                learner_id=learner_id,
                vocabulary_id=vocabulary_id,
                status=KnowledgeStatus.NEW,
            )
        else:
            base = existing

        previous = base.status
        updated = base.with_success(at) if is_correct else base.with_failure(at)
        await self._vocab_repo.save(updated)
        return previous, updated.status

    async def _update_character_knowledge(
        self,
        *,
        learner_id: LearnerId,
        character: Character,
        is_correct: bool,
        at: datetime,
    ) -> tuple[KnowledgeStatus | None, KnowledgeStatus | None]:
        existing = await self._char_repo.get(learner_id, character)

        if existing is None:
            base = CharacterKnowledge(
                learner_id=learner_id,
                character=character,
                status=KnowledgeStatus.NEW,
            )
        else:
            base = existing

        previous = base.status
        if is_correct:
            # pinyin_correct=True by default for MVP; refine when
            # direction-aware scoring is added.
            updated = base.with_success(at, pinyin_correct=True)
        else:
            updated = base.with_failure(at)

        await self._char_repo.save(updated)
        return previous, updated.status

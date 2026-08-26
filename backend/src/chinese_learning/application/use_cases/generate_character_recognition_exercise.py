"""
Generate a character-recognition Exercise filtered by knowledge status.

Builds an in-memory Exercise aggregate. Persistence and scoring are handled
by later branches.

Note: Category filtering is not supported for characters yet — CategoryAssignment
links only to VocabularyItem. Status filtering is supported.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.practice.exercise import (
    Exercise,
    ExerciseId,
    ExerciseType,
)
from chinese_learning.domain.practice.question import (
    Question,
    QuestionId,
    QuestionType,
)
from chinese_learning.domain.text_analysis.character import Character
from chinese_learning.infrastructure.nlp.cedict_dictionary import CedictDictionary
from chinese_learning.infrastructure.persistence.repositories.learner.character_knowledge_repository import (
    CharacterKnowledgeRepository,
)


class RecognitionDirection(StrEnum):
    """Which side of the card is shown as the prompt."""

    CHARACTER_TO_MEANING = "character_to_meaning"  # prompt = 学, answer = study
    CHARACTER_TO_PINYIN = "character_to_pinyin"  # prompt = 学, answer = xué
    MEANING_TO_CHARACTER = "meaning_to_character"  # prompt = study, answer = 学
    PINYIN_TO_CHARACTER = "pinyin_to_character"  # prompt = xué, answer = 学


@dataclass(frozen=True, slots=True)
class GenerateCharacterRecognitionExerciseResult:
    exercise: Exercise
    candidate_count: int


class GenerateCharacterRecognitionExercise:
    """
    Selects characters the learner knows (optionally by status), enriches
    them via CEDICT for meaning/pinyin, builds recognition questions, and
    returns a PENDING Exercise.
    """

    def __init__(
        self,
        character_knowledge_repo: CharacterKnowledgeRepository,
        dictionary: CedictDictionary,
    ) -> None:
        self._knowledge_repo = character_knowledge_repo
        self._dictionary = dictionary

    async def execute(
        self,
        learner_id: LearnerId,
        *,
        count: int = 10,
        knowledge_status: KnowledgeStatus | None = None,
        direction: RecognitionDirection = RecognitionDirection.CHARACTER_TO_MEANING,
        created_at: datetime | None = None,
        rng: random.Random | None = None,
    ) -> GenerateCharacterRecognitionExerciseResult:
        if count < 1:
            raise ValueError("count must be at least 1")

        now = created_at or datetime.now(UTC)
        sampler = rng or random.Random()

        candidates = await self._candidate_characters(
            learner_id=learner_id,
            knowledge_status=knowledge_status,
        )

        if not candidates:
            raise ValueError("No characters match the given filters for this learner")

        sample_size = min(count, len(candidates))
        selected = sampler.sample(candidates, sample_size)

        questions = tuple(
            self._build_question(char, order=i, direction=direction)
            for i, char in enumerate(selected)
        )

        exercise = Exercise.create(
            id=ExerciseId(str(uuid4())),
            learner_id=learner_id,
            type=ExerciseType.CHARACTER_RECOGNITION,
            questions=questions,
            created_at=now,
            category_id=None,  # characters are not category-linked yet
            knowledge_status_filter=knowledge_status,
        )

        return GenerateCharacterRecognitionExerciseResult(
            exercise=exercise,
            candidate_count=len(candidates),
        )

    async def _candidate_characters(
        self,
        *,
        learner_id: LearnerId,
        knowledge_status: KnowledgeStatus | None,
    ) -> list[Character]:
        if knowledge_status is not None:
            # CharacterKnowledgeRepository takes the enum directly (not .value)
            knowledge_list = await self._knowledge_repo.get_by_status(
                learner_id, knowledge_status
            )
        else:
            knowledge_list = await self._knowledge_repo.get_all_for_learner(learner_id)

        return [k.character for k in knowledge_list]

    def _build_question(
        self,
        character: Character,
        *,
        order: int,
        direction: RecognitionDirection,
    ) -> Question:
        # Enrich from CEDICT (falls back to pypinyin / "—" when missing)
        entry = self._dictionary.lookup(character.symbol)

        if direction is RecognitionDirection.CHARACTER_TO_MEANING:
            prompt = character.symbol
            correct_answers = (entry.meaning,)
        elif direction is RecognitionDirection.CHARACTER_TO_PINYIN:
            prompt = character.symbol
            correct_answers = (entry.pinyin,)
        elif direction is RecognitionDirection.MEANING_TO_CHARACTER:
            prompt = entry.meaning
            correct_answers = (character.symbol,)
        elif direction is RecognitionDirection.PINYIN_TO_CHARACTER:
            prompt = entry.pinyin
            correct_answers = (character.symbol,)
        else:
            raise ValueError(f"Unsupported recognition direction: {direction}")

        return Question(
            id=QuestionId(str(uuid4())),
            type=QuestionType.CHARACTER_RECOGNITION,
            order=order,
            prompt=prompt,
            correct_answers=correct_answers,
            vocabulary_id=None,
            character=character,
            options=(),
        )

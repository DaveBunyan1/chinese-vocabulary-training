"""
Generate a character-recognition Exercise filtered by knowledge status.

Builds an in-memory Exercise aggregate. Persistence and scoring are handled
by later branches.

Note: Category filtering is not supported for characters yet — CategoryAssignment
links only to VocabularyItem. Status filtering is supported.
"""

import random
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from chinese_learning.application.services.weighted_item_selection import (
    compute_weight,
    select_weighted,
)
from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.character_knowledge import CharacterKnowledge
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.practice.exercise import Exercise, ExerciseId, ExerciseType
from chinese_learning.domain.practice.question import Question, QuestionId, QuestionType
from chinese_learning.domain.text_analysis.character import Character
from chinese_learning.infrastructure.nlp.cedict_dictionary import CedictDictionary
from chinese_learning.infrastructure.persistence.repositories.learner.character_knowledge_repository import (
    CharacterKnowledgeRepository,
)


class RecognitionDirection(StrEnum):
    CHARACTER_TO_MEANING = "character_to_meaning"
    CHARACTER_TO_PINYIN = "character_to_pinyin"
    MEANING_TO_CHARACTER = "meaning_to_character"
    PINYIN_TO_CHARACTER = "pinyin_to_character"


@dataclass(frozen=True, slots=True)
class GenerateCharacterRecognitionExerciseResult:
    exercise: Exercise
    candidate_count: int


class GenerateCharacterRecognitionExercise:
    """
    Selects characters with weighted sampling, enriches via CEDICT,
    builds recognition questions, and returns a PENDING Exercise.
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

        candidates = await self._candidate_knowledge(
            learner_id=learner_id,
            knowledge_status=knowledge_status,
        )

        if not candidates:
            raise ValueError("No characters match the given filters for this learner")

        selected_knowledge = select_weighted(
            candidates,
            weight_fn=lambda k: compute_weight(
                status=k.status,
                failed_attempts=k.failed_recognitions,
                last_practised_at=k.last_practised_at,
                next_review_at=k.next_review_at,
                as_of=now,
            ),
            k=min(count, len(candidates)),
            rng=sampler,
        )

        questions = tuple(
            self._build_question(k.character, order=i, direction=direction)
            for i, k in enumerate(selected_knowledge)
        )

        exercise = Exercise.create(
            id=ExerciseId(str(uuid4())),
            learner_id=learner_id,
            type=ExerciseType.CHARACTER_RECOGNITION,
            questions=questions,
            created_at=now,
            category_id=None,
            knowledge_status_filter=knowledge_status,
        )

        return GenerateCharacterRecognitionExerciseResult(
            exercise=exercise,
            candidate_count=len(candidates),
        )

    async def _candidate_knowledge(
        self,
        *,
        learner_id: LearnerId,
        knowledge_status: KnowledgeStatus | None,
    ) -> list[CharacterKnowledge]:
        knowledge_list = await self._knowledge_repo.get_all_for_learner(learner_id)
        if knowledge_status is not None:
            knowledge_list = [k for k in knowledge_list if k.status is knowledge_status]
        return knowledge_list

    def _build_question(
        self,
        character: Character,
        *,
        order: int,
        direction: RecognitionDirection,
    ) -> Question:
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

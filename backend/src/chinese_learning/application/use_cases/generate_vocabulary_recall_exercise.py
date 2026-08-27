"""
Generate a vocabulary-recall Exercise filtered by category and/or knowledge status.

Selection uses weighted sampling (status, failures, recency, due).
This use case builds an in-memory Exercise aggregate.
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
from chinese_learning.domain.category.category import CategoryId
from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.learner.vocabulary_knowledge import VocabularyKnowledge
from chinese_learning.domain.practice.exercise import Exercise, ExerciseId, ExerciseType
from chinese_learning.domain.practice.question import Question, QuestionId, QuestionType
from chinese_learning.domain.vocabulary.vocabulary_item import VocabularyItem
from chinese_learning.infrastructure.persistence.repositories.learner.vocabulary_knowledge_repository import (
    VocabularyKnowledgeRepository,
)
from chinese_learning.infrastructure.persistence.repositories.linguistic.category_assignment_repository import (
    CategoryAssignmentRepository,
)
from chinese_learning.infrastructure.persistence.repositories.linguistic.vocabulary_item_repository import (
    VocabularyItemRepository,
)


class RecallDirection(StrEnum):
    """Which side of the card is shown as the prompt."""

    MEANING_TO_HANZI = "meaning_to_hanzi"
    HANZI_TO_MEANING = "hanzi_to_meaning"
    PINYIN_TO_HANZI = "pinyin_to_hanzi"


@dataclass(frozen=True, slots=True)
class GenerateVocabularyRecallExerciseResult:
    exercise: Exercise
    candidate_count: int


class GenerateVocabularyRecallExercise:
    """
    Selects vocabulary with weighted sampling, builds recall questions,
    and returns a PENDING Exercise.
    """

    def __init__(
        self,
        vocabulary_knowledge_repo: VocabularyKnowledgeRepository,
        vocabulary_item_repo: VocabularyItemRepository,
        category_assignment_repo: CategoryAssignmentRepository,
    ) -> None:
        self._knowledge_repo = vocabulary_knowledge_repo
        self._item_repo = vocabulary_item_repo
        self._assignment_repo = category_assignment_repo

    async def execute(
        self,
        learner_id: LearnerId,
        *,
        count: int = 10,
        category_id: CategoryId | None = None,
        knowledge_status: KnowledgeStatus | None = None,
        direction: RecallDirection = RecallDirection.MEANING_TO_HANZI,
        created_at: datetime | None = None,
        rng: random.Random | None = None,
    ) -> GenerateVocabularyRecallExerciseResult:
        if count < 1:
            raise ValueError("count must be at least 1")

        now = created_at or datetime.now(UTC)
        sampler = rng or random.Random()

        candidates = await self._candidate_knowledge(
            learner_id=learner_id,
            knowledge_status=knowledge_status,
            category_id=category_id,
        )

        if not candidates:
            raise ValueError("No vocabulary matches the given filters for this learner")

        selected_knowledge = select_weighted(
            candidates,
            weight_fn=lambda k: compute_weight(
                status=k.status,
                failed_attempts=k.failed_recalls,
                last_practised_at=k.last_practised_at,
                next_review_at=k.next_review_at,
                as_of=now,
            ),
            k=min(count, len(candidates)),
            rng=sampler,
        )

        selected_ids = [k.vocabulary_id for k in selected_knowledge]
        items = await self._item_repo.get_many(selected_ids)
        items_by_id = {str(item.id): item for item in items}

        ordered_items: list[VocabularyItem] = []
        for vid in selected_ids:
            item = items_by_id.get(str(vid))
            if item is not None:
                ordered_items.append(item)

        if not ordered_items:
            raise ValueError(
                "No vocabulary items could be loaded for the selected candidates"
            )

        questions = tuple(
            self._build_question(item, order=i, direction=direction)
            for i, item in enumerate(ordered_items)
        )

        exercise = Exercise.create(
            id=ExerciseId(str(uuid4())),
            learner_id=learner_id,
            type=ExerciseType.VOCABULARY_RECALL,
            questions=questions,
            created_at=now,
            category_id=category_id,
            knowledge_status_filter=knowledge_status,
        )

        return GenerateVocabularyRecallExerciseResult(
            exercise=exercise,
            candidate_count=len(candidates),
        )

    async def _candidate_knowledge(
        self,
        *,
        learner_id: LearnerId,
        knowledge_status: KnowledgeStatus | None,
        category_id: CategoryId | None,
    ) -> list[VocabularyKnowledge]:
        # Load all then filter in memory (avoids SQLEnum string comparison issues)
        knowledge_list = await self._knowledge_repo.get_all_for_learner(learner_id)
        if knowledge_status is not None:
            knowledge_list = [k for k in knowledge_list if k.status is knowledge_status]

        if category_id is not None:
            assignments = await self._assignment_repo.get_by_category(category_id)
            allowed = {a.vocabulary_id.value for a in assignments}
            knowledge_list = [
                k for k in knowledge_list if str(k.vocabulary_id) in allowed
            ]

        return knowledge_list

    def _build_question(
        self,
        item: VocabularyItem,
        *,
        order: int,
        direction: RecallDirection,
    ) -> Question:
        if direction is RecallDirection.MEANING_TO_HANZI:
            prompt = item.meaning
            correct_answers = (item.text,)
        elif direction is RecallDirection.PINYIN_TO_HANZI:
            prompt = item.pinyin
            correct_answers = (item.text,)
        elif direction is RecallDirection.HANZI_TO_MEANING:
            prompt = item.text
            correct_answers = (item.meaning,)
        else:
            raise ValueError(f"Unsupported recall direction: {direction}")

        return Question(
            id=QuestionId(str(uuid4())),
            type=QuestionType.VOCABULARY_RECALL,
            order=order,
            prompt=prompt,
            correct_answers=correct_answers,
            vocabulary_id=item.id,
            character=None,
            options=(),
        )

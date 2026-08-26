"""
Build a review queue from knowledge records.

Priority:
1. Items with next_review_at <= as_of (explicitly due)
2. Unscheduled NEW/LEARNING items (next_review_at is None) — first review

Full SM-2 scheduling of next_review_at is out of scope here; this service
only *selects* what to review.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.character_knowledge import CharacterKnowledge
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.learner.vocabulary_knowledge import VocabularyKnowledge
from chinese_learning.infrastructure.persistence.repositories.learner.character_knowledge_repository import (
    CharacterKnowledgeRepository,
)
from chinese_learning.infrastructure.persistence.repositories.learner.vocabulary_knowledge_repository import (
    VocabularyKnowledgeRepository,
)
from chinese_learning.infrastructure.persistence.repositories.linguistic.vocabulary_item_repository import (
    VocabularyItemRepository,
)


class ReviewItemKind(StrEnum):
    VOCABULARY = "vocabulary"
    CHARACTER = "character"


class ReviewReason(StrEnum):
    DUE = "due"  # next_review_at <= as_of
    UNSCHEDULED = "unscheduled"  # never scheduled, still learning


@dataclass(frozen=True, slots=True)
class ReviewQueueItem:
    kind: ReviewItemKind
    reason: ReviewReason
    # Vocabulary fields (kind=vocabulary)
    vocabulary_id: str | None
    text: str | None
    pinyin: str | None
    meaning: str | None
    # Character fields (kind=character)
    character: str | None
    # Shared
    status: str
    next_review_at: str | None
    successful_attempts: int
    failed_attempts: int


@dataclass(frozen=True, slots=True)
class GetReviewQueueResult:
    items: tuple[ReviewQueueItem, ...]
    due_vocabulary_count: int
    due_character_count: int
    unscheduled_vocabulary_count: int
    unscheduled_character_count: int
    total: int
    as_of: str


class GetReviewQueue:
    def __init__(
        self,
        vocabulary_knowledge_repo: VocabularyKnowledgeRepository,
        character_knowledge_repo: CharacterKnowledgeRepository,
        vocabulary_item_repo: VocabularyItemRepository,
    ) -> None:
        self._vocab_knowledge_repo = vocabulary_knowledge_repo
        self._char_knowledge_repo = character_knowledge_repo
        self._vocab_item_repo = vocabulary_item_repo

    async def execute(
        self,
        learner_id: LearnerId,
        *,
        as_of: datetime | None = None,
        limit: int = 20,
        include_vocabulary: bool = True,
        include_characters: bool = True,
        include_unscheduled: bool = True,
    ) -> GetReviewQueueResult:
        if limit < 1:
            raise ValueError("limit must be at least 1")

        now = as_of or datetime.now(UTC)
        queue: list[ReviewQueueItem] = []

        due_vocab_count = 0
        due_char_count = 0
        unscheduled_vocab_count = 0
        unscheduled_char_count = 0

        if include_vocabulary:
            due_vocab = await self._vocab_knowledge_repo.get_due_for_review(
                learner_id, now
            )
            due_vocab_count = len(due_vocab)
            due_ids = {str(k.vocabulary_id) for k in due_vocab}

            unscheduled_vocab: list[VocabularyKnowledge] = []
            if include_unscheduled:
                all_vocab = await self._vocab_knowledge_repo.get_all_for_learner(
                    learner_id
                )
                unscheduled_vocab = [
                    vk
                    for vk in all_vocab
                    if vk.next_review_at is None
                    and str(vk.vocabulary_id) not in due_ids
                    and vk.status in (KnowledgeStatus.NEW, KnowledgeStatus.LEARNING)
                ]
                unscheduled_vocab_count = len(unscheduled_vocab)

            ordered_vocab = list(due_vocab) + unscheduled_vocab
            vids = [vk.vocabulary_id for vk in ordered_vocab]
            items = await self._vocab_item_repo.get_many(vids)
            items_by_id = {str(i.id): i for i in items}

            for vk in ordered_vocab:
                item = items_by_id.get(str(vk.vocabulary_id))
                if item is None:
                    continue
                reason = (
                    ReviewReason.DUE
                    if vk.next_review_at is not None and vk.next_review_at <= now
                    else ReviewReason.UNSCHEDULED
                )
                queue.append(
                    ReviewQueueItem(
                        kind=ReviewItemKind.VOCABULARY,
                        reason=reason,
                        vocabulary_id=str(vk.vocabulary_id),
                        text=item.text,
                        pinyin=item.pinyin,
                        meaning=item.meaning,
                        character=None,
                        status=vk.status.value,
                        next_review_at=(
                            vk.next_review_at.isoformat() if vk.next_review_at else None
                        ),
                        successful_attempts=vk.successful_recalls,
                        failed_attempts=vk.failed_recalls,
                    )
                )

        if include_characters:
            due_chars = await self._char_knowledge_repo.get_due_for_review(
                learner_id, now
            )
            due_char_count = len(due_chars)
            due_symbols = {str(k.character) for k in due_chars}

            unscheduled_chars: list[CharacterKnowledge] = []
            if include_unscheduled:
                all_chars = await self._char_knowledge_repo.get_all_for_learner(
                    learner_id
                )
                unscheduled_chars = [
                    k
                    for k in all_chars
                    if k.next_review_at is None
                    and str(k.character) not in due_symbols
                    and k.status in (KnowledgeStatus.NEW, KnowledgeStatus.LEARNING)
                ]
                unscheduled_char_count = len(unscheduled_chars)

            ordered_chars = list(due_chars) + unscheduled_chars

            for k in ordered_chars:
                reason = (
                    ReviewReason.DUE
                    if k.next_review_at is not None and k.next_review_at <= now
                    else ReviewReason.UNSCHEDULED
                )
                queue.append(
                    ReviewQueueItem(
                        kind=ReviewItemKind.CHARACTER,
                        reason=reason,
                        vocabulary_id=None,
                        text=None,
                        pinyin=None,
                        meaning=None,
                        character=str(k.character),
                        status=k.status.value,
                        next_review_at=(
                            k.next_review_at.isoformat() if k.next_review_at else None
                        ),
                        successful_attempts=k.successful_recognitions,
                        failed_attempts=k.failed_recognitions,
                    )
                )

        # Due items first, then unscheduled; within each group keep insertion order
        queue.sort(key=lambda i: 0 if i.reason is ReviewReason.DUE else 1)
        limited = queue[:limit]

        return GetReviewQueueResult(
            items=tuple(limited),
            due_vocabulary_count=due_vocab_count,
            due_character_count=due_char_count,
            unscheduled_vocabulary_count=unscheduled_vocab_count,
            unscheduled_character_count=unscheduled_char_count,
            total=len(limited),
            as_of=now.isoformat(),
        )

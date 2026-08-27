"""
List vocabulary items for a learner with optional filters.

Returns dashboard rows combining VocabularyItem + VocabularyKnowledge + categories.
"""

from dataclasses import dataclass

from chinese_learning.domain.category.category import Category, CategoryId, CategoryType
from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.learner.vocabulary_knowledge import VocabularyKnowledge
from chinese_learning.domain.vocabulary.vocabulary_item import (
    VocabularyItem,
)
from chinese_learning.infrastructure.persistence.repositories.learner.vocabulary_knowledge_repository import (
    VocabularyKnowledgeRepository,
)
from chinese_learning.infrastructure.persistence.repositories.linguistic.category_assignment_repository import (
    CategoryAssignmentRepository,
)
from chinese_learning.infrastructure.persistence.repositories.linguistic.category_repository import (
    CategoryRepository,
)
from chinese_learning.infrastructure.persistence.repositories.linguistic.vocabulary_item_repository import (
    VocabularyItemRepository,
)


@dataclass(frozen=True, slots=True)
class CategorySummary:
    id: str
    name: str
    type: str
    hsk_level: int | None


@dataclass(frozen=True, slots=True)
class VocabularyDashboardRow:
    vocabulary_id: str
    text: str
    pinyin: str
    meaning: str
    status: str
    successful_recalls: int
    failed_recalls: int
    times_seen: int
    last_practised_at: str | None
    last_seen_at: str | None
    categories: tuple[CategorySummary, ...]
    hsk_level: int | None  # derived from assigned HSK category, if any


@dataclass(frozen=True, slots=True)
class ListVocabularyDashboardResult:
    items: tuple[VocabularyDashboardRow, ...]
    total: int
    status_counts: dict[
        str, int
    ]  # new/learning/known within current scope (after category/HSK/search; before status filter)


class ListVocabularyDashboard:
    """
    Build a filtered vocabulary dashboard for one learner.
    """

    def __init__(
        self,
        vocabulary_knowledge_repo: VocabularyKnowledgeRepository,
        vocabulary_item_repo: VocabularyItemRepository,
        category_repo: CategoryRepository,
        category_assignment_repo: CategoryAssignmentRepository,
    ) -> None:
        self._knowledge_repo = vocabulary_knowledge_repo
        self._item_repo = vocabulary_item_repo
        self._category_repo = category_repo
        self._assignment_repo = category_assignment_repo

    async def execute(
        self,
        learner_id: LearnerId,
        *,
        knowledge_status: KnowledgeStatus | None = None,
        category_id: CategoryId | None = None,
        hsk_level: int | None = None,
        search: str | None = None,
    ) -> ListVocabularyDashboardResult:
        """
        Build dashboard rows for one learner.

        Filter order:
        1. Load all knowledge for the learner
        2. Apply category / HSK / search scope filters
        3. Compute status_counts from that scoped set (so chips match the list)
        4. Apply knowledge_status filter only to the returned items
        """
        knowledge_list = await self._knowledge_repo.get_all_for_learner(learner_id)

        empty_counts = {"new": 0, "learning": 0, "known": 0}
        if not knowledge_list:
            return ListVocabularyDashboardResult(
                items=(),
                total=0,
                status_counts=empty_counts,
            )

        # Key knowledge by string id so lookups stay consistent across repos/mappers
        knowledge_by_vid: dict[str, VocabularyKnowledge] = {
            str(k.vocabulary_id): k for k in knowledge_list
        }
        vids = [k.vocabulary_id for k in knowledge_list]

        items = await self._item_repo.get_many(vids)
        items_by_id = {str(i.id): i for i in items}

        all_categories = await self._category_repo.get_all()
        categories_by_id = {str(c.id): c for c in all_categories}

        # Assignments per vocabulary id (string keys)
        assignments_by_vid: dict[str, list[CategoryId]] = {str(v): [] for v in vids}
        for vid in vids:
            for a in await self._assignment_repo.get_by_vocabulary(vid):
                assignments_by_vid[str(vid)].append(a.category_id)

        # Optional category filter
        if category_id is not None:
            allowed = {
                str(a.vocabulary_id)
                for a in await self._assignment_repo.get_by_category(category_id)
            }
            knowledge_by_vid = {
                vid_key: k
                for vid_key, k in knowledge_by_vid.items()
                if vid_key in allowed
            }

        # Optional HSK level filter (via assigned HSK categories)
        if hsk_level is not None:
            hsk_cat_ids = {
                str(c.id)
                for c in all_categories
                if c.type == CategoryType.HSK and c.hsk_level == hsk_level
            }
            knowledge_by_vid = {
                vid_key: k
                for vid_key, k in knowledge_by_vid.items()
                if hsk_cat_ids.intersection(
                    str(cid) for cid in assignments_by_vid.get(vid_key, [])
                )
            }

        # Optional text/pinyin/meaning search
        needle = search.strip().casefold() if search else None

        # Build scoped rows (before knowledge-status filter)
        scoped_rows: list[VocabularyDashboardRow] = []
        for vid_key, knowledge in knowledge_by_vid.items():
            item = items_by_id.get(vid_key)
            if item is None:
                continue
            if needle and not self._matches_search(item, needle):
                continue

            cat_summaries, hsk = self._categories_for(
                assignments_by_vid.get(vid_key, []),
                categories_by_id,
            )
            if hsk_level is not None and hsk != hsk_level:
                continue
            scoped_rows.append(self._to_row(item, knowledge, cat_summaries, hsk))

        # Chip counts reflect the scoped set (HSK / category / search), not the
        # full profile — so "All (5)" matches five visible words after an HSK filter.
        status_counts = {"new": 0, "learning": 0, "known": 0}
        for row in scoped_rows:
            if row.status in status_counts:
                status_counts[row.status] += 1

        # Status filter only narrows the list, not the chip totals
        if knowledge_status is not None:
            wanted = knowledge_status.value
            rows = [r for r in scoped_rows if r.status == wanted]
        else:
            rows = scoped_rows

        rows.sort(key=lambda r: r.text)

        return ListVocabularyDashboardResult(
            items=tuple(rows),
            total=len(rows),
            status_counts=status_counts,
        )

    @staticmethod
    def _matches_search(item: VocabularyItem, needle: str) -> bool:
        return (
            needle in item.text.casefold()
            or needle in item.pinyin.casefold()
            or needle in item.meaning.casefold()
        )

    @staticmethod
    def _categories_for(
        category_ids: list[CategoryId],
        categories_by_id: dict[str, Category],
    ) -> tuple[tuple[CategorySummary, ...], int | None]:
        summaries: list[CategorySummary] = []
        hsk_level: int | None = None
        for cid in category_ids:
            cat = categories_by_id.get(str(cid))
            if cat is None:
                continue
            summaries.append(
                CategorySummary(
                    id=str(cat.id),
                    name=cat.name,
                    type=cat.type.value,
                    hsk_level=cat.hsk_level,
                )
            )
            if cat.type == CategoryType.HSK and cat.hsk_level is not None:
                # Prefer the lowest HSK level if multiple somehow assigned
                if hsk_level is None or cat.hsk_level < hsk_level:
                    hsk_level = cat.hsk_level
        summaries.sort(key=lambda s: (s.type, s.name))
        return tuple(summaries), hsk_level

    @staticmethod
    def _to_row(
        item: VocabularyItem,
        knowledge: VocabularyKnowledge,
        categories: tuple[CategorySummary, ...],
        hsk_level: int | None,
    ) -> VocabularyDashboardRow:
        return VocabularyDashboardRow(
            vocabulary_id=str(item.id),
            text=item.text,
            pinyin=item.pinyin,
            meaning=item.meaning,
            status=knowledge.status.value,
            successful_recalls=knowledge.successful_recalls,
            failed_recalls=knowledge.failed_recalls,
            times_seen=knowledge.times_seen,
            last_practised_at=(
                knowledge.last_practised_at.isoformat()
                if knowledge.last_practised_at
                else None
            ),
            last_seen_at=(
                knowledge.last_seen_at.isoformat() if knowledge.last_seen_at else None
            ),
            categories=categories,
            hsk_level=hsk_level,
        )

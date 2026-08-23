from collections.abc import Callable

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.application.services.hsk_lookup_service import HSKLookupService
from chinese_learning.application.use_cases.assign_hsk_category import AssignHSKCategory
from chinese_learning.domain.category.category import Category, CategoryId, CategoryType
from chinese_learning.domain.category.category_assignment import CategoryAssignment
from chinese_learning.domain.vocabulary.vocabulary_item import (
    VocabularyId,
    VocabularyItem,
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

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def hsk_lookup() -> HSKLookupService:
    """In-memory lookup – no files needed."""
    return HSKLookupService(
        {
            "爱": 1,
            "爸爸": 2,
            "安静": 3,
            "尴尬": 7,
        }
    )


@pytest.fixture
async def seeded_categories(
    db_session: AsyncSession, make_category: Callable[..., Category]
) -> dict[str, Category]:
    """Seed the HSK + Uncategorised categories the use-case expects."""
    repo = CategoryRepository(db_session)

    cats = {
        "hsk1": make_category(
            id=CategoryId("a1000000-0000-4000-8000-000000000001"),
            name="HSK 1",
            type=CategoryType.HSK,
            hsk_level=1,
            sort_order=1,
        ),
        "hsk2": make_category(
            id=CategoryId("a1000000-0000-4000-8000-000000000002"),
            name="HSK 2",
            type=CategoryType.HSK,
            hsk_level=2,
            sort_order=2,
        ),
        "hsk3": make_category(
            id=CategoryId("a1000000-0000-4000-8000-000000000003"),
            name="HSK 3",
            type=CategoryType.HSK,
            hsk_level=3,
            sort_order=3,
        ),
        "hsk7": make_category(
            id=CategoryId("a1000000-0000-4000-8000-000000000007"),
            name="HSK 7-9",
            type=CategoryType.HSK,
            hsk_level=7,
            sort_order=7,
        ),
        "uncategorised": make_category(
            id=CategoryId("c1000000-0000-4000-8000-000000000001"),
            name="Uncategorised",
            type=CategoryType.SYSTEM,
            hsk_level=None,
            sort_order=999,
        ),
        "food": make_category(
            name="Food",
            type=CategoryType.TOPIC,
            hsk_level=None,
        ),
    }
    await repo.save_many(list(cats.values()))
    await db_session.commit()
    return cats


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_assigns_correct_hsk_level(
    db_session: AsyncSession,
    hsk_lookup: HSKLookupService,
    seeded_categories: dict[str, Category],
    make_vocabulary_item: Callable[..., VocabularyItem],
):
    vocab_repo = VocabularyItemRepository(db_session)
    category_repo = CategoryRepository(db_session)
    assignment_repo = CategoryAssignmentRepository(db_session)
    use_case = AssignHSKCategory(hsk_lookup, category_repo, assignment_repo)

    items = [
        make_vocabulary_item(id=VocabularyId("1"), text="爱"),  # → HSK 1
        make_vocabulary_item(id=VocabularyId("2"), text="爸爸"),  # → HSK 2
        make_vocabulary_item(id=VocabularyId("3"), text="安静"),  # → HSK 3
        make_vocabulary_item(id=VocabularyId("4"), text="尴尬"),  # → HSK 7-9
    ]

    for item in items:
        await vocab_repo.save(item)
    await db_session.flush()

    created = await use_case.execute(items)
    await db_session.commit()

    assert created == 4

    expected = [
        seeded_categories["hsk1"],
        seeded_categories["hsk2"],
        seeded_categories["hsk3"],
        seeded_categories["hsk7"],
    ]

    for item, expected_cat in zip(items, expected, strict=True):
        assignments = await assignment_repo.get_by_vocabulary(item.id)
        assert len(assignments) == 1
        assert assignments[0].category_id == expected_cat.id


@pytest.mark.asyncio
async def test_assigns_uncategorised_when_unknown(
    db_session: AsyncSession,
    hsk_lookup: HSKLookupService,
    seeded_categories: dict[str, Category],
    make_vocabulary_item: Callable[..., VocabularyItem],
):
    vocab_repo = VocabularyItemRepository(db_session)
    category_repo = CategoryRepository(db_session)
    assignment_repo = CategoryAssignmentRepository(db_session)
    use_case = AssignHSKCategory(hsk_lookup, category_repo, assignment_repo)

    item = make_vocabulary_item(text="完全不在HSK里的词")
    await vocab_repo.save(item)

    created = await use_case.execute([item])
    await db_session.commit()

    assert created == 1
    assignments = await assignment_repo.get_by_vocabulary(item.id)
    assert len(assignments) == 1
    assert assignments[0].category_id == seeded_categories["uncategorised"].id


@pytest.mark.asyncio
async def test_does_not_overwrite_existing_hsk_assignment(
    db_session: AsyncSession,
    hsk_lookup: HSKLookupService,
    seeded_categories: dict[str, Category],
    make_vocabulary_item: Callable[..., VocabularyItem],
):
    vocab_repo = VocabularyItemRepository(db_session)
    category_repo = CategoryRepository(db_session)
    assignment_repo = CategoryAssignmentRepository(db_session)
    use_case = AssignHSKCategory(hsk_lookup, category_repo, assignment_repo)

    item = make_vocabulary_item(text="爱")  # would be HSK 1
    await vocab_repo.save(item)

    # Pre-assign a different HSK category
    await assignment_repo.save(
        CategoryAssignment(
            category_id=seeded_categories["hsk3"].id,
            vocabulary_id=item.id,
        )
    )
    await db_session.commit()

    created = await use_case.execute([item])
    await db_session.commit()

    assert created == 0
    assignments = await assignment_repo.get_by_vocabulary(item.id)
    assert len(assignments) == 1
    assert assignments[0].category_id == seeded_categories["hsk3"].id


@pytest.mark.asyncio
async def test_does_not_touch_topic_categories(
    db_session: AsyncSession,
    hsk_lookup: HSKLookupService,
    seeded_categories: dict[str, Category],
    make_vocabulary_item: Callable[..., VocabularyItem],
):
    vocab_repo = VocabularyItemRepository(db_session)
    category_repo = CategoryRepository(db_session)
    assignment_repo = CategoryAssignmentRepository(db_session)
    use_case = AssignHSKCategory(hsk_lookup, category_repo, assignment_repo)

    item = make_vocabulary_item(text="爱")
    await vocab_repo.save(item)

    # Already has a topic category
    await assignment_repo.save(
        CategoryAssignment(
            category_id=seeded_categories["food"].id,
            vocabulary_id=item.id,
        )
    )
    await db_session.commit()

    created = await use_case.execute([item])
    await db_session.commit()

    assert created == 1  # still adds the HSK category
    assignments = await assignment_repo.get_by_vocabulary(item.id)
    category_ids = {a.category_id for a in assignments}

    assert seeded_categories["food"].id in category_ids
    assert seeded_categories["hsk1"].id in category_ids
    assert len(assignments) == 2


@pytest.mark.asyncio
async def test_empty_list_is_noop(
    db_session: AsyncSession,
    hsk_lookup: HSKLookupService,
):
    category_repo = CategoryRepository(db_session)
    assignment_repo = CategoryAssignmentRepository(db_session)
    use_case = AssignHSKCategory(hsk_lookup, category_repo, assignment_repo)

    created = await use_case.execute([])
    assert created == 0


@pytest.mark.asyncio
async def test_skips_when_already_has_system_category(
    db_session: AsyncSession,
    hsk_lookup: HSKLookupService,
    seeded_categories: dict[str, Category],
    make_vocabulary_item: Callable[..., VocabularyItem],
):
    voacb_repo = VocabularyItemRepository(db_session)
    category_repo = CategoryRepository(db_session)
    assignment_repo = CategoryAssignmentRepository(db_session)
    use_case = AssignHSKCategory(hsk_lookup, category_repo, assignment_repo)

    item = make_vocabulary_item(text="爱")
    await voacb_repo.save(item)

    await assignment_repo.save(
        CategoryAssignment(
            category_id=seeded_categories["uncategorised"].id,
            vocabulary_id=item.id,
        )
    )
    await db_session.commit()

    created = await use_case.execute([item])
    assert created == 0

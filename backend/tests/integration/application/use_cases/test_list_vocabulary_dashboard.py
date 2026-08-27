"""Integration tests for ListVocabularyDashboard against real Postgres."""

from collections.abc import Callable
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.application.use_cases.list_vocabulary_dashboard import (
    ListVocabularyDashboard,
)
from chinese_learning.domain.category.category import Category, CategoryId, CategoryType
from chinese_learning.domain.category.category_assignment import CategoryAssignment
from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.learner.vocabulary_knowledge import VocabularyKnowledge
from chinese_learning.domain.vocabulary.vocabulary_item import (
    VocabularyId,
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


def _use_case(session: AsyncSession) -> ListVocabularyDashboard:
    return ListVocabularyDashboard(
        vocabulary_knowledge_repo=VocabularyKnowledgeRepository(session),
        vocabulary_item_repo=VocabularyItemRepository(session),
        category_repo=CategoryRepository(session),
        category_assignment_repo=CategoryAssignmentRepository(session),
    )


@pytest.fixture
async def dashboard_seed(
    db_session: AsyncSession,
    learner_id: LearnerId,
    make_vocabulary_item: Callable[..., VocabularyItem],
    make_vocabulary_knowledge: Callable[..., VocabularyKnowledge],
    make_category: Callable[..., Category],
) -> dict[str, Any]:
    """
    Seed three vocab items with mixed statuses and HSK assignments:

    - 一 (HSK 1, NEW)
    - 两 (HSK 2, LEARNING)
    - 你好 (HSK 1, KNOWN)  — meaning "hello" for search tests
    """
    item_repo = VocabularyItemRepository(db_session)
    knowledge_repo = VocabularyKnowledgeRepository(db_session)
    cat_repo = CategoryRepository(db_session)
    assign_repo = CategoryAssignmentRepository(db_session)

    hsk1 = make_category(
        id=CategoryId(str(uuid4())),
        name="HSK 1",
        type=CategoryType.HSK,
        hsk_level=1,
        sort_order=1,
    )
    hsk2 = make_category(
        id=CategoryId(str(uuid4())),
        name="HSK 2",
        type=CategoryType.HSK,
        hsk_level=2,
        sort_order=2,
    )
    topic = make_category(
        id=CategoryId(str(uuid4())),
        name="Greetings",
        type=CategoryType.TOPIC,
        hsk_level=None,
        sort_order=10,
    )

    v1 = make_vocabulary_item(
        id=VocabularyId(str(uuid4())), text="一", pinyin="yī", meaning="one"
    )
    v2 = make_vocabulary_item(
        id=VocabularyId(str(uuid4())), text="两", pinyin="liǎng", meaning="two"
    )
    v3 = make_vocabulary_item(
        id=VocabularyId(str(uuid4())), text="你好", pinyin="nǐhǎo", meaning="hello"
    )

    await cat_repo.save_many([hsk1, hsk2, topic])
    await item_repo.save_many([v1, v2, v3])
    await knowledge_repo.save_many(
        [
            make_vocabulary_knowledge(
                learner_id=learner_id,
                vocabulary_id=v1.id,
                status=KnowledgeStatus.NEW,
            ),
            make_vocabulary_knowledge(
                learner_id=learner_id,
                vocabulary_id=v2.id,
                status=KnowledgeStatus.LEARNING,
            ),
            make_vocabulary_knowledge(
                learner_id=learner_id,
                vocabulary_id=v3.id,
                status=KnowledgeStatus.KNOWN,
            ),
        ]
    )
    await assign_repo.save_many(
        [
            CategoryAssignment(category_id=hsk1.id, vocabulary_id=v1.id),
            CategoryAssignment(category_id=hsk2.id, vocabulary_id=v2.id),
            CategoryAssignment(category_id=hsk1.id, vocabulary_id=v3.id),
            CategoryAssignment(category_id=topic.id, vocabulary_id=v3.id),
        ]
    )
    await db_session.commit()

    return {
        "hsk1": hsk1,
        "hsk2": hsk2,
        "topic": topic,
        "v1": v1,
        "v2": v2,
        "v3": v3,
    }


@pytest.mark.asyncio
async def test_lists_all_items_with_status_counts(
    db_session: AsyncSession, learner_id: LearnerId, dashboard_seed: dict[str, Any]
) -> None:
    result = await _use_case(db_session).execute(learner_id)
    print(result)

    assert result.total == 3
    assert result.status_counts == {"new": 1, "learning": 1, "known": 1}
    texts = {row.text for row in result.items}
    assert texts == {"一", "两", "你好"}


@pytest.mark.asyncio
async def test_hsk_filter_narrows_list_and_status_counts(
    db_session: AsyncSession, learner_id: LearnerId, dashboard_seed: dict[str, Any]
) -> None:
    result = await _use_case(db_session).execute(learner_id, hsk_level=1)

    assert result.total == 2
    assert {row.text for row in result.items} == {"一", "你好"}
    # Scoped counts: one NEW, one KNOWN under HSK 1
    assert result.status_counts == {"new": 1, "learning": 0, "known": 1}
    assert all(row.hsk_level == 1 for row in result.items)


@pytest.mark.asyncio
async def test_hsk_filter_combined_with_status(
    db_session: AsyncSession, learner_id: LearnerId, dashboard_seed: dict[str, Any]
) -> None:
    result = await _use_case(db_session).execute(
        learner_id,
        hsk_level=1,
        knowledge_status=KnowledgeStatus.KNOWN,
    )

    # List narrowed to KNOWN within HSK 1
    assert result.total == 1
    assert result.items[0].text == "你好"
    # Chips still reflect full HSK 1 scope (not the status-filtered subset)
    assert result.status_counts == {"new": 1, "learning": 0, "known": 1}


@pytest.mark.asyncio
async def test_category_filter(
    db_session: AsyncSession,
    learner_id: LearnerId,
    dashboard_seed: dict[str, Any],
) -> None:
    topic = dashboard_seed["topic"]
    result = await _use_case(db_session).execute(learner_id, category_id=topic.id)

    assert result.total == 1
    assert result.items[0].text == "你好"
    assert result.status_counts == {"new": 0, "learning": 0, "known": 1}


@pytest.mark.asyncio
async def test_search_filter(
    db_session: AsyncSession, learner_id: LearnerId, dashboard_seed: dict[str, Any]
) -> None:
    result = await _use_case(db_session).execute(learner_id, search="hello")

    assert result.total == 1
    assert result.items[0].text == "你好"
    assert result.status_counts == {"new": 0, "learning": 0, "known": 1}


@pytest.mark.asyncio
async def test_empty_for_other_learner(
    db_session: AsyncSession,
    other_learner_id: LearnerId,
) -> None:
    result = await _use_case(db_session).execute(other_learner_id)

    assert result.total == 0
    assert result.items == ()
    assert result.status_counts == {"new": 0, "learning": 0, "known": 0}

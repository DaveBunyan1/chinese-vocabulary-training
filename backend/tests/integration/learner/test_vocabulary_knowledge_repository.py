from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.learner.vocabulary_knowledge import VocabularyKnowledge
from chinese_learning.domain.vocabulary.vocabulary_item import VocabularyId
from chinese_learning.infrastructure.persistence.repositories.learner.vocabulary_knowledge_repository import (
    VocabularyKnowledgeRepository,
)


@pytest.mark.asyncio
async def test_vocabulary_get_returns_none_when_missing(
    db_session: AsyncSession, learner_id: LearnerId
):
    repo = VocabularyKnowledgeRepository(db_session)
    result = await repo.get(learner_id, VocabularyId(str(uuid4())))
    assert result is None


@pytest.mark.asyncio
async def test_vocabulary_save_and_get(
    db_session: AsyncSession,
    learner_id: LearnerId,
    make_vocabulary_knowledge: Callable[..., VocabularyKnowledge],
):
    repo = VocabularyKnowledgeRepository(db_session)
    knowledge = make_vocabulary_knowledge(
        learner_id=learner_id, times_seen=1, ease_factor=2.5
    )

    await repo.save(knowledge)
    await db_session.commit()

    loaded = await repo.get(learner_id, knowledge.vocabulary_id)
    assert loaded is not None
    assert loaded.learner_id == learner_id
    assert loaded.vocabulary_id == knowledge.vocabulary_id
    assert loaded.times_seen == 1
    assert loaded.ease_factor == 2.5


@pytest.mark.asyncio
async def test_vocabulary_save_updates_existing(
    db_session: AsyncSession,
    learner_id: LearnerId,
    make_vocabulary_knowledge: Callable[..., VocabularyKnowledge],
):
    repo = VocabularyKnowledgeRepository(db_session)
    original = make_vocabulary_knowledge(learner_id=learner_id, times_seen=1)
    await repo.save(original)
    await db_session.commit()

    updated = make_vocabulary_knowledge(
        learner_id=learner_id,
        vocabulary_id=str(original.vocabulary_id),
        status=KnowledgeStatus.LEARNING,
        times_seen=8,
    )
    await repo.save(updated)
    await db_session.commit()

    loaded = await repo.get(learner_id, original.vocabulary_id)
    assert loaded is not None
    assert loaded.status == KnowledgeStatus.LEARNING
    assert loaded.times_seen == 8


@pytest.mark.asyncio
async def test_vocabulary_save_many(
    db_session: AsyncSession,
    learner_id: LearnerId,
    make_vocabulary_knowledge: Callable[..., VocabularyKnowledge],
):
    repo = VocabularyKnowledgeRepository(db_session)
    items = [
        make_vocabulary_knowledge(
            learner_id=learner_id, vocabulary_id=VocabularyId(f"vocab-{i}")
        )
        for i in range(3)
    ]
    await repo.save_many(items)

    all_items = await repo.get_all_for_learner(learner_id)
    assert len(all_items) == 3


@pytest.mark.asyncio
async def test_vocabulary_get_many(
    db_session: AsyncSession,
    learner_id: LearnerId,
    make_vocabulary_knowledge: Callable[..., VocabularyKnowledge],
):
    repo = VocabularyKnowledgeRepository(db_session)
    k1 = make_vocabulary_knowledge(
        learner_id=learner_id, vocabulary_id=VocabularyId("vocab-1")
    )
    k2 = make_vocabulary_knowledge(
        learner_id=learner_id, vocabulary_id=VocabularyId("vocab-2")
    )
    await repo.save_many([k1, k2])
    await db_session.commit()

    results = await repo.get_many(
        learner_id, [k1.vocabulary_id, VocabularyId(str(uuid4()))]
    )
    assert len(results) == 1
    assert results[0].vocabulary_id == k1.vocabulary_id


@pytest.mark.asyncio
async def test_vocabulary_get_due_for_review(
    db_session: AsyncSession,
    learner_id: LearnerId,
    make_vocabulary_knowledge: Callable[..., VocabularyKnowledge],
):
    repo = VocabularyKnowledgeRepository(db_session)
    now = datetime.now(UTC)

    due = make_vocabulary_knowledge(
        learner_id=learner_id,
        vocabulary_id=VocabularyId("due-vocab"),
        next_review_at=now - timedelta(minutes=30),
    )
    future = make_vocabulary_knowledge(
        learner_id=learner_id, next_review_at=now + timedelta(days=2)
    )
    await repo.save_many([due, future])
    await db_session.commit()

    results = await repo.get_due_for_review(learner_id, as_of=now)
    assert len(results) == 1
    assert results[0].vocabulary_id == due.vocabulary_id


@pytest.mark.asyncio
async def test_vocabulary_count_by_status(
    db_session: AsyncSession,
    learner_id: LearnerId,
    make_vocabulary_knowledge: Callable[..., VocabularyKnowledge],
):
    repo = VocabularyKnowledgeRepository(db_session)
    await repo.save_many(
        [
            make_vocabulary_knowledge(
                learner_id=learner_id,
                vocabulary_id=VocabularyId("vocab-1"),
                status=KnowledgeStatus.NEW,
            ),
            make_vocabulary_knowledge(
                learner_id=learner_id,
                vocabulary_id=VocabularyId("vocab-2"),
                status=KnowledgeStatus.NEW,
            ),
            make_vocabulary_knowledge(
                learner_id=learner_id,
                vocabulary_id=VocabularyId("vocab-3"),
                status=KnowledgeStatus.KNOWN,
            ),
        ]
    )
    await db_session.commit()

    counts = await repo.count_by_status(learner_id)
    assert counts.get(KnowledgeStatus.NEW) == 2
    assert counts.get(KnowledgeStatus.KNOWN) == 1


@pytest.mark.asyncio
async def test_vocabulary_exists(
    db_session: AsyncSession,
    learner_id: LearnerId,
    make_vocabulary_knowledge: Callable[..., VocabularyKnowledge],
):
    repo = VocabularyKnowledgeRepository(db_session)
    knowledge = make_vocabulary_knowledge(learner_id=learner_id)
    await repo.save(knowledge)
    await db_session.commit()

    assert await repo.exists(learner_id, knowledge.vocabulary_id) is True
    assert await repo.exists(learner_id, VocabularyId(str(uuid4()))) is False


@pytest.mark.asyncio
async def test_vocabulary_get_all_for_learner(
    db_session: AsyncSession,
    learner_id: LearnerId,
    other_learner_id: LearnerId,
    make_vocabulary_knowledge: Callable[..., VocabularyKnowledge],
):
    repo = VocabularyKnowledgeRepository(db_session)
    await repo.save_many(
        [
            make_vocabulary_knowledge(
                learner_id=learner_id,
                vocabulary_id=VocabularyId("v-a"),
                status=KnowledgeStatus.NEW,
            ),
            make_vocabulary_knowledge(
                learner_id=learner_id,
                vocabulary_id=VocabularyId("v-b"),
                status=KnowledgeStatus.KNOWN,
            ),
            make_vocabulary_knowledge(
                learner_id=other_learner_id,
                vocabulary_id=VocabularyId("v-c"),
                status=KnowledgeStatus.LEARNING,
            ),
        ]
    )
    await db_session.commit()

    results = await repo.get_all_for_learner(learner_id)
    ids = {str(k.vocabulary_id) for k in results}
    assert ids == {"v-a", "v-b"}


@pytest.mark.asyncio
async def test_vocabulary_get_by_status(
    db_session: AsyncSession,
    learner_id: LearnerId,
    make_vocabulary_knowledge: Callable[..., VocabularyKnowledge],
):
    repo = VocabularyKnowledgeRepository(db_session)
    await repo.save_many(
        [
            make_vocabulary_knowledge(
                learner_id=learner_id,
                vocabulary_id=VocabularyId("v-new"),
                status=KnowledgeStatus.NEW,
            ),
            make_vocabulary_knowledge(
                learner_id=learner_id,
                vocabulary_id=VocabularyId("v-known"),
                status=KnowledgeStatus.KNOWN,
            ),
        ]
    )
    await db_session.commit()

    new_only = await repo.get_by_status(learner_id, KnowledgeStatus.NEW.value)
    assert len(new_only) == 1
    assert new_only[0].status is KnowledgeStatus.NEW
    assert str(new_only[0].vocabulary_id) == "v-new"

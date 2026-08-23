from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.character_knowledge import CharacterKnowledge
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.text_analysis.character import Character
from chinese_learning.infrastructure.persistence.repositories.learner.character_knowledge_repository import (
    CharacterKnowledgeRepository,
)


@pytest.mark.asyncio
async def test_update_existing_character_knowledge(db_session: AsyncSession):
    repo = CharacterKnowledgeRepository(db_session)
    learner_id = LearnerId("user_123")
    char = Character("山")
    now = datetime.now(UTC)

    # 1. Create and save initial record
    initial = CharacterKnowledge(
        learner_id=learner_id,
        character=char,
        status=KnowledgeStatus.NEW,
    )
    await repo.save(initial)
    await db_session.commit()

    # 2. Simulate learning event using immutable helper method
    updated_domain = initial.with_success(at=now)
    await repo.save(updated_domain)
    await db_session.commit()

    # 3. Fetch from DB and verify update was persisted
    retrieved = await repo.get(learner_id, char)
    assert retrieved is not None
    assert retrieved.status == KnowledgeStatus.LEARNING
    assert retrieved.successful_recognitions == 1
    assert retrieved.last_practised_at == now


@pytest.mark.asyncio
async def test_character_get_returns_none_when_missing(
    db_session: AsyncSession, learner_id: LearnerId
):
    repo = CharacterKnowledgeRepository(db_session)
    result = await repo.get(learner_id, Character("你"))
    assert result is None


@pytest.mark.asyncio
async def test_character_save_and_get(
    db_session: AsyncSession,
    learner_id: LearnerId,
    make_character_knowledge: Callable[..., CharacterKnowledge],
):
    repo = CharacterKnowledgeRepository(db_session)
    knowledge = make_character_knowledge(
        learner_id=learner_id, character="好", times_seen=1
    )

    await repo.save(knowledge)
    await db_session.commit()

    loaded = await repo.get(learner_id, Character("好"))
    assert loaded is not None
    assert loaded.learner_id == learner_id
    assert str(loaded.character) == "好"
    assert loaded.status == KnowledgeStatus.NEW
    assert loaded.times_seen == 1


@pytest.mark.asyncio
async def test_character_save_updates_existing(
    db_session: AsyncSession,
    learner_id: LearnerId,
    make_character_knowledge: Callable[..., CharacterKnowledge],
):
    repo = CharacterKnowledgeRepository(db_session)
    original = make_character_knowledge(
        learner_id=learner_id, character="学", times_seen=1
    )
    await repo.save(original)
    await db_session.commit()

    updated = make_character_knowledge(
        learner_id=learner_id,
        character="学",
        status=KnowledgeStatus.LEARNING,
        times_seen=5,
    )
    await repo.save(updated)
    await db_session.commit()

    loaded = await repo.get(learner_id, Character("学"))
    assert loaded is not None
    assert loaded.status == KnowledgeStatus.LEARNING
    assert loaded.times_seen == 5


@pytest.mark.asyncio
async def test_character_save_many_empty_list_is_noop(db_session: AsyncSession):
    repo = CharacterKnowledgeRepository(db_session)
    await repo.save_many([])  # should not raise
    await db_session.commit()


@pytest.mark.asyncio
async def test_character_save_many_inserts_and_updates(
    db_session: AsyncSession,
    learner_id: LearnerId,
    make_character_knowledge: Callable[..., CharacterKnowledge],
):
    repo = CharacterKnowledgeRepository(db_session)

    k1 = make_character_knowledge(learner_id=learner_id, character="一")
    k2 = make_character_knowledge(learner_id=learner_id, character="二", times_seen=1)
    await repo.save_many([k1, k2])
    await db_session.commit()

    # Update one, insert another
    k1_updated = make_character_knowledge(
        learner_id=learner_id, character="一", times_seen=10
    )
    k3 = make_character_knowledge(learner_id=learner_id, character="三", times_seen=1)
    await repo.save_many([k1_updated, k3])
    await db_session.commit()

    all_items = await repo.get_all_for_learner(learner_id)
    assert len(all_items) == 3
    by_char = {str(k.character): k for k in all_items}
    assert by_char["一"].times_seen == 10
    assert by_char["二"].times_seen == 1
    assert by_char["三"].times_seen == 1


@pytest.mark.asyncio
async def test_character_get_many(
    db_session: AsyncSession,
    learner_id: LearnerId,
    make_character_knowledge: Callable[..., CharacterKnowledge],
):
    repo = CharacterKnowledgeRepository(db_session)
    await repo.save_many(
        [
            make_character_knowledge(learner_id=learner_id, character="中"),
            make_character_knowledge(learner_id=learner_id, character="国"),
            make_character_knowledge(learner_id=learner_id, character="人"),
        ]
    )
    await db_session.commit()

    results = await repo.get_many(
        learner_id, [Character("中"), Character("人"), Character("在")]
    )
    assert len(results) == 2
    chars = {str(r.character) for r in results}
    assert chars == {"中", "人"}


@pytest.mark.asyncio
async def test_character_get_many_empty(
    db_session: AsyncSession, learner_id: LearnerId
):
    repo = CharacterKnowledgeRepository(db_session)
    assert await repo.get_many(learner_id, []) == []


@pytest.mark.asyncio
async def test_character_get_all_for_learner_isolates_learners(
    db_session: AsyncSession,
    learner_id: LearnerId,
    other_learner_id: LearnerId,
    make_character_knowledge: Callable[..., CharacterKnowledge],
):
    repo = CharacterKnowledgeRepository(db_session)
    await repo.save(make_character_knowledge(learner_id=learner_id, character="我"))
    await repo.save(
        make_character_knowledge(learner_id=other_learner_id, character="你")
    )
    await db_session.commit()

    mine = await repo.get_all_for_learner(learner_id)
    assert len(mine) == 1
    assert str(mine[0].character) == "我"


@pytest.mark.asyncio
async def test_character_get_by_status(
    db_session: AsyncSession,
    learner_id: LearnerId,
    make_character_knowledge: Callable[..., CharacterKnowledge],
):
    repo = CharacterKnowledgeRepository(db_session)
    await repo.save_many(
        [
            make_character_knowledge(
                learner_id=learner_id, character="新", status=KnowledgeStatus.NEW
            ),
            make_character_knowledge(
                learner_id=learner_id, character="学", status=KnowledgeStatus.LEARNING
            ),
            make_character_knowledge(
                learner_id=learner_id, character="习", status=KnowledgeStatus.LEARNING
            ),
        ]
    )
    await db_session.commit()

    learning = await repo.get_by_status(learner_id, KnowledgeStatus.LEARNING)
    assert len(learning) == 2
    assert all(k.status == KnowledgeStatus.LEARNING for k in learning)


@pytest.mark.asyncio
async def test_character_get_due_for_review(
    db_session: AsyncSession,
    learner_id: LearnerId,
    make_character_knowledge: Callable[..., CharacterKnowledge],
):
    repo = CharacterKnowledgeRepository(db_session)
    now = datetime.now(UTC)

    due = make_character_knowledge(
        learner_id=learner_id, character="到", next_review_at=now - timedelta(hours=1)
    )
    not_due = make_character_knowledge(
        learner_id=learner_id, character="期", next_review_at=now + timedelta(days=3)
    )
    await repo.save_many([due, not_due])
    await db_session.commit()

    results = await repo.get_due_for_review(learner_id, as_of=now)
    assert len(results) == 1
    assert str(results[0].character) == "到"


@pytest.mark.asyncio
async def test_character_count_by_status(
    db_session: AsyncSession,
    learner_id: LearnerId,
    make_character_knowledge: Callable[..., CharacterKnowledge],
):
    repo = CharacterKnowledgeRepository(db_session)
    await repo.save_many(
        [
            make_character_knowledge(
                learner_id=learner_id, character="你", status=KnowledgeStatus.NEW
            ),
            make_character_knowledge(
                learner_id=learner_id, character="我", status=KnowledgeStatus.NEW
            ),
            make_character_knowledge(
                learner_id=learner_id, character="今", status=KnowledgeStatus.KNOWN
            ),
        ]
    )
    await db_session.commit()

    counts = await repo.count_by_status(learner_id)
    assert counts[KnowledgeStatus.NEW] == 2
    assert counts[KnowledgeStatus.KNOWN] == 1


@pytest.mark.asyncio
async def test_character_exists(
    db_session: AsyncSession,
    learner_id: LearnerId,
    make_character_knowledge: Callable[..., CharacterKnowledge],
):
    repo = CharacterKnowledgeRepository(db_session)
    await repo.save(make_character_knowledge(learner_id=learner_id, character="存"))
    await db_session.commit()

    assert await repo.exists(learner_id, Character("存")) is True
    assert await repo.exists(learner_id, Character("不")) is False

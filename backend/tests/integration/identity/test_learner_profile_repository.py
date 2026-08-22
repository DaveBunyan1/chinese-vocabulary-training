from collections.abc import Callable
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.domain.identity.learner import LearnerId, LearnerProfile
from chinese_learning.domain.identity.user import User
from chinese_learning.infrastructure.persistence.repositories.identity.learner_profile_repository import (
    LearnerProfileRepository,
)
from chinese_learning.infrastructure.persistence.repositories.identity.user_repository import (
    UserRepository,
)


@pytest.mark.asyncio
async def test_learner_profile_get_returns_none_when_missing(db_session: AsyncSession):
    repo = LearnerProfileRepository(db_session)
    assert await repo.get(LearnerId(str(uuid4()))) is None


@pytest.mark.asyncio
async def test_learner_profile_save_and_get(
    db_session: AsyncSession,
    make_user: Callable[..., User],
    make_learner_profile: Callable[..., LearnerProfile],
):
    user_repo = UserRepository(db_session)
    profile_repo = LearnerProfileRepository(db_session)

    user = make_user()
    await user_repo.save(user)
    await db_session.commit()

    profile = make_learner_profile(user_id=user.id)
    await profile_repo.save(profile)
    await db_session.commit()

    loaded = await profile_repo.get(profile.id)
    assert loaded is not None
    assert loaded.id == profile.id
    assert loaded.user_id == user.id
    assert loaded.language == "zh-CN"
    assert loaded.display_name == "Chinese Learner"


@pytest.mark.asyncio
async def test_learner_profile_get_by_user(
    db_session: AsyncSession,
    make_user: Callable[..., User],
    make_learner_profile: Callable[..., LearnerProfile],
):
    user_repo = UserRepository(db_session)
    profile_repo = LearnerProfileRepository(db_session)

    user = make_user()
    other_user = make_user(email="other@example.com")
    await user_repo.save_many([user, other_user])
    await db_session.commit()

    p1 = make_learner_profile(
        user_id=user.id, language="zh-CN", display_name="Mandarin"
    )
    p2 = make_learner_profile(
        user_id=user.id, language="zh-TW", display_name="Traditional"
    )
    p3 = make_learner_profile(user_id=other_user.id, language="zh-CN")

    await profile_repo.save_many([p1, p2, p3])
    await db_session.commit()

    results = await profile_repo.get_by_user(user.id)
    assert len(results) == 2
    languages = {p.language for p in results}
    assert languages == {"zh-CN", "zh-TW"}


@pytest.mark.asyncio
async def test_learner_profile_save_updates_existing(
    db_session: AsyncSession,
    make_user: Callable[..., User],
    make_learner_profile: Callable[..., LearnerProfile],
):
    user_repo = UserRepository(db_session)
    profile_repo = LearnerProfileRepository(db_session)

    user = make_user()
    await user_repo.save(user)
    await db_session.commit()

    profile = make_learner_profile(user_id=user.id, display_name="Old Name")
    await profile_repo.save(profile)
    await db_session.commit()

    updated = make_learner_profile(
        id=profile.id,
        user_id=user.id,
        language=profile.language,
        display_name="New Name",
    )
    await profile_repo.save(updated)
    await db_session.commit()

    loaded = await profile_repo.get(profile.id)
    assert loaded is not None
    assert loaded.display_name == "New Name"


@pytest.mark.asyncio
async def test_learner_profile_exists(
    db_session: AsyncSession,
    make_user: Callable[..., User],
    make_learner_profile: Callable[..., LearnerProfile],
):
    user_repo = UserRepository(db_session)
    profile_repo = LearnerProfileRepository(db_session)

    user = make_user()
    await user_repo.save(user)
    await db_session.commit()

    profile = make_learner_profile(user_id=user.id)
    await profile_repo.save(profile)
    await db_session.commit()

    assert await profile_repo.exists(profile.id) is True
    assert await profile_repo.exists(LearnerId(str(uuid4()))) is False

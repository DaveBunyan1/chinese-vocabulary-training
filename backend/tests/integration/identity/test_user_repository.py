from collections.abc import Callable
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.domain.identity.user import User, UserId
from chinese_learning.infrastructure.persistence.repositories.identity.user_repository import (
    UserRepository,
)


@pytest.mark.asyncio
async def test_user_get_returns_none_when_missing(db_session: AsyncSession):
    repo = UserRepository(db_session)
    assert await repo.get(UserId(str(uuid4()))) is None


@pytest.mark.asyncio
async def test_user_save_and_get(
    db_session: AsyncSession, make_user: Callable[..., User]
):
    repo = UserRepository(db_session)
    user = make_user()

    await repo.save(user)
    await db_session.commit()

    loaded = await repo.get(user.id)
    assert loaded is not None
    assert loaded.id == user.id
    assert loaded.email == user.email
    assert loaded.display_name == user.display_name


@pytest.mark.asyncio
async def test_user_get_by_email(
    db_session: AsyncSession, make_user: Callable[..., User]
):
    repo = UserRepository(db_session)
    user = make_user(email="unique@example.com")
    await repo.save(user)
    await db_session.commit()

    loaded = await repo.get_by_email("unique@example.com")
    assert loaded is not None
    assert loaded.id == user.id

    assert await repo.get_by_email("missing@example.com") is None


@pytest.mark.asyncio
async def test_user_save_updates_existing(
    db_session: AsyncSession, make_user: Callable[..., User]
):
    repo = UserRepository(db_session)
    user = make_user(display_name="Old Name")
    await repo.save(user)
    await db_session.commit()

    updated = make_user(
        id=(user.id),
        email=user.email,
        display_name="New Name",
    )
    await repo.save(updated)
    await db_session.commit()

    loaded = await repo.get(user.id)
    assert loaded is not None
    assert loaded.display_name == "New Name"
    # created_at should remain the original value (we don't overwrite it)


@pytest.mark.asyncio
async def test_user_save_many(db_session: AsyncSession, make_user: Callable[..., User]):
    repo = UserRepository(db_session)
    users = [
        make_user(email="a@example.com"),
        make_user(email="b@example.com"),
        make_user(email="c@example.com"),
    ]
    await repo.save_many(users)
    await db_session.commit()

    for u in users:
        assert await repo.exists(u.id) is True


@pytest.mark.asyncio
async def test_user_exists(db_session: AsyncSession, make_user: Callable[..., User]):
    repo = UserRepository(db_session)
    user = make_user()
    await repo.save(user)
    await db_session.commit()

    assert await repo.exists(user.id) is True
    assert await repo.exists(UserId(str(uuid4()))) is False


@pytest.mark.asyncio
async def test_user_exists_by_email(
    db_session: AsyncSession, make_user: Callable[..., User]
):
    repo = UserRepository(db_session)
    user = make_user(email="exists@example.com")
    await repo.save(user)
    await db_session.commit()

    assert await repo.exists_by_email("exists@example.com") is True
    assert await repo.exists_by_email("nope@example.com") is False

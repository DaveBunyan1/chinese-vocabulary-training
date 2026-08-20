from datetime import UTC, datetime
from typing import Any

import pytest

from chinese_learning.domain.identity.user import User, UserId

NOW = datetime(2026, 8, 20, 12, 0, 0, tzinfo=UTC)


def make_user(**overrides: Any):
    defaults = {
        "id": UserId("user-1"),
        "email": "learner@example.com",
        "display_name": "Dave",
        "created_at": NOW,
    }
    defaults.update(overrides)
    return User(**defaults)


class TestUserInvariants:
    def test_valid_user_can_be_created(self):
        user = make_user()
        assert user.email == "learner@example.com"
        assert user.display_name == "Dave"
        assert user.id.value == "user-1"

    def test_empty_email_raises(self):
        with pytest.raises(ValueError, match="email cannot be empty"):
            make_user(email="")

    def test_whitespace_only_email_raises(self):
        with pytest.raises(ValueError, match="email cannot be empty"):
            make_user(email="   ")

    def test_empty_display_name_raises(self):
        with pytest.raises(ValueError, match="display_name cannot be empty"):
            make_user(display_name="")

    def test_whitespace_only_display_name_raises(self):
        with pytest.raises(ValueError, match="display_name cannot be empty"):
            make_user(display_name="   ")

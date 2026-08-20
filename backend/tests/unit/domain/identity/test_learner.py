from datetime import UTC, datetime
from typing import Any

import pytest

from chinese_learning.domain.identity.learner import LearnerId, LearnerProfile
from chinese_learning.domain.identity.user import UserId

NOW = datetime(2026, 8, 20, 12, 0, 0, tzinfo=UTC)


def make_learner(**overrides: Any):
    defaults = {
        "id": LearnerId("learner-1"),
        "user_id": UserId("user-1"),
        "language": "zh-CN",
        "display_name": "My Chinese",
        "created_at": NOW,
    }
    defaults.update(overrides)
    return LearnerProfile(**defaults)


class TestLearnerProfileInvariants:
    def test_valid_learner_profile_can_be_created(self):
        profile = make_learner()
        assert profile.language == "zh-CN"
        assert profile.display_name == "My Chinese"
        assert profile.id.value == "learner-1"
        assert profile.user_id.value == "user-1"

    def test_empty_language_raises(self):
        with pytest.raises(ValueError, match="language cannot be empty"):
            make_learner(language="")

    def test_whitespace_only_language_raises(self):
        with pytest.raises(ValueError, match="language cannot be empty"):
            make_learner(language="   ")

    def test_empty_display_name_raises(self):
        with pytest.raises(ValueError, match="display_name cannot be empty"):
            make_learner(display_name="")

    def test_whitespace_only_display_name_raises(self):
        with pytest.raises(ValueError, match="display_name cannot be empty"):
            make_learner(display_name="   ")

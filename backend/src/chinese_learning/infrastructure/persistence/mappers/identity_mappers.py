from chinese_learning.domain.identity.learner import LearnerId, LearnerProfile
from chinese_learning.domain.identity.user import User, UserId
from chinese_learning.infrastructure.persistence.mappers.mappers_utils import (
    ensure_non_null_utc,
)
from chinese_learning.infrastructure.persistence.models import (
    LearnerProfileModel,
    UserModel,
)

# ---------- User ----------


def user_to_domain(model: UserModel) -> User:
    return User(
        id=UserId(model.id),
        email=model.email,
        display_name=model.display_name,
        created_at=ensure_non_null_utc(model.created_at),
    )


def user_to_model(domain: User) -> UserModel:
    return UserModel(
        id=str(domain.id.value),
        email=domain.email,
        display_name=domain.display_name,
        created_at=domain.created_at,
    )


# ---------- LearnerProfile ----------


def learner_profile_to_domain(model: LearnerProfileModel) -> LearnerProfile:
    return LearnerProfile(
        id=LearnerId(model.id),
        user_id=UserId(model.user_id),
        language=model.language,
        display_name=model.display_name,
        created_at=ensure_non_null_utc(model.created_at),
    )


def learner_profile_to_model(domain: LearnerProfile) -> LearnerProfileModel:
    return LearnerProfileModel(
        id=str(domain.id.value),
        user_id=str(domain.user_id.value),
        language=domain.language,
        display_name=domain.display_name,
        created_at=domain.created_at,
    )

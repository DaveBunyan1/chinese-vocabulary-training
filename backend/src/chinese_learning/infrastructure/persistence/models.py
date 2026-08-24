from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from chinese_learning.domain.category.category import CategoryType
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.infrastructure.persistence.base import Base


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class LearnerProfileModel(Base):
    __tablename__ = "learner_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    language: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. "zh-CN"
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class CharacterModel(Base):
    __tablename__ = "characters"

    symbol: Mapped[str] = mapped_column(String(1), primary_key=True, nullable=False)


class TokenModel(Base):
    __tablename__ = "tokens"

    text: Mapped[str] = mapped_column(String(255), primary_key=True, nullable=False)


class SentenceModel(Base):
    __tablename__ = "sentences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    tokens_json: Mapped[str] = mapped_column(Text, nullable=False)


class VocabularyItemModel(Base):
    __tablename__ = "vocabulary_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    text: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    pinyin: Mapped[str] = mapped_column(String(255), nullable=False)
    meaning: Mapped[str] = mapped_column(Text, nullable=False)


class CategoryModel(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(
        SQLEnum(CategoryType, values_callable=lambda x: [e.value for e in x]),  # pyright: ignore[reportUnknownLambdaType]
        nullable=False,
        index=True,
    )
    parent_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("categories.id"), nullable=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    hsk_level: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)


class CategoryAssignmentModel(Base):
    __tablename__ = "category_assignments"

    category_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("categories.id"), primary_key=True
    )
    vocabulary_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("vocabulary_items.id"), primary_key=True
    )

    __table_args__ = (
        UniqueConstraint("category_id", "vocabulary_id", name="uq_category_vocabulary"),
    )


class CharacterKnowledgeModel(Base):
    __tablename__ = "character_knowledge"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    learner_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    character_literal: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[KnowledgeStatus] = mapped_column(
        SQLEnum(KnowledgeStatus), nullable=False
    )

    successful_recognitions: Mapped[int] = mapped_column(Integer, default=0)
    failed_recognitions: Mapped[int] = mapped_column(Integer, default=0)
    correct_pinyin_count: Mapped[int] = mapped_column(Integer, default=0)

    times_seen: Mapped[int] = mapped_column(Integer, default=0)
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_practised_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_review_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )

    __table_args__ = (
        UniqueConstraint(
            "learner_id", "character_literal", name="uq_learner_character"
        ),
    )


class VocabularyKnowledgeModel(Base):
    __tablename__ = "vocabulary_knowledge"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    learner_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    vocabulary_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[KnowledgeStatus] = mapped_column(
        SQLEnum(KnowledgeStatus), nullable=False
    )

    successful_recalls: Mapped[int] = mapped_column(Integer, default=0)
    failed_recalls: Mapped[int] = mapped_column(Integer, default=0)
    times_seen: Mapped[int] = mapped_column(Integer, default=0)
    times_produced: Mapped[int] = mapped_column(Integer, default=0)

    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_practised_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    next_review_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )
    ease_factor: Mapped[float | None] = mapped_column(Float)
    interval_days: Mapped[float | None] = mapped_column(Float)

    __table_args__ = (
        UniqueConstraint("learner_id", "vocabulary_id", name="uq_learner_vocab"),
    )

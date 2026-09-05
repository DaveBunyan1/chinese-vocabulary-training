"""
Seed complete HSK 1 + HSK 2 vocabulary into the database.

- Ensures a default User + Chinese LearnerProfile exist
  (same UUIDs already used by the hard-coded routers).
- Creates VocabularyItem rows from the normalised HSK JSON files.
- Creates VocabularyKnowledge rows:
    HSK 1 → KnowledgeStatus.LEARNING
    HSK 2 → KnowledgeStatus.NEW
- Assigns each item to the corresponding HSK category
  (requires `make seed-categories` to have been run first).

Idempotent: uses deterministic UUIDs (uuid5) and ON CONFLICT upserts.

Usage (from repository root, DB running):
  make seed-hsk
  # or
  cd backend && PYTHONPATH=src python -m chinese_learning.infrastructure.persistence.seed.seed_hsk_vocabulary
"""

import asyncio
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from chinese_learning.domain.category.category import CategoryId
from chinese_learning.domain.category.category_assignment import CategoryAssignment
from chinese_learning.domain.identity.learner import LearnerId, LearnerProfile
from chinese_learning.domain.identity.user import User, UserId
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.learner.vocabulary_knowledge import VocabularyKnowledge
from chinese_learning.domain.vocabulary.vocabulary_item import (
    VocabularyId,
    VocabularyItem,
)
from chinese_learning.infrastructure.persistence.repositories.identity.learner_profile_repository import (
    LearnerProfileRepository,
)
from chinese_learning.infrastructure.persistence.repositories.identity.user_repository import (
    UserRepository,
)
from chinese_learning.infrastructure.persistence.repositories.learner.vocabulary_knowledge_repository import (
    VocabularyKnowledgeRepository,
)
from chinese_learning.infrastructure.persistence.repositories.linguistic.category_assignment_repository import (
    CategoryAssignmentRepository,
)
from chinese_learning.infrastructure.persistence.repositories.linguistic.vocabulary_item_repository import (
    VocabularyItemRepository,
)
from chinese_learning.infrastructure.persistence.repositories.repo_utils import logger
from chinese_learning.infrastructure.persistence.seed.categories import (
    HSK_1_ID,
    HSK_2_ID,
)
from chinese_learning.infrastructure.telemetry.config import settings

# Deterministic IDs already referenced by the presentation layer
DEFAULT_USER_ID = UserId(value="00000000-0000-0000-0000-000000000001")
DEFAULT_LEARNER_ID = LearnerId(value="00000000-0000-0000-0000-000000000001")

# Namespace for deterministic vocabulary UUIDs
_VOCAB_NS = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")

HSK_DATA_DIR = (
    Path(__file__).resolve().parents[3] / "application" / "services" / "data" / "hsk"
)


class Transcriptions(TypedDict, total=False):
    pinyin: str
    numeric: str
    wadegiles: str
    bopomofo: str
    romatzyh: str


class Form(TypedDict, total=False):
    traditional: str
    transcriptions: Transcriptions
    meanings: list[str]
    classifiers: list[str]


class Entry(TypedDict, total=False):
    simplified: str
    radical: str
    frequency: int
    pos: list[str]
    forms: list[Form]


def _primary_pinyin(entry: Entry) -> str:
    forms = entry.get("forms") or []
    if not forms:
        return entry.get("simplified", "")
    t = forms[0].get("transcriptions") or {}
    return (t.get("pinyin") or t.get("numeric") or "").strip() or entry.get(
        "simplified", ""
    )


def _primary_meaning(entry: Entry) -> str:
    forms = entry.get("forms") or []
    if not forms:
        return entry.get("simplified", "")
    meanings = forms[0].get("meanings") or []
    if not meanings:
        return entry.get("simplified", "")
    # Take the first sense; keep it reasonably short
    raw = meanings[0].strip()
    # Prefer the part before the first semicolon when present
    if ";" in raw:
        raw = raw.split(";")[0].strip()
    return raw or entry.get("simplified", "")


def _vocab_id_for(
    text: str, pos: str | None = None, sense_key: str | None = None
) -> VocabularyId:
    """Deterministic ID from surface form + POS (and optional sense_key fallback)."""
    pos_key = (pos or "").strip().lower()
    key = sense_key or f"{text}|{pos_key}"
    return VocabularyId(str(uuid.uuid5(_VOCAB_NS, key)))


def _primary_pos(entry: Entry) -> str | None:
    """First POS token from Mandarin Bean / project JSON, lowercased."""
    raw_list = entry.get("pos") or []
    if isinstance(raw_list, str):
        raw_list = [raw_list]
    for p in raw_list:
        token = str(p).strip().lower()
        token = token.split("（")[0].split("(")[0].strip()
        if token:
            return token
    return None


def load_hsk_entries(level: int) -> list[Entry]:
    path = HSK_DATA_DIR / f"{level}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run `python backend/scripts/normalize_hsk_json.py` first."
        )

    return_data: list[Entry] = json.loads(path.read_text(encoding="utf-8"))
    return return_data


async def ensure_default_user_and_learner(session: AsyncSession) -> None:
    user_repo = UserRepository(session)
    learner_repo = LearnerProfileRepository(session)

    existing_user = await user_repo.get(DEFAULT_USER_ID)
    if existing_user is None:
        now = datetime.now(UTC)
        user = User(
            id=DEFAULT_USER_ID,
            email="default@chinese-learning.local",
            display_name="Default Learner",
            created_at=now,
        )
        await user_repo.save(user)
        logger.info("seed.created_default_user", user_id=str(DEFAULT_USER_ID.value))

    existing_learner = await learner_repo.get(DEFAULT_LEARNER_ID)
    if existing_learner is None:
        now = datetime.now(UTC)
        profile = LearnerProfile(
            id=DEFAULT_LEARNER_ID,
            user_id=DEFAULT_USER_ID,
            language="zh-CN",
            display_name="My Chinese",
            created_at=now,
        )
        await learner_repo.save(profile)
        logger.info(
            "seed.created_default_learner", learner_id=str(DEFAULT_LEARNER_ID.value)
        )


async def seed_level(
    session: AsyncSession,
    *,
    level: int,
    status: KnowledgeStatus,
    category_id: CategoryId,
) -> tuple[int, int]:
    """
    Returns (items_upserted, knowledge_upserted).
    """
    entries = load_hsk_entries(level)
    item_repo = VocabularyItemRepository(session)
    knowledge_repo = VocabularyKnowledgeRepository(session)
    assignment_repo = CategoryAssignmentRepository(session)

    items: list[VocabularyItem] = []
    knowledges: list[VocabularyKnowledge] = []
    assignments: list[CategoryAssignment] = []
    now = datetime.now(UTC)

    for entry in entries:
        text = str(entry.get("simplified")) or str(entry.get("hanzi")) or ""
        if not text:
            continue
        pos = _primary_pos(entry)
        sense_key = str(entry.get("_sense_key"))
        vid = _vocab_id_for(text, pos=pos, sense_key=sense_key)
        pinyin = _primary_pinyin(entry)
        meaning = _primary_meaning(entry)

        items.append(
            VocabularyItem(
                id=vid,
                text=text,
                pinyin=pinyin,
                meaning=meaning,
                pos=pos,
            )
        )
        knowledges.append(
            VocabularyKnowledge(
                learner_id=DEFAULT_LEARNER_ID,
                vocabulary_id=vid,
                status=status,
                first_seen_at=now,
                last_seen_at=now,
            )
        )
        assignments.append(
            CategoryAssignment(category_id=category_id, vocabulary_id=vid)
        )

    await item_repo.save_many(items)
    await knowledge_repo.save_many(knowledges)
    await assignment_repo.save_many(assignments)

    return len(items), len(knowledges)


async def seed_hsk_vocabulary(session: AsyncSession) -> None:
    await ensure_default_user_and_learner(session)

    n1_items, n1_know = await seed_level(
        session,
        level=1,
        status=KnowledgeStatus.LEARNING,
        category_id=HSK_1_ID,
    )
    n2_items, n2_know = await seed_level(
        session,
        level=2,
        status=KnowledgeStatus.NEW,
        category_id=HSK_2_ID,
    )

    await session.commit()
    logger.info(
        "seed.hsk_complete",
        hsk1_items=n1_items,
        hsk1_knowledge=n1_know,
        hsk2_items=n2_items,
        hsk2_knowledge=n2_know,
    )
    print(f"Seeded HSK 1: {n1_items} items (LEARNING), HSK 2: {n2_items} items (NEW)")


async def main() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        await seed_hsk_vocabulary(session)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

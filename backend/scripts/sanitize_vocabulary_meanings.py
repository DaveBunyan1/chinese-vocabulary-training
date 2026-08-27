#!/usr/bin/env python3
"""
One-shot (or re-runnable) script: sanitize vocabulary_item.meaning values.

Strategy
--------
1. Prefer a fresh CC-CEDICT lookup for the item text (applies sanitizer at source).
2. If the word is missing from CEDICT, run sanitize_definition on the stored meaning.

Usage (from repo root, with venv active and DATABASE_URL set)::

    PYTHONPATH=backend/src python -m chinese_learning...  # not a package module
    cd backend && PYTHONPATH=src python scripts/sanitize_vocabulary_meanings.py
    # or dry-run:
    PYTHONPATH=src python scripts/sanitize_vocabulary_meanings.py --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Allow running as a script without install
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from chinese_learning.infrastructure.nlp.cedict_dictionary import (  # noqa: E402
    CedictDictionary,
)
from chinese_learning.infrastructure.nlp.definition_sanitize import (  # noqa: E402
    sanitize_definition,
)
from chinese_learning.infrastructure.persistence.models import (  # noqa: E402
    VocabularyItemModel,
)

DEFAULT_CEDICT = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "chinese_learning"
    / "infrastructure"
    / "nlp"
    / "data"
    / "cedict.txt"
)


async def run(*, dry_run: bool, database_url: str, cedict_path: Path) -> int:
    dictionary = CedictDictionary(cedict_path)
    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    updated = 0
    scanned = 0
    examples: list[tuple[str, str, str]] = []

    async with session_factory() as session:
        result = await session.execute(select(VocabularyItemModel))
        rows = list(result.scalars().all())
        scanned = len(rows)

        for row in rows:
            old = row.meaning
            if dictionary.contains(row.text):
                new = dictionary.lookup(row.text).meaning
            else:
                new = sanitize_definition(old)
                if not new.strip():
                    new = old

            if new == old:
                continue

            updated += 1
            if len(examples) < 15:
                examples.append((row.text, old, new))

            if not dry_run:
                await session.execute(
                    update(VocabularyItemModel)
                    .where(VocabularyItemModel.id == row.id)
                    .values(meaning=new)
                )

        if not dry_run:
            await session.commit()

    await engine.dispose()

    mode = "DRY-RUN" if dry_run else "APPLIED"
    print(
        f"[{mode}] scanned={scanned} would_update={updated}"
        if dry_run
        else f"[{mode}] scanned={scanned} updated={updated}"
    )
    for text, old, new in examples:
        print(f"  {text}")
        print(f"    - {old}")
        print(f"    + {new}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without writing to the database",
    )
    parser.add_argument(
        "--database-url",
        default=os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://chinese:chinese@localhost:5432/chinese_learning",
        ),
        help="Async SQLAlchemy URL (default: DATABASE_URL or local docker)",
    )
    parser.add_argument(
        "--cedict",
        type=Path,
        default=DEFAULT_CEDICT,
        help="Path to cedict.txt",
    )
    args = parser.parse_args()
    return asyncio.run(
        run(
            dry_run=args.dry_run,
            database_url=args.database_url,
            cedict_path=args.cedict,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
Sanitize meanings for Chinese characters.

Background
----------
The ``characters`` table only stores the symbol (PK). Pinyin/meaning for the
character dashboard and recognition exercises are resolved at runtime via
CC-CEDICT (``CedictDictionary.lookup``), which already runs
``sanitize_definition`` on load.

What *is* persisted are ``vocabulary_items`` rows. Single-character vocabulary
(e.g. 他, 是, 不) still holds a ``meaning`` column used by the vocabulary
dashboard and vocab practice. This script updates those rows.

For every distinct symbol in ``character_knowledge`` it also prints a
lookup sample so you can confirm live CEDICT glosses look clean (no DB write
needed for pure character entities).

Usage (from ``backend/``, venv active)::

    PYTHONPATH=src python scripts/sanitize_character_meanings.py --dry-run
    PYTHONPATH=src python scripts/sanitize_character_meanings.py
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

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
    CharacterKnowledgeModel,
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


def _is_single_cjk(text: str) -> bool:
    if len(text) != 1:
        return False
    code = ord(text)
    return (
        0x4E00 <= code <= 0x9FFF
        or 0x3400 <= code <= 0x4DBF
        or 0x20000 <= code <= 0x2A6DF
    )


async def run(*, dry_run: bool, database_url: str, cedict_path: Path) -> int:
    dictionary = CedictDictionary(cedict_path)
    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    vocab_scanned = 0
    vocab_updated = 0
    examples: list[tuple[str, str, str]] = []
    char_samples: list[tuple[str, str]] = []

    async with session_factory() as session:
        # --- 1) Single-character vocabulary_items ---
        result = await session.execute(select(VocabularyItemModel))
        rows = list(result.scalars().all())
        char_rows = [r for r in rows if _is_single_cjk(r.text)]
        vocab_scanned = len(char_rows)

        for row in char_rows:
            old = row.meaning
            if dictionary.contains(row.text):
                new = dictionary.lookup(row.text).meaning
            else:
                new = sanitize_definition(old)
                if not new.strip():
                    new = old

            if new == old:
                continue

            vocab_updated += 1
            if len(examples) < 20:
                examples.append((row.text, old, new))

            if not dry_run:
                await session.execute(
                    update(VocabularyItemModel)
                    .where(VocabularyItemModel.id == row.id)
                    .values(meaning=new)
                )

        if not dry_run and vocab_updated:
            await session.commit()

        # --- 2) Sample live CEDICT glosses for known characters ---
        ck = await session.execute(
            select(CharacterKnowledgeModel.character_literal).distinct()
        )
        symbols = sorted({row[0] for row in ck.all() if row[0]})
        for symbol in symbols[:30]:
            gloss = dictionary.lookup(symbol).meaning
            char_samples.append((symbol, gloss))

    await engine.dispose()

    mode = "DRY-RUN" if dry_run else "APPLIED"
    print(f"[{mode}] single-character vocabulary_items")
    print(f"  scanned={vocab_scanned} updated={vocab_updated}")
    for text, old, new in examples:
        print(f"  {text}")
        print(f"    - {old}")
        print(f"    + {new}")

    print()
    print(
        "Live CEDICT glosses for characters in character_knowledge "
        "(not stored in DB; already sanitized on dictionary load):"
    )
    if not char_samples:
        print("  (no character_knowledge rows found)")
    for symbol, gloss in char_samples:
        print(f"  {symbol} → {gloss}")

    print()
    print(
        "Note: the characters table has no meaning column. "
        "Dashboard/exercises call CedictDictionary.lookup at runtime."
    )
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
    )
    parser.add_argument("--cedict", type=Path, default=DEFAULT_CEDICT)
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

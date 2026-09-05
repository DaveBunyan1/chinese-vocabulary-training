"""
Normalize the project's HSK JSON files using Mandarin Bean as the source of truth.

Sources:
  https://mandarinbean.com/new-hsk-1-word-list/   (exactly 300 words)
  https://mandarinbean.com/new-hsk-2-word-list/   (200 syllabus entries)

Cached copies live under:
  backend/scripts/data/hsk_official/mandarinbean_hsk{1,2}.json

This script:
  1. Loads the Mandarin Bean tables (word, pinyin, POS, English translation).
  2. Keeps dual-sense rows separate (e.g. 过 verb vs 过 particle, 花 spend vs 花 flower).
  3. Builds project-schema JSON entries (simplified, forms[0].transcriptions + meanings).
  4. Optionally enriches radical / frequency / traditional from existing project JSON.
  5. Writes backend/.../data/hsk/1.json and 2.json.

Usage (from repository root):
  python backend/scripts/normalize_hsk_json.py
  python backend/scripts/normalize_hsk_json.py --fetch   # re-scrape live pages
"""

import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
HSK_DATA_DIR = (
    REPO_ROOT
    / "backend"
    / "src"
    / "chinese_learning"
    / "application"
    / "services"
    / "data"
    / "hsk"
)
OFFICIAL_DIR = Path(__file__).resolve().parent / "data" / "hsk_official"

MANDARINBEAN_URLS = {
    1: "https://mandarinbean.com/new-hsk-1-word-list/",
    2: "https://mandarinbean.com/new-hsk-2-word-list/",
}

# Sense markers Mandarin Bean appends for dual entries (花2, etc.)
_SENSE_MARKER_RE = re.compile(r"(\d+)$")


# ---------------------------------------------------------------------------
# HTML table scraper (Mandarin Bean)
# ---------------------------------------------------------------------------
class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_table = False
        self.in_td = False
        self.rows: list[list[str]] = []
        self.current_row: list[str] = []
        self.current_cell: list[str] = []
        self.table_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self.table_count += 1
            if self.table_count == 1:
                self.in_table = True
        elif tag == "tr" and self.in_table:
            self.current_row = []
        elif tag in ("td", "th") and self.in_table:
            self.in_td = True
            self.current_cell = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "table" and self.in_table:
            self.in_table = False
        elif tag in ("td", "th") and self.in_td:
            self.in_td = False
            self.current_row.append("".join(self.current_cell).strip())
        elif tag == "tr" and self.in_table and self.current_row:
            self.rows.append(self.current_row)
            self.current_row = []

    def handle_data(self, data: str) -> None:
        if self.in_td:
            self.current_cell.append(data)


def _parse_row(cells: list[str]) -> dict | None:
    """
    Accept both the normal 5-column layout and the occasional 4-column
    layout where Part of Speech is missing (e.g. 为什么).

      5 cols: No | Word | Pinyin | POS | Translation
      4 cols: No | Word | Pinyin | Translation
    """
    if not cells or not cells[0].isdigit():
        return None

    no = int(cells[0])
    if len(cells) >= 5:
        word, pinyin, pos, translation = cells[1], cells[2], cells[3], cells[4]
    elif len(cells) == 4:
        word, pinyin, pos, translation = cells[1], cells[2], "", cells[3]
    else:
        return None

    return {
        "no": no,
        "word": word.strip(),
        "pinyin": pinyin.replace(" ", "").strip(),
        "pos": pos.strip(),
        "translation": translation.strip(),
    }


def fetch_mandarinbean(level: int) -> list[dict]:
    """Scrape the Mandarin Bean word list page and return structured rows."""
    url = MANDARINBEAN_URLS[level]
    req = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        },
    )
    with urlopen(req, timeout=60) as resp:  # noqa: S310
        html = resp.read().decode("utf-8", errors="ignore")

    parser = _TableParser()
    parser.feed(html)

    rows: list[dict] = []
    for cells in parser.rows[1:]:  # skip header
        parsed = _parse_row(cells)
        if parsed is not None:
            rows.append(parsed)
    return rows


def load_or_fetch_mandarinbean(level: int, *, force_fetch: bool) -> list[dict]:
    cache = OFFICIAL_DIR / f"mandarinbean_hsk{level}.json"
    if force_fetch or not cache.exists():
        print(f"Fetching Mandarin Bean HSK {level} …")
        rows = fetch_mandarinbean(level)
        OFFICIAL_DIR.mkdir(parents=True, exist_ok=True)
        cache.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"  cached {len(rows)} rows → {cache}")
        return rows
    return json.loads(cache.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Keep dual-sense rows separate; only normalise display word
# ---------------------------------------------------------------------------
def normalize_rows(rows: list[dict]) -> list[dict]:
    """
    Keep every syllabus row (including dual-sense 过 / 花 pairs).

    - Strip trailing sense markers from the *display* word (花2 → 花)
      so the learner sees the real hanzi.
    - Preserve distinct pinyin / POS / translation so the two senses
      remain separate VocabularyItems after seeding.
    """
    out: list[dict] = []
    for row in rows:
        raw = row["word"]
        surface = _SENSE_MARKER_RE.sub("", raw).strip() or raw
        out.append(
            {
                "no": row["no"],
                "word": surface,
                "pinyin": row["pinyin"],
                "pos": row["pos"],
                "translation": row["translation"],
                # Keep original label for stable unique IDs when surface forms collide
                "raw_word": raw,
            }
        )
    return out


# ---------------------------------------------------------------------------
# Optional enrichment from previous project JSON
# ---------------------------------------------------------------------------
def load_existing_project_json(level: int) -> dict[str, dict]:
    path = HSK_DATA_DIR / f"{level}.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, dict] = {}
    for entry in data:
        key = entry.get("simplified") or entry.get("hanzi") or entry.get("word")
        if key:
            out[key] = entry
    return out


def build_project_entry(
    row: dict,
    existing: dict[str, dict],
) -> dict:
    """Map a Mandarin Bean row into the project's HSK JSON schema."""
    word = row["word"]
    pinyin = row["pinyin"] or word
    meaning = row["translation"] or word

    base = existing.get(word, {})
    radical = base.get("radical", "")
    frequency = base.get("frequency", 0)
    pos_list = [p.strip() for p in re.split(r"[、,;/]", row["pos"]) if p.strip()]
    if not pos_list:
        pos_list = base.get("pos") or []

    traditional = word
    if base.get("forms"):
        traditional = base["forms"][0].get("traditional") or word

    return {
        "simplified": word,
        "radical": radical,
        "frequency": frequency,
        "pos": pos_list,
        "forms": [
            {
                "traditional": traditional,
                "transcriptions": {
                    "pinyin": pinyin,
                    "numeric": pinyin,
                    "wadegiles": "",
                    "bopomofo": "",
                    "romatzyh": "",
                },
                "meanings": [meaning],
                "classifiers": (base.get("forms") or [{}])[0].get("classifiers") or [],
            }
        ],
        # Stable key for dual-sense items that share the same surface form
        "_sense_key": f"{row.get('raw_word', word)}|{pinyin}|{row['no']}",
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def normalize_level(level: int, *, force_fetch: bool) -> list[dict]:
    rows = load_or_fetch_mandarinbean(level, force_fetch=force_fetch)
    normalised = normalize_rows(rows)
    existing = load_existing_project_json(level)
    other = load_existing_project_json(1 if level == 2 else 2)
    existing = {**other, **existing}

    entries = [build_project_entry(row, existing) for row in normalised]
    print(
        f"HSK {level}: {len(rows)} syllabus rows → "
        f"{len(entries)} entries kept separate (Mandarin Bean)"
    )
    return entries


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="Re-download Mandarin Bean pages even if cache exists",
    )
    args = parser.parse_args()

    OFFICIAL_DIR.mkdir(parents=True, exist_ok=True)
    HSK_DATA_DIR.mkdir(parents=True, exist_ok=True)

    for level in (1, 2):
        entries = normalize_level(level, force_fetch=args.fetch)
        out_path = HSK_DATA_DIR / f"{level}.json"
        # Persist _sense_key so the seed script can build unique IDs for dual senses
        out_path.write_text(
            json.dumps(entries, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote {out_path} ({len(entries)} entries)")

    hsk1 = json.loads((HSK_DATA_DIR / "1.json").read_text(encoding="utf-8"))
    hsk2 = json.loads((HSK_DATA_DIR / "2.json").read_text(encoding="utf-8"))
    words1 = {e["simplified"] for e in hsk1}
    assert len(hsk1) == 300, f"Expected 300 HSK1 words, got {len(hsk1)}"
    assert "你好" in words1, "你好 must be in HSK 1"
    assert len(hsk2) == 200, f"Expected 200 HSK2 entries, got {len(hsk2)}"
    assert any(e["simplified"] == "为什么" for e in hsk2), "为什么 must be in HSK 2"
    # Dual senses preserved
    guo = [e for e in hsk2 if e["simplified"] == "过"]
    hua = [e for e in hsk2 if e["simplified"] == "花"]
    assert len(guo) == 2, f"Expected 2 senses of 过, got {len(guo)}"
    assert len(hua) == 2, f"Expected 2 senses of 花, got {len(hua)}"
    print("Sanity checks passed.")
    print(f"Final counts → HSK1: {len(hsk1)}, HSK2: {len(hsk2)}")


if __name__ == "__main__":
    main()

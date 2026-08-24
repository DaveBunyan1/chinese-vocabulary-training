import csv
import re
from pathlib import Path
from typing import Any

from chinese_learning.application.services.hsk_lookup_service import (
    get_default_hsk_lookup,
)
from chinese_learning.infrastructure.nlp.analyse_text import AnalyseText
from chinese_learning.infrastructure.nlp.cedict_dictionary import CedictDictionary

SAMPLES = Path(__file__).parent / "samples"
OUT = Path(__file__).parent / "out"
MISS_MARKERS = ("[not found", "not found in cc-cedict")  # adjust to your real string

DIGIT_RE = re.compile(r"^\d+$")
PUNCT_RE = re.compile(r"^[\W_]+$", re.UNICODE)


def is_miss(meaning: str) -> bool:
    m = meaning.lower()
    return any(s in m for s in MISS_MARKERS) or not meaning.strip()


def is_junk(text: str) -> bool:
    t = text.strip()
    if not t:
        return True
    if DIGIT_RE.match(t):
        return True
    if PUNCT_RE.match(t) and not any("\u4e00" <= c <= "\u9fff" for c in t):
        return True
    return False


def is_odd_meaning(meaning: str) -> bool:
    m = meaning.lower()
    if "surname" in m and m.count("/") <= 2:
        return True
    if len(meaning) > 400:
        return True
    return False


def main() -> None:
    OUT.mkdir(exist_ok=True)
    analyse = AnalyseText()
    dictionary = CedictDictionary(
        Path("src/chinese_learning/infrastructure/nlp/data/cedict.txt")
    )
    hsk = get_default_hsk_lookup()

    rows: list[dict[str, Any]] = []
    # unique surface forms across corpus (optional: also track per-file)
    seen: set[str] = set()

    for path in sorted(SAMPLES.glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        analysis = analyse.execute(text)
        for token in analysis.sentence.tokens:
            surface = token.text
            if surface in seen:
                continue
            seen.add(surface)

            item = dictionary.lookup(surface)  # or whatever returns meaning/pinyin
            meaning = item.meaning
            level = hsk.get_level(surface)

            rows.append(
                {
                    "source_file": path.name,
                    "text": surface,
                    "pinyin": item.pinyin,
                    "meaning": meaning,
                    "hsk_level": level if level is not None else "",
                    "is_miss": is_miss(meaning),
                    "is_junk": is_junk(surface),
                    "is_odd_meaning": is_odd_meaning(meaning),
                    "meaning_len": len(meaning),
                }
            )

    out_csv = OUT / "tokens.csv"
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)

    # --- summary ---
    n = len(rows)
    misses = [r for r in rows if r["is_miss"] and not r["is_junk"]]
    hsk_null = [
        r for r in rows if not r["hsk_level"] and not r["is_junk"] and not r["is_miss"]
    ]
    odd = [r for r in rows if r["is_odd_meaning"] and not r["is_miss"]]
    junk = [r for r in rows if r["is_junk"]]

    summary = OUT / "findings.md"
    summary.write_text(
        "\n".join(
            [
                "# Phase B findings",
                "",
                f"- Unique tokens: **{n}**",
                f"- Junk (digits/punct): **{len(junk)}** ({100 * len(junk) / max(n, 1):.1f}%)",
                f"- Dictionary misses (non-junk): **{len(misses)}** ({100 * len(misses) / max(n, 1):.1f}%)",
                f"- HSK null (non-junk, has gloss): **{len(hsk_null)}** ({100 * len(hsk_null) / max(n, 1):.1f}%)",
                f"- Odd meanings: **{len(odd)}**",
                "",
                "## Example misses",
                *[f"- `{r['text']}`" for r in misses[:30]],
                "",
                "## Example HSK null",
                *[f"- `{r['text']}` — {r['meaning'][:80]}" for r in hsk_null[:30]],
                "",
                "## Example odd definitions",
                *[f"- `{r['text']}` — {r['meaning'][:120]}" for r in odd[:20]],
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"Wrote {out_csv} and {summary}")


if __name__ == "__main__":
    main()

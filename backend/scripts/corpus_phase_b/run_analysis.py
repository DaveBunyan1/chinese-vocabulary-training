import csv
from pathlib import Path
from typing import Any

from chinese_learning.application.services.hsk_lookup_service import (
    get_default_hsk_lookup,
)
from chinese_learning.infrastructure.nlp.analyse_text import AnalyseText
from chinese_learning.infrastructure.nlp.cedict_dictionary import CedictDictionary
from chinese_learning.infrastructure.nlp.cedict_segment import max_match_segment
from chinese_learning.infrastructure.nlp.token_filters import is_studyable_chinese_token

SAMPLES = Path(__file__).parent / "samples"
OUT = Path(__file__).parent / "out"
SOFT_MISS = {"", "—", "-", "–"}


def is_miss(meaning: str) -> bool:
    return meaning.strip() in SOFT_MISS or "[not found" in meaning.lower()


def is_odd_meaning(meaning: str) -> bool:
    m = meaning.lower()
    if "surname" in m and m.count(";") <= 1:
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
    lexicon = dictionary.known_words()

    rows: list[dict[str, Any]] = []
    seen_pieces: set[str] = set()

    jieba_token_count = 0
    jieba_studyable = 0
    split_events = 0

    for path in sorted(SAMPLES.glob("*.txt")):
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            print(f"skip empty: {path.name}")
            continue

        analysis = analyse.execute(text)

        for token in analysis.sentence.tokens:
            surface = token.text
            jieba_token_count += 1

            if not is_studyable_chinese_token(surface):
                continue
            jieba_studyable += 1

            if dictionary.contains(surface):
                pieces = [surface]
                was_split = False
            else:
                pieces = [
                    p
                    for p in max_match_segment(surface, lexicon)
                    if is_studyable_chinese_token(p)
                ]
                was_split = pieces != [surface]
                if was_split:
                    split_events += 1

            if not pieces:
                continue

            for piece in pieces:
                if piece in seen_pieces:
                    continue
                seen_pieces.add(piece)

                item = dictionary.lookup(piece)
                meaning = item.meaning
                level = hsk.get_level(piece)

                rows.append(
                    {
                        "source_file": path.name,
                        "source_token": surface,
                        "text": piece,
                        "was_split": was_split and piece != surface,
                        "pinyin": item.pinyin,
                        "meaning": meaning,
                        "hsk_level": level if level is not None else "",
                        "is_miss": is_miss(meaning),
                        "is_odd_meaning": is_odd_meaning(meaning),
                        "meaning_len": len(meaning),
                    }
                )

    if not rows:
        print("No tokens found — check samples/")
        return

    out_csv = OUT / "tokens.csv"
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    n = len(rows)
    misses = [r for r in rows if r["is_miss"]]
    hsk_null = [r for r in rows if not r["hsk_level"] and not r["is_miss"]]
    odd = [r for r in rows if r["is_odd_meaning"] and not r["is_miss"]]
    split_pieces = [r for r in rows if r["was_split"]]

    summary = OUT / "findings.md"
    summary.write_text(
        "\n".join(
            [
                "# Corpus findings (aligned with import pipeline)",
                "",
                f"- Jieba tokens (raw stream): **{jieba_token_count}**",
                f"- Jieba studyable tokens: **{jieba_studyable}**",
                f"- Sub-segmentation expansions: **{split_events}**",
                f"- Unique pieces after sub-segmentation: **{n}**",
                f"- Dictionary misses (pieces): **{len(misses)}** ({100 * len(misses) / n:.1f}%)",
                f"- HSK null (non-miss pieces): **{len(hsk_null)}** ({100 * len(hsk_null) / n:.1f}%)",
                f"- Odd meanings: **{len(odd)}**",
                f"- Pieces that came from a split: **{len(split_pieces)}**",
                "",
                "## Example misses (after sub-segmentation)",
                *[f"- `{r['text']}` (from `{r['source_token']}`)" for r in misses[:30]],
                "",
                "## Example HSK null",
                *[f"- `{r['text']}` — {r['meaning'][:80]}" for r in hsk_null[:30]],
                "",
                "## Example odd definitions",
                *[f"- `{r['text']}` — {r['meaning'][:120]}" for r in odd[:20]],
                "",
                "## Example splits",
                *{
                    f"- `{r['source_token']}` → piece `{r['text']}`"
                    for r in split_pieces[:30]
                },
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"Wrote {out_csv} and {summary}")


if __name__ == "__main__":
    main()

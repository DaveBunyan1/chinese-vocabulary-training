"""Pinyin tone-number ↔ diacritic conversion and match normalisation."""

from __future__ import annotations

import re
import unicodedata

_MARK_TO_TONE: dict[str, tuple[str, int]] = {}
for _vowel, _marks in {
    "a": "āáǎà",
    "e": "ēéěè",
    "i": "īíǐì",
    "o": "ōóǒò",
    "u": "ūúǔù",
    "ü": "ǖǘǚǜ",
}.items():
    for _tone, _ch in enumerate(_marks, start=1):
        _MARK_TO_TONE[_ch] = (_vowel, _tone)
        _MARK_TO_TONE[_ch.upper()] = (_vowel.upper(), _tone)

_TONE_MARKS: dict[str, tuple[str, ...]] = {
    "a": ("a", "ā", "á", "ǎ", "à"),
    "e": ("e", "ē", "é", "ě", "è"),
    "i": ("i", "ī", "í", "ǐ", "ì"),
    "o": ("o", "ō", "ó", "ǒ", "ò"),
    "u": ("u", "ū", "ú", "ǔ", "ù"),
    "ü": ("ü", "ǖ", "ǘ", "ǚ", "ǜ"),
    "v": ("ü", "ǖ", "ǘ", "ǚ", "ǜ"),
}

_SYLLABLE_NUM_RE = re.compile(r"([a-züv]+)([1-5])", re.IGNORECASE)
_VOWELS = set("aeiouvüAEIOUVÜ")


def to_tone_numbers(pinyin: str) -> str:
    """
    Convert diacritic pinyin to numbered form.

    ``nǐ hǎo`` / ``nǐhǎo`` → ``ni3 hao3`` / ``ni3hao3``
    """
    if not pinyin:
        return pinyin

    text = unicodedata.normalize("NFC", pinyin).replace("v", "ü").replace("V", "Ü")
    out: list[str] = []
    i = 0
    pending_tone: int | None = None

    def flush_tone() -> None:
        nonlocal pending_tone
        if pending_tone is not None:
            out.append(str(pending_tone))
            pending_tone = None

    while i < len(text):
        ch = text[i]
        if ch in _MARK_TO_TONE:
            base, tone = _MARK_TO_TONE[ch]
            out.append(base)
            pending_tone = tone
            i += 1
            # Consume rest of this syllable only:
            # - unmarked vowels (e.g. ǎo → ao)
            # - coda n / ng / r
            # Do not consume the next syllable's initial consonant.
            while i < len(text):
                nxt = text[i]
                if nxt in _MARK_TO_TONE:
                    break
                if nxt in "aeiouüAEIOUÜ" or nxt in _VOWELS:
                    out.append(nxt)
                    i += 1
                    continue
                # coda: n, ng, r
                if nxt in "nN":
                    out.append(nxt)
                    i += 1
                    if i < len(text) and text[i] in "gG":
                        out.append(text[i])
                        i += 1
                    break
                if nxt in "rR":
                    out.append(nxt)
                    i += 1
                    break
                break
            flush_tone()
            continue

        if not ch.isalpha() and ch not in "üÜ":
            flush_tone()
            out.append(ch)
            i += 1
            continue

        out.append(ch)
        i += 1

    flush_tone()
    return "".join(out)


def to_tone_marks(pinyin: str) -> str:
    """Convert numbered pinyin to diacritic form. ``ni3 hao3`` → ``nǐ hǎo``."""
    if not pinyin:
        return pinyin

    def repl(match: re.Match[str]) -> str:
        syllable = match.group(1)
        tone = int(match.group(2))
        if tone == 5:
            return syllable.replace("v", "ü").replace("V", "Ü")
        return _apply_tone_mark(syllable, tone)

    return _SYLLABLE_NUM_RE.sub(repl, pinyin)


def _apply_tone_mark(syllable: str, tone: int) -> str:
    lower = syllable.lower().replace("v", "ü")
    for target in ("a", "e", "o"):
        idx = lower.find(target)
        if idx >= 0:
            return _replace_vowel_at(syllable, idx, target, tone)
    last = -1
    last_v = ""
    for i, ch in enumerate(lower):
        if ch in "iuü":
            last = i
            last_v = ch
    if last >= 0:
        return _replace_vowel_at(syllable, last, last_v, tone)
    return syllable


def _replace_vowel_at(syllable: str, idx: int, vowel: str, tone: int) -> str:
    marks = _TONE_MARKS.get(vowel, (vowel,))
    mark = marks[tone] if 0 <= tone < len(marks) else vowel
    return syllable[:idx] + mark + syllable[idx + 1 :]


def normalize_pinyin_for_match(value: str) -> str:
    """Canonical form: tone numbers, no spaces, casefold, ü as v."""
    text = value.strip()
    text = to_tone_numbers(text)
    text = text.casefold().replace("ü", "v")
    text = re.sub(r"[\s']+", "", text)
    return text


def looks_like_pinyin(value: str) -> bool:
    if not value or not re.search(r"[A-Za-züÜ]", value):
        return False
    if re.search(r"[\u4e00-\u9fff]", value):
        return False
    if re.search(r"[āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ]", value):
        return True
    if re.search(r"[a-zü]+[1-5]", value, re.IGNORECASE):
        return True
    return bool(re.fullmatch(r"[A-Za-züÜ\s']+", value.strip()))

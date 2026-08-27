"""Sanitize CC-CEDICT glosses into short learner-facing definitions."""

import re

# Sense is dropped when it begins with these markers (optionally inside parens)
_META_SENSE_START_RE = re.compile(
    r"(?i)^\s*(?:"
    r"\("
    r"(?:bound form|variant of|old variant of|archaic variant of|"
    r"see also|abbr\.?|abbreviation|used in|used before|used after)"
    r"\)|"
    r"(?:bound form|variant of|old variant of|archaic variant of|"
    r"see also|abbr\.?|abbreviation)\b"
    r")"
)

_PAREN_RE = re.compile(r"\([^)]*\)")
_BRACKET_REF_RE = re.compile(r"\[[^\]]*\]")
_MULTI_SPACE_RE = re.compile(r"\s+")
_MULTI_SEMI_RE = re.compile(r"\s*;\s*")
_HAS_WORD_RE = re.compile(r"[\w\u4e00-\u9fff]", re.UNICODE)


def sanitize_definition(raw: str) -> str:
    """
    Turn a raw CC-CEDICT definition field into a concise gloss.

    CEDICT stores senses separated by ``/``. Each sense may include
    parenthetical usage notes, bound-form markers, classifier tags, etc.

    Example
    -------
    ``(third-person singular) (since the early 20th century, usu. male)
    he; him; his/(bound form) other; another; ...``
    → ``he; him; his``
    """
    if not raw or not raw.strip():
        return raw

    senses = [s.strip() for s in raw.split("/") if s.strip()]
    if not senses:
        senses = [raw.strip()]

    cleaned: list[str] = []
    for sense in senses:
        cleaned_sense = _sanitize_sense(sense)
        if cleaned_sense and cleaned_sense not in cleaned:
            cleaned.append(cleaned_sense)

    if not cleaned:
        fallback = _PAREN_RE.sub("", raw)
        fallback = _BRACKET_REF_RE.sub("", fallback)
        fallback = _MULTI_SPACE_RE.sub(" ", fallback).strip(" ;,")
        return fallback or raw.strip()

    return "; ".join(cleaned)


def _sanitize_sense(sense: str) -> str:
    if _META_SENSE_START_RE.match(sense):
        return ""

    text = _PAREN_RE.sub("", sense)
    text = _BRACKET_REF_RE.sub("", text)
    text = _MULTI_SPACE_RE.sub(" ", text).strip()

    parts = [p.strip() for p in _MULTI_SEMI_RE.split(text) if p.strip()]
    parts = [p for p in parts if _HAS_WORD_RE.search(p)]
    return "; ".join(parts)

import re

_DIGIT_RE = re.compile(r"^\d+$")
# Latin letters / common Western tokens (allow internal hyphen/apostrophe)
_LATIN_RE = re.compile(r"^[A-Za-z]+(?:['-][A-Za-z]+)*$")
_PUNCT_OR_SPACE_RE = re.compile(r"^[\s\W_]+$", re.UNICODE)


def is_studyable_chinese_token(text: str) -> bool:
    """
    Return True if this surface form should become vocabulary.
    Filters pure digits, pure Latin, and punctuation-only tokens.
    """
    t = text.strip()
    if not t:
        return False
    if _DIGIT_RE.match(t):
        return False
    if _LATIN_RE.match(t):
        return False
    if _PUNCT_OR_SPACE_RE.match(t):
        return False
    # Must contain at least one CJK unified ideograph
    if not any("\u4e00" <= ch <= "\u9fff" for ch in t):
        return False
    return True

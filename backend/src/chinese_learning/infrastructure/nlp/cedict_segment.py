def max_match_segment(
    text: str, lexicon: set[str], *, max_word_len: int = 4
) -> list[str]:
    """
    Forward maximum matching against a CEDICT key set.

    Prefers the longest prefix in `lexicon` at each position.
    If no multi-char match exists, emits one character and continues.
    """
    if not text:
        return []

    n = len(text)
    i = 0
    parts: list[str] = []

    while i < n:
        matched = None
        # Longest first
        upper = min(max_word_len, n - i)
        for size in range(upper, 0, -1):
            piece = text[i : i + size]
            if piece in lexicon:
                matched = piece
                break
        if matched is None:
            # Unknown single char (or non-Han): still emit so we don't drop text
            matched = text[i]
        parts.append(matched)
        i += len(matched)

    return parts

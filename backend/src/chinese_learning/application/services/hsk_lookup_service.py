import json
from functools import lru_cache
from pathlib import Path


class HSKLookupService:
    """
    Maps a Chinese word (simplified) → lowest HSK 3.0 level (1-7).
    Level 7 = HSK 7-9 band.
    Returns None when the word is not in any HSK list.
    """

    def __init__(self, word_to_level: dict[str, int]) -> None:
        self._map = word_to_level

    def get_level(self, word: str) -> int | None:
        """Return 1-7 or None."""
        return self._map.get(word)

    @classmethod
    def from_drkameleon_json(cls, path: Path | str) -> HSKLookupService:
        """
        Load from drkameleon/complete-hsk-vocabulary style files.
        Prefer the exclusive lists so each word is tagged with the
        level at which it is first introduced.
        """
        path = Path(path)
        word_to_level: dict[str, int] = {}

        for level in range(1, 8):
            file = path / f"{level}.json"
            if not file.exists():
                continue
            data = json.loads(file.read_text(encoding="utf-8"))
            for entry in data:
                # drkameleon entries usually have "simplified" or "hanzi"
                word = (
                    entry.get("simplified") or entry.get("hanzi") or entry.get("word")
                )
                if word and word not in word_to_level:
                    word_to_level[word] = level

        return cls(word_to_level)


@lru_cache(maxsize=1)
def get_default_hsk_lookup() -> HSKLookupService:

    data_dir = Path(__file__).resolve().parent / "data" / "hsk"
    return HSKLookupService.from_drkameleon_json(data_dir)

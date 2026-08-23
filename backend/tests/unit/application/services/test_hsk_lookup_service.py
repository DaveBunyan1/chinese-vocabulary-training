import json
from pathlib import Path

import pytest

from chinese_learning.application.services.hsk_lookup_service import HSKLookupService


@pytest.fixture
def sample_hsk_dir(tmp_path: Path) -> Path:
    """Minimal exclusive-style files mimicking drkameleon layout."""
    data = {
        1: [{"simplified": "爱"}, {"simplified": "八"}],
        2: [{"simplified": "爸爸"}, {"simplified": "杯子"}],
        3: [{"simplified": "安静"}],
        7: [{"simplified": "尴尬"}],  # 7-9 band
    }
    for level, entries in data.items():
        (tmp_path / f"{level}.json").write_text(json.dumps(entries), encoding="utf-8")
    return tmp_path


def test_get_level_returns_correct_level(sample_hsk_dir: Path):
    service = HSKLookupService.from_drkameleon_json(sample_hsk_dir)

    assert service.get_level("爱") == 1
    assert service.get_level("八") == 1
    assert service.get_level("爸爸") == 2
    assert service.get_level("杯子") == 2
    assert service.get_level("安静") == 3
    assert service.get_level("尴尬") == 7


def test_get_level_returns_none_for_unknown(sample_hsk_dir: Path):
    service = HSKLookupService.from_drkameleon_json(sample_hsk_dir)
    assert service.get_level("不存在的词") is None
    assert service.get_level("") is None


def test_first_seen_level_wins(sample_hsk_dir: Path):
    """A word that appears in multiple files keeps the lowest level."""
    # Manually add the same word to level 1 and 3
    level3 = json.loads((sample_hsk_dir / "3.json").read_text())
    level3.append({"simplified": "爱"})
    (sample_hsk_dir / "3.json").write_text(json.dumps(level3), encoding="utf-8")

    service = HSKLookupService.from_drkameleon_json(sample_hsk_dir)
    assert service.get_level("爱") == 1  # still the first (lowest) level

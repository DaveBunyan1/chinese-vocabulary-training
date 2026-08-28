from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from chinese_learning.application.use_cases.link_vocabulary_characters import (
    LinkVocabularyCharacters,
)
from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.character_knowledge import CharacterKnowledge
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.text_analysis.character import Character
from chinese_learning.domain.vocabulary.vocabulary_item import (
    VocabularyId,
    VocabularyItem,
)

FIXED = datetime(2026, 8, 28, 12, 0, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_creates_knowledge_for_constituent_characters() -> None:
    repo = AsyncMock()
    repo.get_many.return_value = []
    use_case = LinkVocabularyCharacters(repo)
    learner = LearnerId(str(uuid4()))
    item = VocabularyItem(
        id=VocabularyId(str(uuid4())),
        text="你好",
        pinyin="nǐhǎo",
        meaning="hello",
    )

    result = await use_case.execute(learner, [item], at=FIXED)

    assert result.characters_created == 2
    assert result.characters_updated == 0
    repo.save_many.assert_awaited_once()
    saved = repo.save_many.await_args.args[0]
    symbols = {str(k.character) for k in saved}
    assert symbols == {"你", "好"}
    assert all(k.status is KnowledgeStatus.NEW for k in saved)


@pytest.mark.asyncio
async def test_updates_existing_character_knowledge() -> None:
    repo = AsyncMock()
    learner = LearnerId(str(uuid4()))
    existing = CharacterKnowledge(
        learner_id=learner,
        character=Character("你"),
        status=KnowledgeStatus.LEARNING,
        times_seen=3,
        first_seen_at=FIXED,
        last_seen_at=FIXED,
    )
    repo.get_many.return_value = [existing]
    use_case = LinkVocabularyCharacters(repo)
    item = VocabularyItem(
        id=VocabularyId(str(uuid4())),
        text="你",
        pinyin="nǐ",
        meaning="you",
    )

    result = await use_case.execute(learner, [item], at=FIXED)

    assert result.characters_created == 0
    assert result.characters_updated == 1
    saved = repo.save_many.await_args.args[0]
    assert saved[0].times_seen == 4

"""
Integration tests for practice REST endpoints.

These require a seeded learner with some vocabulary/character knowledge.
They follow the same async_client + db_session_populated pattern as
test_text_import_router.py.
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.domain.learner.character_knowledge import CharacterKnowledge
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.learner.vocabulary_knowledge import VocabularyKnowledge
from chinese_learning.domain.text_analysis.character import Character
from chinese_learning.domain.vocabulary.vocabulary_item import (
    VocabularyId,
    VocabularyItem,
)
from chinese_learning.infrastructure.persistence.repositories.learner.character_knowledge_repository import (
    CharacterKnowledgeRepository,
)
from chinese_learning.infrastructure.persistence.repositories.learner.vocabulary_knowledge_repository import (
    VocabularyKnowledgeRepository,
)
from chinese_learning.infrastructure.persistence.repositories.linguistic.vocabulary_item_repository import (
    VocabularyItemRepository,
)
from chinese_learning.presentation.rest.routers.practice import DEFAULT_LEARNER_ID

LEARNER_ID = DEFAULT_LEARNER_ID


async def _seed_vocab(
    session: AsyncSession,
    *,
    text: str = "你好",
    pinyin: str = "nǐhǎo",
    meaning: str = "hello",
    status: KnowledgeStatus = KnowledgeStatus.LEARNING,
) -> VocabularyItem:
    vid = VocabularyId(str(uuid4()))
    item = VocabularyItem(id=vid, text=text, pinyin=pinyin, meaning=meaning)
    await VocabularyItemRepository(session).save(item)
    knowledge = VocabularyKnowledge(
        learner_id=LEARNER_ID,
        vocabulary_id=vid,
        status=status,
    )
    await VocabularyKnowledgeRepository(session).save(knowledge)
    await session.commit()
    return item


async def _seed_character(
    session: AsyncSession,
    *,
    symbol: str = "学",
    status: KnowledgeStatus = KnowledgeStatus.LEARNING,
) -> Character:
    char = Character(symbol)
    knowledge = CharacterKnowledge(
        learner_id=LEARNER_ID,
        character=char,
        status=status,
    )
    await CharacterKnowledgeRepository(session).save(knowledge)
    await session.commit()
    return char


@pytest.mark.asyncio
async def test_generate_vocabulary_recall_success(
    async_client: AsyncClient,
    db_session_populated: AsyncSession,
) -> None:
    await _seed_vocab(db_session_populated)
    await _seed_vocab(
        db_session_populated, text="谢谢", pinyin="xièxie", meaning="thanks"
    )

    response = await async_client.post(
        "/api/v1/practice/vocabulary-recall",
        json={"count": 5, "direction": "meaning_to_hanzi"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "vocabulary_recall"
    assert data["status"] == "pending"
    assert data["question_count"] >= 1
    assert data["candidate_count"] >= 1
    assert len(data["questions"]) == data["question_count"]

    q = data["questions"][0]
    assert q["type"] == "vocabulary_recall"
    assert q["vocabulary_id"] is not None
    assert q["character"] is None
    assert len(q["correct_answers"]) >= 1
    assert q["prompt"]


@pytest.mark.asyncio
async def test_generate_vocabulary_recall_no_knowledge_returns_404(
    async_client: AsyncClient,
    db_session_populated: AsyncSession,
) -> None:
    response = await async_client.post(
        "/api/v1/practice/vocabulary-recall",
        json={"count": 5},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_generate_vocabulary_recall_invalid_direction(
    async_client: AsyncClient,
    db_session_populated: AsyncSession,
) -> None:
    await _seed_vocab(db_session_populated)
    response = await async_client.post(
        "/api/v1/practice/vocabulary-recall",
        json={"count": 1, "direction": "not_a_direction"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_generate_character_recognition_success(
    async_client: AsyncClient,
    db_session_populated: AsyncSession,
) -> None:
    await _seed_character(db_session_populated, symbol="学")
    await _seed_character(db_session_populated, symbol="习")

    response = await async_client.post(
        "/api/v1/practice/character-recognition",
        json={"count": 5, "direction": "character_to_meaning"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "character_recognition"
    assert data["status"] == "pending"
    assert data["question_count"] >= 1

    q = data["questions"][0]
    assert q["type"] == "character_recognition"
    assert q["character"] is not None
    assert q["vocabulary_id"] is None


@pytest.mark.asyncio
async def test_generate_character_recognition_no_knowledge_returns_404(
    async_client: AsyncClient,
) -> None:
    response = await async_client.post(
        "/api/v1/practice/character-recognition",
        json={"count": 5},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_submit_vocab_answer_correct(
    async_client: AsyncClient,
    db_session_populated: AsyncSession,
) -> None:
    item = await _seed_vocab(db_session_populated)

    gen = await async_client.post(
        "/api/v1/practice/vocabulary-recall",
        json={"count": 1, "direction": "meaning_to_hanzi"},
    )
    assert gen.status_code == 200
    exercise = gen.json()
    q = exercise["questions"][0]

    response = await async_client.post(
        "/api/v1/practice/answers",
        json={
            "exercise_id": exercise["id"],
            "question_id": q["id"],
            "question_type": "vocabulary_recall",
            "raw_answer": item.text,
            "correct_answers": q["correct_answers"],
            "vocabulary_id": q["vocabulary_id"],
            "response_time_ms": 900,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_correct"] is True
    assert data["attempt_id"]
    assert data["new_status"] in {"learning", "known"}
    assert data["response_time_ms"] == 900


@pytest.mark.asyncio
async def test_submit_vocab_answer_incorrect(
    async_client: AsyncClient,
    db_session_populated: AsyncSession,
) -> None:
    await _seed_vocab(db_session_populated)

    gen = await async_client.post(
        "/api/v1/practice/vocabulary-recall",
        json={"count": 1},
    )
    exercise = gen.json()
    q = exercise["questions"][0]

    response = await async_client.post(
        "/api/v1/practice/answers",
        json={
            "exercise_id": exercise["id"],
            "question_id": q["id"],
            "question_type": "vocabulary_recall",
            "raw_answer": "totally-wrong",
            "correct_answers": q["correct_answers"],
            "vocabulary_id": q["vocabulary_id"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_correct"] is False


@pytest.mark.asyncio
async def test_submit_answer_invalid_question_type(
    async_client: AsyncClient,
    db_session_populated: AsyncSession,
) -> None:
    response = await async_client.post(
        "/api/v1/practice/answers",
        json={
            "exercise_id": str(uuid4()),
            "question_id": str(uuid4()),
            "question_type": "not_valid",
            "raw_answer": "x",
            "correct_answers": ["y"],
            "vocabulary_id": str(uuid4()),
        },
    )
    assert response.status_code == 422

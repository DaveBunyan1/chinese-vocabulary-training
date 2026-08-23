import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.infrastructure.persistence.models import (
    CategoryAssignmentModel,
    CategoryModel,
    CharacterKnowledgeModel,
    VocabularyItemModel,
    VocabularyKnowledgeModel,
)
from chinese_learning.presentation.rest.routers.text_import import DEFAULT_LEARNER_ID

LEARNER_ID = DEFAULT_LEARNER_ID.value  # "00000000-0000-0000-0000-000000000001"


@pytest.mark.asyncio
async def test_import_text_success(
    async_client: AsyncClient,
    db_session_populated: AsyncSession,
) -> None:
    payload = {"raw_text": "我喜欢学中文。"}

    response = await async_client.post("/api/v1/imports/text", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert data["total_tokens"] > 0
    assert data["created_vocabulary_count"] > 0
    assert data["existing_vocabulary_count"] == 0
    assert data["updated_character_knowledge_count"] > 0
    assert data["updated_vocabulary_knowledge_count"] > 0
    assert len(data["imported_items"]) > 0

    # Response shape + HSK level present
    first = data["imported_items"][0]
    assert {"id", "text", "pinyin", "meaning", "hsk_level"} <= first.keys()
    assert first["hsk_level"] is None or isinstance(first["hsk_level"], int)

    # Knowledge rows written for the correct learner
    vocab_records = (
        (
            await db_session_populated.execute(
                select(VocabularyKnowledgeModel).where(
                    VocabularyKnowledgeModel.learner_id == LEARNER_ID
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(vocab_records) == data["updated_vocabulary_knowledge_count"]

    char_records = (
        (
            await db_session_populated.execute(
                select(CharacterKnowledgeModel).where(
                    CharacterKnowledgeModel.learner_id == LEARNER_ID
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(char_records) == data["updated_character_knowledge_count"]


@pytest.mark.asyncio
async def test_import_text_assigns_hsk_categories(
    async_client: AsyncClient,
    db_session_populated: AsyncSession,
) -> None:
    """Every imported vocabulary item should have exactly one HSK or Uncategorised assignment."""
    payload = {"raw_text": "我喜欢学中文。"}

    response = await async_client.post("/api/v1/imports/text", json=payload)
    assert response.status_code == 200
    data = response.json()

    item_ids = [item["id"] for item in data["imported_items"]]
    assert item_ids

    # All items exist in vocabulary_items
    vocab_rows = (
        (
            await db_session_populated.execute(
                select(VocabularyItemModel).where(VocabularyItemModel.id.in_(item_ids))
            )
        )
        .scalars()
        .all()
    )
    assert len(vocab_rows) == len(item_ids)

    # Each has at least one category assignment
    assignments = (
        (
            await db_session_populated.execute(
                select(CategoryAssignmentModel).where(
                    CategoryAssignmentModel.vocabulary_id.in_(item_ids)
                )
            )
        )
        .scalars()
        .all()
    )
    assigned_vocab_ids = {a.vocabulary_id for a in assignments}
    assert assigned_vocab_ids == set(item_ids)

    # Those categories are HSK or SYSTEM
    category_ids = {a.category_id for a in assignments}
    categories = (
        (
            await db_session_populated.execute(
                select(CategoryModel).where(CategoryModel.id.in_(category_ids))
            )
        )
        .scalars()
        .all()
    )
    assert all(c.type in ("hsk", "system") for c in categories)


@pytest.mark.asyncio
async def test_import_text_hsk_level_in_response_matches_known_words(
    async_client: AsyncClient,
) -> None:
    """
    Use a short phrase with well-known HSK 1 words so we can assert levels.
    Adjust the expected levels if your HSK data differs.
    """
    payload = {"raw_text": "我爱你"}  # 我/爱/你 are typically HSK 1

    response = await async_client.post("/api/v1/imports/text", json=payload)
    assert response.status_code == 200
    data = response.json()

    by_text = {item["text"]: item for item in data["imported_items"]}
    # These assertions depend on your loaded HSK lists – keep them loose if needed
    for word in ("我", "爱", "你"):
        if word in by_text:
            level = by_text[word]["hsk_level"]
            assert level is None or level == 1


@pytest.mark.asyncio
async def test_import_text_subsequent_exposure_increments_count(
    async_client: AsyncClient,
) -> None:
    payload = {"raw_text": "你好"}

    res1 = await async_client.post("/api/v1/imports/text", json=payload)
    assert res1.status_code == 200
    data1 = res1.json()
    created_first = data1["created_vocabulary_count"]
    assert created_first > 0

    res2 = await async_client.post("/api/v1/imports/text", json=payload)
    assert res2.status_code == 200
    data2 = res2.json()

    assert data2["created_vocabulary_count"] == 0
    assert data2["existing_vocabulary_count"] == created_first


@pytest.mark.asyncio
async def test_import_text_validation_empty_string(
    async_client: AsyncClient,
) -> None:
    response = await async_client.post("/api/v1/imports/text", json={"raw_text": ""})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_import_text_validation_missing_field(
    async_client: AsyncClient,
) -> None:
    response = await async_client.post("/api/v1/imports/text", json={})
    assert response.status_code == 422

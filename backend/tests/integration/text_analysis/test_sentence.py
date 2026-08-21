from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.domain.text_analysis.sentence import Sentence
from chinese_learning.domain.text_analysis.token import Token
from chinese_learning.infrastructure.persistence.repositories.text_analysis.sentence_repository import (
    SentenceRepository,
)


def make_sentence(
    raw_text: str = "我喜欢学习中文", token_texts: list[str] | None = None
) -> Sentence:
    if token_texts is None:
        token_texts = ["我", "喜欢", "学习", "中文"]
    tokens = [Token(t) for t in token_texts]
    return Sentence(raw_text=raw_text, tokens=tokens)


@pytest.mark.asyncio
async def test_sentence_get_returns_none_when_missing(db_session: AsyncSession):
    repo = SentenceRepository(db_session)
    assert await repo.get(str(uuid4())) is None


@pytest.mark.asyncio
async def test_sentence_save_and_get(db_session: AsyncSession):
    repo = SentenceRepository(db_session)
    sentence = make_sentence()

    sentence_id = await repo.save(sentence)
    await db_session.commit()

    loaded = await repo.get(sentence_id)
    assert loaded is not None
    assert loaded.raw_text == "我喜欢学习中文"
    assert [t.text for t in loaded.tokens] == ["我", "喜欢", "学习", "中文"]


@pytest.mark.asyncio
async def test_sentence_save_with_explicit_id(db_session: AsyncSession):
    repo = SentenceRepository(db_session)
    sentence = make_sentence()
    custom_id = str(uuid4())

    returned_id = await repo.save(sentence, sentence_id=custom_id)
    await db_session.commit()

    assert returned_id == custom_id
    loaded = await repo.get(custom_id)
    assert loaded is not None
    assert loaded.raw_text == sentence.raw_text


@pytest.mark.asyncio
async def test_sentence_save_many(db_session: AsyncSession):
    repo = SentenceRepository(db_session)
    s1 = make_sentence("我爱中国", ["我", "爱", "中国"])
    s2 = make_sentence("今天天气很好", ["今天", "天气", "很", "好"])

    ids = await repo.save_many([s1, s2])
    await db_session.commit()

    assert len(ids) == 2
    assert len(set(ids)) == 2  # unique IDs

    loaded1 = await repo.get(ids[0])
    loaded2 = await repo.get(ids[1])
    assert loaded1 is not None and loaded1.raw_text == "我爱中国"
    assert loaded2 is not None and loaded2.raw_text == "今天天气很好"


@pytest.mark.asyncio
async def test_sentence_save_many_empty(db_session: AsyncSession):
    repo = SentenceRepository(db_session)
    assert await repo.save_many([]) == []


@pytest.mark.asyncio
async def test_sentence_get_by_raw_text(db_session: AsyncSession):
    repo = SentenceRepository(db_session)
    s1 = make_sentence("重复句子", ["重复", "句子"])
    s2 = make_sentence("重复句子", ["重复", "句子"])  # same text, different instance
    s3 = make_sentence("不同句子", ["不同", "句子"])

    await repo.save_many([s1, s2, s3])
    await db_session.commit()

    results = await repo.get_by_raw_text("重复句子")
    assert len(results) == 2
    assert all(s.raw_text == "重复句子" for s in results)


@pytest.mark.asyncio
async def test_sentence_exists(db_session: AsyncSession):
    repo = SentenceRepository(db_session)
    sentence = make_sentence()
    sentence_id = await repo.save(sentence)
    await db_session.commit()

    assert await repo.exists(sentence_id) is True
    assert await repo.exists(str(uuid4())) is False


@pytest.mark.asyncio
async def test_sentence_tokens_order_is_preserved(db_session: AsyncSession):
    repo = SentenceRepository(db_session)
    sentence = make_sentence(
        raw_text="一二三四五",
        token_texts=["一", "二", "三", "四", "五"],
    )

    sentence_id = await repo.save(sentence)
    await db_session.commit()

    loaded = await repo.get(sentence_id)
    assert loaded is not None
    assert [t.text for t in loaded.tokens] == ["一", "二", "三", "四", "五"]

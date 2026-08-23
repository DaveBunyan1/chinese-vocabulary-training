from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from chinese_learning.application.use_cases.import_vocabulary_from_text import (
    ImportVocabularyFromText,
    ImportVocabularyResult,
)
from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.text_analysis.character import Character
from chinese_learning.domain.text_analysis.sentence import Sentence
from chinese_learning.domain.text_analysis.token import Token
from chinese_learning.domain.vocabulary.vocabulary_item import (
    VocabularyId,
    VocabularyItem,
)
from chinese_learning.infrastructure.nlp.text_analysis_result import (
    TextAnalysisResult,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_vocab(text: str, id: str | None = None) -> VocabularyItem:
    return VocabularyItem(
        id=VocabularyId(id or str(uuid4())),
        text=text,
        pinyin="test",
        meaning="test meaning",
    )


def make_analysis(
    token_texts: list[str], raw_text: str = "dummy"
) -> TextAnalysisResult:
    tokens = [Token(t) for t in token_texts]
    sentence = Sentence(raw_text=raw_text, tokens=tokens)
    characters = tuple(Character(c) for t in token_texts for c in t if len(c) == 1)
    return TextAnalysisResult(sentence=sentence, characters=characters)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.fixture
def learner_id() -> LearnerId:
    return LearnerId(str(uuid4()))


@pytest.fixture
def analyse_text() -> Mock:
    return Mock()


@pytest.fixture
def dictionary() -> Mock:
    return Mock()


@pytest.fixture
def vocabulary_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def assign_hsk() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def use_case(
    analyse_text: Mock,
    dictionary: Mock,
    vocabulary_repo: AsyncMock,
    assign_hsk: AsyncMock,
) -> ImportVocabularyFromText:
    return ImportVocabularyFromText(
        analyse_text=analyse_text,
        dictionary=dictionary,
        vocabulary_repo=vocabulary_repo,
        assign_hsk=assign_hsk,
    )


@pytest.mark.asyncio
async def test_all_tokens_already_exist(
    use_case: ImportVocabularyFromText,
    analyse_text: Mock,
    dictionary: Mock,
    vocabulary_repo: AsyncMock,
    learner_id: LearnerId,
):
    analysis = make_analysis(["我", "喜欢", "中文"])
    analyse_text.execute.return_value = analysis

    existing_items = [make_vocab(t) for t in ["我", "喜欢", "中文"]]
    vocabulary_repo.get_by_text.side_effect = existing_items

    result = await use_case.execute(learner_id, "我喜欢中文")

    assert isinstance(result, ImportVocabularyResult)
    assert result.created_count == 0
    assert result.existing_count == 3
    assert len(result.vocabulary_items) == 3
    assert result.analysis is analysis

    dictionary.lookup.assert_not_called()
    vocabulary_repo.save.assert_not_called()


@pytest.mark.asyncio
async def test_all_tokens_are_new(
    use_case: ImportVocabularyFromText,
    analyse_text: Mock,
    dictionary: Mock,
    vocabulary_repo: AsyncMock,
    learner_id: LearnerId,
):
    analysis = make_analysis(["学习", "中文"])
    analyse_text.execute.return_value = analysis

    vocabulary_repo.get_by_text.return_value = None

    new_items = [make_vocab("学习"), make_vocab("中文")]
    dictionary.lookup.side_effect = new_items

    result = await use_case.execute(learner_id, "学习中文")

    assert result.created_count == 2
    assert result.existing_count == 0
    assert len(result.vocabulary_items) == 2

    assert dictionary.lookup.call_count == 2
    assert vocabulary_repo.save.call_count == 2


@pytest.mark.asyncio
async def test_mixed_existing_and_new(
    use_case: ImportVocabularyFromText,
    analyse_text: Mock,
    dictionary: Mock,
    vocabulary_repo: AsyncMock,
    learner_id: LearnerId,
):
    analysis = make_analysis(["我", "学习", "中文"])
    analyse_text.execute.return_value = analysis

    existing = make_vocab("我")
    new1 = make_vocab("学习")
    new2 = make_vocab("中文")

    vocabulary_repo.get_by_text.side_effect = [existing, None, None]
    dictionary.lookup.side_effect = [new1, new2]

    result = await use_case.execute(learner_id, "我学习中文")

    assert result.created_count == 2
    assert result.existing_count == 1
    assert len(result.vocabulary_items) == 3

    # Order should follow the original token order
    assert result.vocabulary_items[0].text == "我"
    assert result.vocabulary_items[1].text == "学习"
    assert result.vocabulary_items[2].text == "中文"


@pytest.mark.asyncio
async def test_empty_analysis_raises(
    use_case: ImportVocabularyFromText,
    analyse_text: Mock,
    learner_id: LearnerId,
):
    analyse_text.execute.side_effect = ValueError("raw_text cannot be empty")

    with pytest.raises(ValueError, match="raw_text cannot be empty"):
        await use_case.execute(learner_id, "")


@pytest.mark.asyncio
async def test_result_contains_original_analysis(
    use_case: ImportVocabularyFromText,
    analyse_text: Mock,
    vocabulary_repo: AsyncMock,
    learner_id: LearnerId,
):
    analysis = make_analysis(["测试"])
    analyse_text.execute.return_value = analysis
    vocabulary_repo.get_by_text.return_value = make_vocab("测试")

    result = await use_case.execute(learner_id, "测试")

    assert result.analysis is analysis
    assert result.analysis.sentence.raw_text == "dummy"

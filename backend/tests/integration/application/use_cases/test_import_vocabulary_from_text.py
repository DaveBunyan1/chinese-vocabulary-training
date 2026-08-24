import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.application.services.hsk_lookup_service import HSKLookupService
from chinese_learning.application.use_cases.assign_hsk_category import AssignHSKCategory
from chinese_learning.application.use_cases.import_vocabulary_from_text import (
    ImportVocabularyFromText,
)
from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.infrastructure.nlp.analyse_text import AnalyseText
from chinese_learning.infrastructure.nlp.cedict_dictionary import CedictDictionary
from chinese_learning.infrastructure.persistence.repositories.linguistic.category_assignment_repository import (
    CategoryAssignmentRepository,
)
from chinese_learning.infrastructure.persistence.repositories.linguistic.category_repository import (
    CategoryRepository,
)
from chinese_learning.infrastructure.persistence.repositories.linguistic.vocabulary_item_repository import (
    VocabularyItemRepository,
)

LEARNER_ID = LearnerId(value="00000000-0000-0000-0000-000000000001")


@pytest.fixture
def hsk_lookup() -> HSKLookupService:
    return HSKLookupService({"我": 1, "的": 1, "喜欢": 1, "学": 1, "中文": 1})


@pytest.fixture
def use_case(
    db_session_populated: AsyncSession,
    hsk_lookup: HSKLookupService,
    cedict_dictionary: CedictDictionary,
) -> ImportVocabularyFromText:
    return ImportVocabularyFromText(
        analyse_text=AnalyseText(),
        dictionary=cedict_dictionary,
        vocabulary_repo=VocabularyItemRepository(db_session_populated),
        assign_hsk=AssignHSKCategory(
            hsk_lookup,
            CategoryRepository(db_session_populated),
            CategoryAssignmentRepository(db_session_populated),
        ),
    )


@pytest.mark.asyncio
async def test_repeated_tokens_return_unique_vocabulary_items(
    db_session_populated: AsyncSession,
    use_case: ImportVocabularyFromText,
) -> None:
    result = await use_case.execute(LEARNER_ID, "我的我的我的")
    await db_session_populated.commit()

    texts = [item.text for item in result.vocabulary_items]
    ids = [item.id.value for item in result.vocabulary_items]

    assert len(result.vocabulary_items) == len(set(texts))
    assert len(ids) == len(set(ids))
    assert set(texts) == {"我", "的"}
    assert result.created_count == 2
    assert result.existing_count == 0
    # analysis still reflects full token stream
    assert len(result.analysis.sentence.tokens) == 6


@pytest.mark.asyncio
async def test_repeated_tokens_second_import_counts_as_existing(
    db_session_populated: AsyncSession,
    use_case: ImportVocabularyFromText,
) -> None:
    first = await use_case.execute(LEARNER_ID, "我的我的")
    await db_session_populated.commit()
    assert first.created_count == 2
    assert first.existing_count == 0

    second = await use_case.execute(LEARNER_ID, "我的我的我的")
    await db_session_populated.commit()

    assert second.created_count == 0
    assert second.existing_count == 2
    assert len(second.vocabulary_items) == 2
    assert {i.text for i in second.vocabulary_items} == {"我", "的"}


@pytest.mark.asyncio
async def test_mixed_new_and_existing_without_duplicate_items(
    db_session_populated: AsyncSession,
    use_case: ImportVocabularyFromText,
) -> None:
    await use_case.execute(LEARNER_ID, "我")
    await db_session_populated.commit()

    result = await use_case.execute(LEARNER_ID, "我的我")
    await db_session_populated.commit()

    assert result.created_count == 1  # 的
    assert result.existing_count == 1  # 我 (counted once, not twice)
    assert len(result.vocabulary_items) == 2
    assert {i.text for i in result.vocabulary_items} == {"我", "的"}


@pytest.mark.asyncio
async def test_compound_miss_is_split_into_known_parts(
    use_case: ImportVocabularyFromText,
):
    result = await use_case.execute(LEARNER_ID, "坐在")
    texts = {i.text for i in result.vocabulary_items}
    assert "坐在" not in texts
    assert "坐" in texts and "在" in texts
    assert all(
        i.meaning != "—" for i in result.vocabulary_items if i.text in {"坐", "在"}
    )


@pytest.mark.asyncio
async def test_known_compound_not_split(use_case: ImportVocabularyFromText):
    result = await use_case.execute(LEARNER_ID, "中国")
    texts = [i.text for i in result.vocabulary_items]
    assert "中国" in texts

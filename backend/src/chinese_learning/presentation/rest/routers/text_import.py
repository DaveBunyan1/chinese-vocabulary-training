from pathlib import Path

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.application.services.hsk_lookup_service import (
    HSKLookupService,
    get_default_hsk_lookup,
)
from chinese_learning.application.use_cases.assign_hsk_category import AssignHSKCategory
from chinese_learning.application.use_cases.import_vocabulary_from_text import (
    ImportVocabularyFromText,
)
from chinese_learning.application.use_cases.link_vocabulary_characters import (
    LinkVocabularyCharacters,
)
from chinese_learning.application.use_cases.update_knowledge_on_exposure import (
    UpdateKnowledgeOnExposure,
)
from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.infrastructure.nlp.analyse_text import AnalyseText
from chinese_learning.infrastructure.nlp.cedict_dictionary import CedictDictionary
from chinese_learning.infrastructure.persistence.database import get_db_session
from chinese_learning.infrastructure.persistence.repositories.learner.character_knowledge_repository import (
    CharacterKnowledgeRepository,
)
from chinese_learning.infrastructure.persistence.repositories.learner.vocabulary_knowledge_repository import (
    VocabularyKnowledgeRepository,
)
from chinese_learning.infrastructure.persistence.repositories.linguistic.category_assignment_repository import (
    CategoryAssignmentRepository,
)
from chinese_learning.infrastructure.persistence.repositories.linguistic.category_repository import (
    CategoryRepository,
)
from chinese_learning.infrastructure.persistence.repositories.linguistic.vocabulary_item_repository import (
    VocabularyItemRepository,
)
from chinese_learning.presentation.rest.schemas.text_import import (
    ImportedVocabularySummary,
    TextImportRequest,
    TextImportResponse,
)

router = APIRouter(prefix="/imports", tags=["Imports"])

DEFAULT_LEARNER_ID = LearnerId(value="00000000-0000-0000-0000-000000000001")


def get_current_learner_id() -> LearnerId:
    # Hardcoded for single-user vertical slice
    return DEFAULT_LEARNER_ID


def get_cedict_dictionary() -> CedictDictionary:
    # Resolves to: chinese_learning/infrastructure/nlp/data/cedict.txt
    dict_path = (
        Path(__file__).resolve().parents[3]  # Go up to chinese_learning/
        / "infrastructure"
        / "nlp"
        / "data"
        / "cedict.txt"
    )
    return CedictDictionary(dict_path)


@router.post(
    "/text",
    response_model=TextImportResponse,
    status_code=status.HTTP_200_OK,
    summary="Import Chinese text and update learner knowledge profile",
)
async def import_text(
    payload: TextImportRequest,
    # TODO: Replace hardcoded default with authenticated user/learner session context
    learner_id: LearnerId = Depends(get_current_learner_id),
    session: AsyncSession = Depends(get_db_session),
    hsk_lookup: HSKLookupService = Depends(get_default_hsk_lookup),
    dictionary: CedictDictionary = Depends(get_cedict_dictionary),
) -> TextImportResponse:

    vocab_repo = VocabularyItemRepository(session)
    category_repo = CategoryRepository(session)
    assignment_repo = CategoryAssignmentRepository(session)

    import_use_case = ImportVocabularyFromText(
        analyse_text=AnalyseText(),
        dictionary=dictionary,
        vocabulary_repo=vocab_repo,
        assign_hsk=AssignHSKCategory(hsk_lookup, category_repo, assignment_repo),
    )
    update_use_case = UpdateKnowledgeOnExposure(
        character_knowledge_repo=CharacterKnowledgeRepository(session),
        vocabulary_knowledge_repo=VocabularyKnowledgeRepository(session),
    )

    import_result = await import_use_case.execute(learner_id, payload.raw_text)

    exposure_result = await update_use_case.execute(
        learner_id=learner_id,
        characters=list(import_result.analysis.characters),
        vocabulary_ids=[item.id for item in import_result.vocabulary_items],
    )

    # Ensure every imported word's constituent characters have knowledge rows
    link_result = await LinkVocabularyCharacters(
        CharacterKnowledgeRepository(session)
    ).execute(learner_id, list(import_result.vocabulary_items))

    # Prefer the higher character touch count for the response metric
    char_knowledge_count = max(
        exposure_result.character_knowledge_updated,
        link_result.characters_touched,
    )

    await session.commit()

    imported_summaries = [
        ImportedVocabularySummary(
            id=str(item.id.value),
            text=item.text,
            pinyin=item.pinyin,
            meaning=item.meaning,
            hsk_level=hsk_lookup.get_level(item.text),
        )
        for item in import_result.vocabulary_items
    ]

    return TextImportResponse(
        total_tokens=len(import_result.analysis.sentence.tokens),
        created_vocabulary_count=import_result.created_count,
        existing_vocabulary_count=import_result.existing_count,
        updated_character_knowledge_count=char_knowledge_count,
        updated_vocabulary_knowledge_count=exposure_result.vocabulary_knowledge_updated,
        imported_items=imported_summaries,
    )

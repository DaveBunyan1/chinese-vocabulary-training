from pydantic import BaseModel, Field


class TextImportRequest(BaseModel):
    raw_text: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Raw Chinese text to analyze and import.",
        examples=["我喜欢学中文。"],
    )


class ImportedVocabularySummary(BaseModel):
    id: str
    text: str
    pinyin: str
    meaning: str
    hsk_level: int | None = Field(
        default=None,
        description="HSK 3.0 level (1–7). 7 means the 7-9 band. None = Uncategorised / not in HSK.",
    )


class TextImportResponse(BaseModel):
    total_tokens: int
    created_vocabulary_count: int
    existing_vocabulary_count: int
    updated_character_knowledge_count: int
    updated_vocabulary_knowledge_count: int
    imported_items: list[ImportedVocabularySummary]

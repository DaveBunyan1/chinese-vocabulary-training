export interface TextImportRequest {
  raw_text: string;
}

export interface ImportedVocabularySummary {
  id: string;
  text: string;
  pinyin: string;
  meaning: string;
}

export interface TextImportResponse {
  total_tokens: number;
  created_vocabulary_count: number;
  existing_vocabulary_count: number;
  updated_character_knowledge_count: number;
  updated_vocabulary_knowledge_count: number;
  imported_items: ImportedVocabularySummary[];
}

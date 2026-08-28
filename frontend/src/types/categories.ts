export interface Category {
  id: string;
  name: string;
  type: string;
  parent_id: string | null;
  sort_order: number;
  hsk_level: number | null;
}

export interface CategoryListResponse {
  categories: Category[];
}

export interface CreateCategoryRequest {
  name: string;
  parent_id?: string | null;
  type?: "custom" | "topic";
}

export interface CreateCategoryResponse {
  category: Category;
}

export interface AssignCategoryRequest {
  vocabulary_id: string;
  category_id: string;
}

export interface AssignCategoryResponse {
  assigned: boolean;
  vocabulary_id: string;
  category_id: string;
}

export interface CategoryVocabularyItem {
  vocabulary_id: string;
  text: string;
  pinyin: string;
  meaning: string;
}

export interface CategoryVocabularyResponse {
  category_id: string;
  items: CategoryVocabularyItem[];
  total: number;
}

export interface UpdateCategoryRequest {
  name?: string | null;
  parent_id?: string | null;
  clear_parent?: boolean;
  sort_order?: number | null;
}

export interface UpdateCategoryResponse {
  category: Category;
}

export interface CategorySummary {
  id: string;
  name: string;
  type: string;
  hsk_level: number | null;
}

export interface VocabularyDashboardItem {
  vocabulary_id: string;
  text: string;
  pinyin: string;
  meaning: string;
  status: string;
  successful_recalls: number;
  failed_recalls: number;
  times_seen: number;
  last_practised_at: string | null;
  last_seen_at: string | null;
  categories: CategorySummary[];
  hsk_level: number | null;
}

export interface VocabularyDashboardResponse {
  items: VocabularyDashboardItem[];
  total: number;
  status_counts: Record<string, number>;
}

export interface CategoryListItem {
  id: string;
  name: string;
  type: string;
  parent_id: string | null;
  sort_order: number;
  hsk_level: number | null;
}

export interface CategoryListResponse {
  categories: CategoryListItem[];
}

export interface VocabularyDashboardFilters {
  status?: string | null;
  category_id?: string | null;
  hsk_level?: number | null;
  search?: string | null;
}

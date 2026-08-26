export interface CharacterDashboardItem {
  character: string;
  pinyin: string;
  meaning: string;
  status: string;
  successful_recognitions: number;
  failed_recognitions: number;
  correct_pinyin_count: number;
  times_seen: number;
  last_practised_at: string | null;
  last_seen_at: string | null;
}

export interface CharacterDashboardResponse {
  items: CharacterDashboardItem[];
  total: number;
  status_counts: Record<string, number>;
}

export interface CharacterDashboardFilters {
  status?: string | null;
  search?: string | null;
}

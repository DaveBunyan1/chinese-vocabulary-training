export interface StatusBreakdown {
  new: number;
  learning: number;
  known: number;
  total: number;
}

export interface VocabularyProgress {
  by_status: StatusBreakdown;
  total_successful_recalls: number;
  total_failed_recalls: number;
  total_times_seen: number;
  items_practised: number;
}

export interface CharacterProgress {
  by_status: StatusBreakdown;
  total_successful_recognitions: number;
  total_failed_recognitions: number;
  total_times_seen: number;
  items_practised: number;
}

export interface ProgressStatsResponse {
  vocabulary: VocabularyProgress;
  characters: CharacterProgress;
}

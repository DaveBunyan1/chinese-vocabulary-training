export type ReviewItemKind = "vocabulary" | "character";
export type ReviewReason = "due" | "unscheduled";

export interface ReviewQueueItem {
  kind: ReviewItemKind;
  reason: ReviewReason;
  vocabulary_id: string | null;
  text: string | null;
  pinyin: string | null;
  meaning: string | null;
  character: string | null;
  status: string;
  next_review_at: string | null;
  successful_attempts: number;
  failed_attempts: number;
}

export interface ReviewQueueResponse {
  items: ReviewQueueItem[];
  due_vocabulary_count: number;
  due_character_count: number;
  unscheduled_vocabulary_count: number;
  unscheduled_character_count: number;
  total: number;
  as_of: string;
}

export interface ReviewQueueFilters {
  limit?: number;
  include_vocabulary?: boolean;
  include_characters?: boolean;
  include_unscheduled?: boolean;
}

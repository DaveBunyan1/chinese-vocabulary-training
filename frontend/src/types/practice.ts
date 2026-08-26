export type QuestionType = "vocabulary_recall" | "character_recognition";

export type KnowledgeStatus = "new" | "learning" | "known";

export type RecallDirection =
  | "meaning_to_hanzi"
  | "hanzi_to_meaning"
  | "pinyin_to_hanzi";

export type RecognitionDirection =
  | "character_to_meaning"
  | "character_to_pinyin"
  | "meaning_to_character"
  | "pinyin_to_character";

export interface AnswerOption {
  text: string;
  is_correct: boolean;
}

export interface Question {
  id: string;
  type: QuestionType;
  order: number;
  prompt: string;
  correct_answers: string[];
  vocabulary_id: string | null;
  character: string | null;
  options: AnswerOption[];
  is_multiple_choice: boolean;
}

export interface Exercise {
  id: string;
  learner_id: string;
  type: QuestionType;
  status: string;
  questions: Question[];
  category_id: string | null;
  knowledge_status_filter: string | null;
  question_count: number;
  candidate_count: number;
  created_at: string;
}

export interface GenerateVocabularyRecallRequest {
  count?: number;
  category_id?: string | null;
  knowledge_status?: KnowledgeStatus | null;
  direction?: RecallDirection;
}

export interface GenerateCharacterRecognitionRequest {
  count?: number;
  knowledge_status?: KnowledgeStatus | null;
  direction?: RecognitionDirection;
}

export interface SubmitAnswerRequest {
  exercise_id: string;
  question_id: string;
  question_type: QuestionType;
  raw_answer: string;
  correct_answers: string[];
  vocabulary_id?: string | null;
  character?: string | null;
  response_time_ms?: number | null;
}

export interface SubmitAnswerResponse {
  attempt_id: string;
  is_correct: boolean;
  previous_status: string | null;
  new_status: string | null;
  raw_answer: string;
  response_time_ms: number | null;
}

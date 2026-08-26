import { apiClient } from "./client";
import type {
  Exercise,
  GenerateCharacterRecognitionRequest,
  GenerateVocabularyRecallRequest,
  SubmitAnswerRequest,
  SubmitAnswerResponse,
} from "../types/practice";

export const generateVocabularyRecall = async (
  data: GenerateVocabularyRecallRequest = {},
): Promise<Exercise> => {
  const response = await apiClient.post<Exercise>(
    "/practice/vocabulary-recall",
    data,
  );
  return response.data;
};

export const generateCharacterRecognition = async (
  data: GenerateCharacterRecognitionRequest = {},
): Promise<Exercise> => {
  const response = await apiClient.post<Exercise>(
    "/practice/character-recognition",
    data,
  );
  return response.data;
};

export const submitAnswer = async (
  data: SubmitAnswerRequest,
): Promise<SubmitAnswerResponse> => {
  const response = await apiClient.post<SubmitAnswerResponse>(
    "/practice/answers",
    data,
  );
  return response.data;
};

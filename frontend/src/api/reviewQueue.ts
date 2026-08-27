import { apiClient } from "./client";
import type {
  ReviewQueueFilters,
  ReviewQueueResponse,
} from "../types/reviewQueue";

export const fetchReviewQueue = async (
  filters: ReviewQueueFilters = {},
): Promise<ReviewQueueResponse> => {
  const params: Record<string, string | number | boolean> = {};
  if (filters.limit != null) params.limit = filters.limit;
  if (filters.include_vocabulary != null) {
    params.include_vocabulary = filters.include_vocabulary;
  }
  if (filters.include_characters != null) {
    params.include_characters = filters.include_characters;
  }
  if (filters.include_unscheduled != null) {
    params.include_unscheduled = filters.include_unscheduled;
  }

  const response = await apiClient.get<ReviewQueueResponse>("/review-queue", {
    params,
  });
  return response.data;
};

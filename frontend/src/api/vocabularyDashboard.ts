import { apiClient } from "./client";
import type {
  CategoryListResponse,
  VocabularyDashboardFilters,
  VocabularyDashboardResponse,
} from "../types/vocabularyDashboard";

export const fetchVocabularyDashboard = async (
  filters: VocabularyDashboardFilters = {},
): Promise<VocabularyDashboardResponse> => {
  const params: Record<string, string | number> = {};
  if (filters.status) params.status = filters.status;
  if (filters.category_id) params.category_id = filters.category_id;
  if (filters.hsk_level != null) params.hsk_level = filters.hsk_level;
  if (filters.search) params.search = filters.search;

  const response = await apiClient.get<VocabularyDashboardResponse>(
    "/vocabulary",
    { params },
  );
  return response.data;
};

export const fetchCategories = async (): Promise<CategoryListResponse> => {
  const response = await apiClient.get<CategoryListResponse>(
    "/vocabulary/categories",
  );
  return response.data;
};

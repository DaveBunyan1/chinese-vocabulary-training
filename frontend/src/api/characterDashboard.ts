import { apiClient } from "./client";
import type {
  CharacterDashboardFilters,
  CharacterDashboardResponse,
} from "../types/characterDashboard";

export const fetchCharacterDashboard = async (
  filters: CharacterDashboardFilters = {},
): Promise<CharacterDashboardResponse> => {
  const params: Record<string, string> = {};
  if (filters.status) params.status = filters.status;
  if (filters.search) params.search = filters.search;

  const response = await apiClient.get<CharacterDashboardResponse>(
    "/characters",
    { params },
  );
  return response.data;
};

import { apiClient } from "./client";
import type { ProgressStatsResponse } from "../types/progress";

export const fetchProgressStats = async (): Promise<ProgressStatsResponse> => {
  const response = await apiClient.get<ProgressStatsResponse>("/progress");
  return response.data;
};

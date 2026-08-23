import { apiClient } from "./client";
import type {
  TextImportRequest,
  TextImportResponse,
} from "../types/textImport";

export const importChineseText = async (
  data: TextImportRequest,
): Promise<TextImportResponse> => {
  const response = await apiClient.post<TextImportResponse>(
    "/imports/text",
    data,
  );
  return response.data;
};

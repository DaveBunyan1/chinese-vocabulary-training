import { apiClient } from "./client";
import type {
  AssignCategoryRequest,
  AssignCategoryResponse,
  CategoryListResponse,
  CategoryVocabularyResponse,
  CreateCategoryRequest,
  CreateCategoryResponse,
  UpdateCategoryRequest,
  UpdateCategoryResponse,
} from "../types/categories";

export const fetchCategories = async (): Promise<CategoryListResponse> => {
  const response = await apiClient.get<CategoryListResponse>("/categories");
  return response.data;
};

export const createCategory = async (
  data: CreateCategoryRequest,
): Promise<CreateCategoryResponse> => {
  const response = await apiClient.post<CreateCategoryResponse>(
    "/categories",
    data,
  );
  return response.data;
};

export const assignCategory = async (
  data: AssignCategoryRequest,
): Promise<AssignCategoryResponse> => {
  const response = await apiClient.post<AssignCategoryResponse>(
    "/categories/assignments",
    data,
  );
  return response.data;
};

export const unassignCategory = async (
  vocabulary_id: string,
  category_id: string,
): Promise<void> => {
  await apiClient.delete("/categories/assignments", {
    data: { vocabulary_id, category_id },
  });
};

export const fetchCategoryVocabulary = async (
  category_id: string,
): Promise<CategoryVocabularyResponse> => {
  const response = await apiClient.get<CategoryVocabularyResponse>(
    `/categories/${category_id}/vocabulary`,
  );
  return response.data;
};

export const updateCategory = async (
  categoryId: string,
  data: UpdateCategoryRequest,
): Promise<UpdateCategoryResponse> => {
  const response = await apiClient.patch<UpdateCategoryResponse>(
    `/categories/${categoryId}`,
    data,
  );
  return response.data;
};

export const deleteCategory = async (categoryId: string): Promise<void> => {
  await apiClient.delete(`/categories/${categoryId}`);
};

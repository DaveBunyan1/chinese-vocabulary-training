import axios from "axios";

/**
 * Shared HTTP client for the Chinese Learning API.
 *
 * baseURL is relative (`/api/v1`) so the same client works in:
 * - Vite dev (proxy → localhost:8000)
 * - Docker/nginx (proxy → backend:8000)
 *
 * Override with VITE_API_BASE_URL only if you intentionally call the API
 * on another origin without a proxy.
 */
const baseURL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(
    /\/$/,
    "",
  ) || "/api/v1";

export const apiClient = axios.create({
  baseURL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30_000,
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (axios.isAxiosError(error)) {
      const status = error.response?.status;
      const detail =
        (error.response?.data as { detail?: unknown } | undefined)?.detail ??
        error.message;
      console.error("[api]", status ?? "network", detail);
    }
    return Promise.reject(error);
  },
);

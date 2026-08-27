import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { LayoutList, RefreshCw, Search } from "lucide-react";

import {
  fetchCategories,
  fetchVocabularyDashboard,
} from "../api/vocabularyDashboard";
import type { VocabularyDashboardItem } from "../types/vocabularyDashboard";

const STATUS_STYLES: Record<string, string> = {
  new: "bg-slate-100 text-slate-700 border-slate-200",
  learning: "bg-amber-50 text-amber-800 border-amber-200",
  known: "bg-emerald-50 text-emerald-800 border-emerald-200",
};

function errorDetail(err: unknown): string {
  const anyErr = err as { response?: { data?: { detail?: string } } };
  return anyErr.response?.data?.detail || "Failed to load vocabulary.";
}

export const VocabularyDashboardView: React.FC = () => {
  const [status, setStatus] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [hskLevel, setHskLevel] = useState("");
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");

  const { data: categoriesData } = useQuery({
    queryKey: ["categories"],
    queryFn: fetchCategories,
  });
  const categories = categoriesData?.categories ?? [];

  const {
    data = null,
    isFetching: loading,
    error: queryError,
    refetch,
  } = useQuery({
    queryKey: ["vocabulary-dashboard", status, categoryId, hskLevel, search],
    queryFn: () =>
      fetchVocabularyDashboard({
        status: status || null,
        category_id: categoryId || null,
        hsk_level: hskLevel ? Number(hskLevel) : null,
        search: search || null,
      }),
  });

  const error = queryError ? errorDetail(queryError) : null;

  const onSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(searchInput.trim());
  };

  const statusCounts = data?.status_counts ?? {};
  const hskCategories = categories.filter((c) => c.type === "hsk");
  const otherCategories = categories.filter((c) => c.type !== "hsk");

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <header className="border-b pb-4">
        <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
          <LayoutList className="text-teal-600" /> Vocabulary
        </h1>
        <p className="text-slate-500 text-sm">
          Browse your words filtered by knowledge status, category, or HSK
          level.
        </p>
      </header>

      <div className="flex flex-wrap gap-2">
        <StatusChip
          label="All"
          count={
            (statusCounts.new ?? 0) +
            (statusCounts.learning ?? 0) +
            (statusCounts.known ?? 0)
          }
          active={status === ""}
          onClick={() => setStatus("")}
        />
        <StatusChip
          label="New"
          count={statusCounts.new ?? 0}
          active={status === "new"}
          onClick={() => setStatus("new")}
        />
        <StatusChip
          label="Learning"
          count={statusCounts.learning ?? 0}
          active={status === "learning"}
          onClick={() => setStatus("learning")}
        />
        <StatusChip
          label="Known"
          count={statusCounts.known ?? 0}
          active={status === "known"}
          onClick={() => setStatus("known")}
        />
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-3">
        <form onSubmit={onSearchSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="search"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search text, pinyin, or meaning..."
              className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-sm font-medium transition"
          >
            Search
          </button>
        </form>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Category
            </label>
            <select
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
            >
              <option value="">Any category</option>
              {otherCategories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.type})
                </option>
              ))}
              {hskCategories.length > 0 && (
                <optgroup label="HSK">
                  {hskCategories.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </optgroup>
              )}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              HSK level
            </label>
            <select
              value={hskLevel}
              onChange={(e) => setHskLevel(e.target.value)}
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
            >
              <option value="">Any level</option>
              {[1, 2, 3, 4, 5, 6, 7].map((n) => (
                <option key={n} value={n}>
                  HSK {n}
                  {n === 7 ? " (7–9)" : ""}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      <div className="flex items-center justify-between text-sm text-slate-500">
        <span>
          {loading
            ? "Loading..."
            : data
              ? `${data.total} word${data.total === 1 ? "" : "s"}`
              : ""}
        </span>
        <button
          type="button"
          onClick={() => void refetch()}
          disabled={loading}
          className="flex items-center gap-1 hover:text-slate-700 disabled:opacity-50"
        >
          <RefreshCw
            className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`}
          />
          Refresh
        </button>
      </div>

      {!loading && data && data.items.length === 0 && (
        <div className="text-center py-12 text-slate-500 text-sm border border-dashed border-slate-300 rounded-xl">
          No vocabulary matches these filters.
          <br />
          Import some text on the Build knowledge tab first.
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {data?.items.map((item) => (
          <VocabCard key={item.vocabulary_id} item={item} />
        ))}
      </div>
    </div>
  );
};

const StatusChip: React.FC<{
  label: string;
  count: number;
  active: boolean;
  onClick: () => void;
}> = ({ label, count, active, onClick }) => (
  <button
    type="button"
    onClick={onClick}
    className={`px-3 py-1.5 rounded-full text-sm border transition ${
      active
        ? "bg-teal-600 text-white border-teal-600"
        : "bg-white text-slate-600 border-slate-200 hover:border-slate-300"
    }`}
  >
    {label}{" "}
    <span className={active ? "opacity-90" : "text-slate-400"}>({count})</span>
  </button>
);

const VocabCard: React.FC<{ item: VocabularyDashboardItem }> = ({ item }) => (
  <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm hover:border-teal-300 transition">
    <div className="flex items-start justify-between gap-2">
      <div>
        <div className="flex items-baseline gap-2">
          <span className="text-xl font-bold text-slate-900">{item.text}</span>
          <span className="text-sm text-teal-700 font-medium">
            {item.pinyin}
          </span>
        </div>
        <p className="text-sm text-slate-600 mt-0.5">{item.meaning}</p>
      </div>
      <span
        className={`shrink-0 text-xs font-medium px-2 py-0.5 rounded-full border ${
          STATUS_STYLES[item.status] ?? STATUS_STYLES.new
        }`}
      >
        {item.status}
      </span>
    </div>

    <div className="mt-3 flex flex-wrap gap-1.5">
      {item.hsk_level != null && (
        <span className="text-xs px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-100">
          HSK {item.hsk_level}
        </span>
      )}
      {item.categories
        .filter((c) => c.type !== "hsk")
        .map((c) => (
          <span
            key={c.id}
            className="text-xs px-2 py-0.5 rounded bg-slate-50 text-slate-600 border border-slate-200"
          >
            {c.name}
          </span>
        ))}
    </div>

    <div className="mt-3 flex gap-4 text-xs text-slate-400">
      <span>✓ {item.successful_recalls}</span>
      <span>✗ {item.failed_recalls}</span>
      <span>seen {item.times_seen}</span>
    </div>
  </div>
);

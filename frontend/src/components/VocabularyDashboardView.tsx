import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { LayoutList, RefreshCw, Search } from "lucide-react";

import {
  fetchCategories,
  fetchVocabularyDashboard,
} from "../api/vocabularyDashboard";
import type { VocabularyDashboardItem } from "../types/vocabularyDashboard";
import { Badge, Button, Card, CardContent, StatusBadge } from "./ui";
import { cn } from "../lib/utils";

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
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <header className="border-b border-border pb-4">
        <h1 className="flex items-center gap-2 text-2xl font-bold text-foreground">
          <LayoutList className="text-primary" /> Vocabulary
        </h1>
        <p className="text-sm text-muted-foreground">
          Browse your words filtered by knowledge status, category, or HSK
          level.
        </p>
      </header>

      <div className="flex flex-wrap gap-2">
        <FilterChip
          label="All"
          count={
            (statusCounts.new ?? 0) +
            (statusCounts.learning ?? 0) +
            (statusCounts.known ?? 0)
          }
          active={status === ""}
          onClick={() => setStatus("")}
        />
        <FilterChip
          label="New"
          count={statusCounts.new ?? 0}
          active={status === "new"}
          onClick={() => setStatus("new")}
        />
        <FilterChip
          label="Learning"
          count={statusCounts.learning ?? 0}
          active={status === "learning"}
          onClick={() => setStatus("learning")}
        />
        <FilterChip
          label="Known"
          count={statusCounts.known ?? 0}
          active={status === "known"}
          onClick={() => setStatus("known")}
        />
      </div>

      <Card>
        <CardContent className="space-y-3">
          <form onSubmit={onSearchSubmit} className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                type="search"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Search text, pinyin, or meaning..."
                className="w-full rounded-lg border border-input bg-background py-2 pl-9 pr-3 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <Button type="submit">Search</Button>
          </form>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-medium text-muted-foreground">
                Category
              </label>
              <select
                value={categoryId}
                onChange={(e) => setCategoryId(e.target.value)}
                className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-ring"
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
              <label className="mb-1 block text-xs font-medium text-muted-foreground">
                HSK level
              </label>
              <select
                value={hskLevel}
                onChange={(e) => setHskLevel(e.target.value)}
                className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-ring"
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
        </CardContent>
      </Card>

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>
          {loading
            ? "Loading..."
            : data
              ? `${data.total} word${data.total === 1 ? "" : "s"}`
              : ""}
        </span>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => void refetch()}
          disabled={loading}
          className="text-muted-foreground"
        >
          <RefreshCw
            className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`}
          />
          Refresh
        </Button>
      </div>

      {!loading && data && data.items.length === 0 && (
        <div className="rounded-xl border border-dashed border-border py-12 text-center text-sm text-muted-foreground">
          No vocabulary matches these filters.
          <br />
          Import some text on the Build knowledge tab first.
        </div>
      )}

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {data?.items.map((item) => (
          <VocabCard key={item.vocabulary_id} item={item} />
        ))}
      </div>
    </div>
  );
};

const FilterChip: React.FC<{
  label: string;
  count: number;
  active: boolean;
  onClick: () => void;
}> = ({ label, count, active, onClick }) => (
  <button
    type="button"
    onClick={onClick}
    className={cn(
      "rounded-full border px-3 py-1.5 text-sm transition",
      active
        ? "border-primary bg-primary text-primary-foreground"
        : "border-border bg-card text-muted-foreground hover:border-primary/40 hover:text-foreground",
    )}
  >
    {label}{" "}
    <span className={active ? "opacity-90" : "text-muted-foreground"}>
      ({count})
    </span>
  </button>
);

const VocabCard: React.FC<{ item: VocabularyDashboardItem }> = ({ item }) => (
  <Card className="transition hover:border-primary/40">
    <CardContent>
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="flex items-baseline gap-2">
            <span className="text-xl font-bold text-foreground">
              {item.text}
            </span>
            <span className="text-sm font-medium text-primary">
              {item.pinyin}
            </span>
          </div>
          <p className="mt-0.5 text-sm text-muted-foreground">{item.meaning}</p>
        </div>
        <StatusBadge status={item.status} />
      </div>

      <div className="mt-3 flex flex-wrap gap-1.5">
        {item.hsk_level != null && (
          <Badge variant="secondary">HSK {item.hsk_level}</Badge>
        )}
        {item.categories
          .filter((c) => c.type !== "hsk")
          .map((c) => (
            <Badge key={c.id} variant="outline">
              {c.name}
            </Badge>
          ))}
      </div>

      <div className="mt-3 flex gap-4 text-xs text-muted-foreground">
        <span>✓ {item.successful_recalls}</span>
        <span>✗ {item.failed_recalls}</span>
        <span>seen {item.times_seen}</span>
      </div>
    </CardContent>
  </Card>
);

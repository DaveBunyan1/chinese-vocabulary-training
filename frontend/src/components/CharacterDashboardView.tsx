import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Languages, RefreshCw, Search } from "lucide-react";

import { fetchCharacterDashboard } from "../api/characterDashboard";
import type { CharacterDashboardItem } from "../types/characterDashboard";
import { Button, Card, CardContent, StatusBadge } from "./ui";
import FilterChip from "./ui/FilterChip";

function errorDetail(err: unknown): string {
  const anyErr = err as { response?: { data?: { detail?: string } } };
  return anyErr.response?.data?.detail || "Failed to load characters.";
}

export const CharacterDashboardView: React.FC = () => {
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");

  const {
    data = null,
    isFetching: loading,
    error: queryError,
    refetch,
  } = useQuery({
    queryKey: ["character-dashboard", status, search],
    queryFn: () =>
      fetchCharacterDashboard({
        status: status || null,
        search: search || null,
      }),
  });

  const error = queryError ? errorDetail(queryError) : null;

  const onSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(searchInput.trim());
  };

  const statusCounts = data?.status_counts ?? {};

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <header className="border-b border-border pb-4">
        <h1 className="flex items-center gap-2 text-2xl font-bold text-foreground">
          <Languages className="text-primary" /> Characters
        </h1>
        <p className="text-sm text-muted-foreground">
          Browse characters from your knowledge profile, filtered by status.
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
        <CardContent>
          <form onSubmit={onSearchSubmit} className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                type="search"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Search character, pinyin, or meaning..."
                className="w-full rounded-lg border border-input bg-background py-2 pl-9 pr-3 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <Button type="submit">Search</Button>
          </form>
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
              ? `${data.total} character${data.total === 1 ? "" : "s"}`
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
          No characters match these filters.
          <br />
          Import some text on the Build knowledge tab first.
        </div>
      )}

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
        {data?.items.map((item) => (
          <CharCard key={item.character} item={item} />
        ))}
      </div>
    </div>
  );
};

const CharCard: React.FC<{ item: CharacterDashboardItem }> = ({ item }) => (
  <Card className="text-center transition hover:border-primary/40">
    <CardContent>
      <div className="mb-1 flex justify-end">
        <StatusBadge status={item.status} />
      </div>
      <p className="text-4xl font-bold leading-none text-foreground">
        {item.character}
      </p>
      <p className="mt-2 text-sm font-medium text-primary">{item.pinyin}</p>
      <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">
        {item.meaning}
      </p>
      <div className="mt-3 flex justify-center gap-3 text-xs text-muted-foreground">
        <span>✓ {item.successful_recognitions}</span>
        <span>✗ {item.failed_recognitions}</span>
        <span>seen {item.times_seen}</span>
      </div>
    </CardContent>
  </Card>
);

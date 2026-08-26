import React, { useCallback, useEffect, useState } from "react";
import { Languages, RefreshCw, Search } from "lucide-react";

import { fetchCharacterDashboard } from "../api/characterDashboard";
import type {
  CharacterDashboardItem,
  CharacterDashboardResponse,
} from "../types/characterDashboard";

const STATUS_STYLES: Record<string, string> = {
  new: "bg-slate-100 text-slate-700 border-slate-200",
  learning: "bg-amber-50 text-amber-800 border-amber-200",
  known: "bg-emerald-50 text-emerald-800 border-emerald-200",
};

function errorDetail(err: unknown): string {
  const anyErr = err as { response?: { data?: { detail?: string } } };
  return anyErr.response?.data?.detail || "Failed to load characters.";
}

export const CharacterDashboardView: React.FC = () => {
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");

  const [data, setData] = useState<CharacterDashboardResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchCharacterDashboard({
        status: status || null,
        search: search || null,
      });
      setData(result);
    } catch (err) {
      setError(errorDetail(err));
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [status, search]);

  useEffect(() => {
    void load();
  }, [load]);

  const onSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(searchInput.trim());
  };

  const statusCounts = data?.status_counts ?? {};

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <header className="border-b pb-4">
        <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
          <Languages className="text-violet-600" /> Characters
        </h1>
        <p className="text-slate-500 text-sm">
          Browse characters from your knowledge profile, filtered by status.
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

      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
        <form onSubmit={onSearchSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="search"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search character, pinyin, or meaning..."
              className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-violet-500"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-lg text-sm font-medium transition"
          >
            Search
          </button>
        </form>
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
              ? `${data.total} character${data.total === 1 ? "" : "s"}`
              : ""}
        </span>
        <button
          type="button"
          onClick={() => void load()}
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
          No characters match these filters.
          <br />
          Import some text on the Build knowledge tab first.
        </div>
      )}

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
        {data?.items.map((item) => (
          <CharCard key={item.character} item={item} />
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
        ? "bg-violet-600 text-white border-violet-600"
        : "bg-white text-slate-600 border-slate-200 hover:border-slate-300"
    }`}
  >
    {label}{" "}
    <span className={active ? "opacity-90" : "text-slate-400"}>({count})</span>
  </button>
);

const CharCard: React.FC<{ item: CharacterDashboardItem }> = ({ item }) => (
  <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm hover:border-violet-300 transition text-center">
    <div className="flex justify-end mb-1">
      <span
        className={`text-xs font-medium px-2 py-0.5 rounded-full border ${
          STATUS_STYLES[item.status] ?? STATUS_STYLES.new
        }`}
      >
        {item.status}
      </span>
    </div>
    <p className="text-4xl font-bold text-slate-900 leading-none">
      {item.character}
    </p>
    <p className="text-sm text-violet-700 font-medium mt-2">{item.pinyin}</p>
    <p className="text-xs text-slate-600 mt-1 line-clamp-2">{item.meaning}</p>
    <div className="mt-3 flex justify-center gap-3 text-xs text-slate-400">
      <span>✓ {item.successful_recognitions}</span>
      <span>✗ {item.failed_recognitions}</span>
      <span>seen {item.times_seen}</span>
    </div>
  </div>
);

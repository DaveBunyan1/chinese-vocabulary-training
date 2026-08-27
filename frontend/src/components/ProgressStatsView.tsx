import React from "react";
import { useQuery } from "@tanstack/react-query";
import { BarChart3, RefreshCw } from "lucide-react";

import { fetchProgressStats } from "../api/progress";
import type { StatusBreakdown } from "../types/progress";

function errorDetail(err: unknown): string {
  const anyErr = err as { response?: { data?: { detail?: string } } };
  return anyErr.response?.data?.detail || "Failed to load progress.";
}

export const ProgressStatsView: React.FC = () => {
  const {
    data = null,
    isFetching: loading,
    error: queryError,
    refetch,
  } = useQuery({
    queryKey: ["progress-stats"],
    queryFn: fetchProgressStats,
  });

  const error = queryError ? errorDetail(queryError) : null;

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <header className="border-b pb-4 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <BarChart3 className="text-sky-600" /> Progress
          </h1>
          <p className="text-slate-500 text-sm">
            Snapshot derived from your vocabulary and character knowledge
            records.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void refetch()}
          disabled={loading}
          className="text-sm text-slate-500 hover:text-slate-700 flex items-center gap-1"
        >
          <RefreshCw
            className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`}
          />
          Refresh
        </button>
      </header>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      {loading && !data && (
        <p className="text-sm text-slate-400 text-center py-12">Loading...</p>
      )}

      {data && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Section
            title="Vocabulary"
            status={data.vocabulary.by_status}
            metrics={[
              {
                label: "Correct recalls",
                value: data.vocabulary.total_successful_recalls,
              },
              {
                label: "Incorrect recalls",
                value: data.vocabulary.total_failed_recalls,
              },
              {
                label: "Times seen",
                value: data.vocabulary.total_times_seen,
              },
              {
                label: "Items practised",
                value: data.vocabulary.items_practised,
              },
            ]}
          />
          <Section
            title="Characters"
            status={data.characters.by_status}
            metrics={[
              {
                label: "Correct recognitions",
                value: data.characters.total_successful_recognitions,
              },
              {
                label: "Incorrect recognitions",
                value: data.characters.total_failed_recognitions,
              },
              {
                label: "Times seen",
                value: data.characters.total_times_seen,
              },
              {
                label: "Items practised",
                value: data.characters.items_practised,
              },
            ]}
          />
        </div>
      )}
    </div>
  );
};

const Section: React.FC<{
  title: string;
  status: StatusBreakdown;
  metrics: { label: string; value: number }[];
}> = ({ title, status, metrics }) => {
  const total = status.total || 1;
  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-5 space-y-5">
      <div className="flex items-baseline justify-between">
        <h2 className="text-lg font-semibold text-slate-800">{title}</h2>
        <span className="text-sm text-slate-500">{status.total} total</span>
      </div>

      <div className="h-3 rounded-full overflow-hidden flex bg-slate-100">
        {status.new > 0 && (
          <div
            className="bg-slate-400"
            style={{ width: `${(status.new / total) * 100}%` }}
            title={`New: ${status.new}`}
          />
        )}
        {status.learning > 0 && (
          <div
            className="bg-amber-400"
            style={{ width: `${(status.learning / total) * 100}%` }}
            title={`Learning: ${status.learning}`}
          />
        )}
        {status.known > 0 && (
          <div
            className="bg-emerald-500"
            style={{ width: `${(status.known / total) * 100}%` }}
            title={`Known: ${status.known}`}
          />
        )}
      </div>

      <div className="grid grid-cols-3 gap-2 text-center text-sm">
        <Stat label="New" value={status.new} color="text-slate-600" />
        <Stat label="Learning" value={status.learning} color="text-amber-700" />
        <Stat label="Known" value={status.known} color="text-emerald-700" />
      </div>

      <div className="grid grid-cols-2 gap-3 pt-2 border-t">
        {metrics.map((m) => (
          <div key={m.label} className="bg-slate-50 rounded-lg p-3 text-center">
            <span className="block text-xl font-bold text-slate-800">
              {m.value}
            </span>
            <span className="text-xs text-slate-500">{m.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const Stat: React.FC<{ label: string; value: number; color: string }> = ({
  label,
  value,
  color,
}) => (
  <div>
    <span className={`block text-lg font-bold ${color}`}>{value}</span>
    <span className="text-xs text-slate-500">{label}</span>
  </div>
);

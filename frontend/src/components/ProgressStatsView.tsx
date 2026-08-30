import React from "react";
import { useQuery } from "@tanstack/react-query";
import { BarChart3, RefreshCw } from "lucide-react";

import { fetchProgressStats } from "../api/progress";
import type { StatusBreakdown } from "../types/progress";
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  StatusBadge,
} from "./ui";

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
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <header className="flex items-start justify-between gap-4 border-b border-border pb-4">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold text-foreground">
            <BarChart3 className="text-primary" /> Progress
          </h1>
          <p className="text-sm text-muted-foreground">
            Snapshot derived from your vocabulary and character knowledge
            records.
          </p>
        </div>
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
      </header>

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      {loading && !data && (
        <p className="py-12 text-center text-sm text-muted-foreground">
          Loading...
        </p>
      )}

      {data && (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
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
    <Card>
      <CardHeader className="flex-row items-baseline justify-between space-y-0">
        <CardTitle>{title}</CardTitle>
        <span className="text-sm text-muted-foreground">
          {status.total} total
        </span>
      </CardHeader>

      <CardContent className="space-y-5">
        <div className="flex h-3 overflow-hidden rounded-full bg-muted">
          {status.new > 0 && (
            <div
              className="bg-status-new"
              style={{ width: `${(status.new / total) * 100}%` }}
              title={`New: ${status.new}`}
            />
          )}
          {status.learning > 0 && (
            <div
              className="bg-status-learning"
              style={{ width: `${(status.learning / total) * 100}%` }}
              title={`Learning: ${status.learning}`}
            />
          )}
          {status.known > 0 && (
            <div
              className="bg-status-known"
              style={{ width: `${(status.known / total) * 100}%` }}
              title={`Known: ${status.known}`}
            />
          )}
        </div>

        <div className="grid grid-cols-3 gap-2 text-center text-sm">
          <StatusStat status="new" value={status.new} />
          <StatusStat status="learning" value={status.learning} />
          <StatusStat status="known" value={status.known} />
        </div>

        <div className="grid grid-cols-2 gap-3 border-t border-border pt-4">
          {metrics.map((m) => (
            <div key={m.label} className="rounded-lg bg-muted p-3 text-center">
              <span className="block text-xl font-bold text-foreground">
                {m.value}
              </span>
              <span className="text-xs text-muted-foreground">{m.label}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

const StatusStat: React.FC<{ status: string; value: number }> = ({
  status,
  value,
}) => (
  <div className="flex flex-col items-center gap-1">
    <span className="text-lg font-bold text-foreground">{value}</span>
    <StatusBadge status={status} />
  </div>
);

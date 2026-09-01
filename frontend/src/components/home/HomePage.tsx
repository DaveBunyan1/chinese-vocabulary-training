import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  BookOpen,
  Brain,
  Sparkles,
  TrendingUp,
  Clock,
  Layers,
} from "lucide-react";

import { fetchProgressStats } from "../../api/progress";
import type { StatusBreakdown } from "../../types/progress";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  StatusBadge,
} from "../ui";
import PlaceholderTag from "../ui/PlaceholderTag";

function errorDetail(err: unknown): string {
  const anyErr = err as { response?: { data?: { detail?: string } } };
  return anyErr.response?.data?.detail || "Failed to load progress.";
}

export function HomePage() {
  const {
    data,
    isFetching: loading,
    error: queryError,
  } = useQuery({
    queryKey: ["progress-stats"],
    queryFn: fetchProgressStats,
  });

  const error = queryError ? errorDetail(queryError) : null;

  return (
    <div className="mx-auto max-w-5xl space-y-8 p-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-bold text-foreground">Home</h1>
        <p className="text-sm text-muted-foreground">
          Snapshot of your Chinese learning progress. Some panels are
          placeholders until more backend support lands.
        </p>
      </header>

      {/* Quick actions */}
      <div className="flex flex-wrap gap-2">
        <Link to="/practice">
          <Button type="button">
            <Brain className="h-4 w-4" /> Practice
          </Button>
        </Link>
        <Link to="/review">
          <Button type="button" variant="secondary">
            <Sparkles className="h-4 w-4" /> Smart review
          </Button>
        </Link>
        <Link to="/import">
          <Button type="button" variant="secondary">
            <BookOpen className="h-4 w-4" /> Import text
          </Button>
        </Link>
      </div>

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      {loading && !data && (
        <p className="py-8 text-center text-sm text-muted-foreground">
          Loading progress…
        </p>
      )}

      {/* Wired: overall knowledge */}
      {data && (
        <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <KnowledgeCard
            title="Vocabulary"
            status={data.vocabulary.by_status}
          />
          <KnowledgeCard
            title="Characters"
            status={data.characters.by_status}
          />
        </section>
      )}

      {/* Placeholders */}
      <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <PlaceholderCard
          icon={<Layers className="h-4 w-4 text-primary" />}
          title="HSK breakdown"
          description="Known / learning / new per HSK level, filterable by category."
          kind="unwired"
        />
        <PlaceholderCard
          icon={<TrendingUp className="h-4 w-4 text-primary" />}
          title="Status trends"
          description="New → learning → known transitions over the last 7 / 30 days."
          kind="unwired"
        />
        <PlaceholderCard
          icon={<Clock className="h-4 w-4 text-primary" />}
          title="Last practice session"
          description="Date, mode, score, and items reviewed."
          kind="unwired"
        />
        <PlaceholderCard
          icon={<BookOpen className="h-4 w-4 text-primary" />}
          title="Recent activity"
          description="Imports, reviews, and status promotions."
          kind="coming_soon"
        />
      </section>
    </div>
  );
}

function KnowledgeCard({
  title,
  status,
}: {
  title: string;
  status: StatusBreakdown;
}) {
  const total = status.total || 1;

  return (
    <Card>
      <CardHeader className="flex-row items-baseline justify-between space-y-0">
        <CardTitle className="text-base">{title}</CardTitle>
        <span className="text-sm text-muted-foreground">
          {status.total} total
        </span>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex h-2.5 overflow-hidden rounded-full bg-muted">
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
        <div className="flex flex-wrap justify-center gap-3">
          <div className="flex flex-col items-center gap-1">
            <span className="text-lg font-bold">{status.new}</span>
            <StatusBadge status="new" />
          </div>
          <div className="flex flex-col items-center gap-1">
            <span className="text-lg font-bold">{status.learning}</span>
            <StatusBadge status="learning" />
          </div>
          <div className="flex flex-col items-center gap-1">
            <span className="text-lg font-bold">{status.known}</span>
            <StatusBadge status="known" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function PlaceholderCard({
  icon,
  title,
  description,
  kind,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  kind: "placeholder" | "unwired" | "coming_soon";
}) {
  return (
    <Card className="border-dashed">
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="flex items-center gap-2 text-base">
            {icon}
            {title}
          </CardTitle>
          <PlaceholderTag kind={kind} />
        </div>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex h-20 items-center justify-center rounded-lg bg-muted/40 text-xs text-muted-foreground">
          Data will appear here when wired
        </div>
      </CardContent>
    </Card>
  );
}

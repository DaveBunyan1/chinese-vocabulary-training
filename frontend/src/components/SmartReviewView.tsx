import React, { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  CheckCircle,
  ChevronRight,
  RefreshCw,
  Sparkles,
  XCircle,
} from "lucide-react";

import { fetchReviewQueue } from "../api/reviewQueue";
import {
  generateCharacterRecognition,
  generateVocabularyRecall,
  submitAnswer,
} from "../api/practice";
import type {
  Exercise,
  Question,
  SubmitAnswerResponse,
} from "../types/practice";
import type { ReviewQueueItem } from "../types/reviewQueue";
import { expandAcceptedTerms, formatAnswerForDisplay } from "../lib/pinyin";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  StatusBadge,
} from "./ui";
import { cn } from "../lib/utils";

type Phase = "queue" | "active" | "summary";

interface AnswerRecord {
  question: Question;
  response: SubmitAnswerResponse;
}

function errorDetail(err: unknown): string {
  const anyErr = err as { response?: { data?: { detail?: string } } };
  const detail = anyErr.response?.data?.detail;
  if (typeof detail === "string") return detail;
  return "Something went wrong.";
}

const fieldClassName =
  "w-full rounded-lg border border-input bg-background px-4 py-3 text-center text-xl text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-ring";

export const SmartReviewView: React.FC = () => {
  const [includeUnscheduled, setIncludeUnscheduled] = useState(true);
  const [includeVocab, setIncludeVocab] = useState(true);
  const [includeChars, setIncludeChars] = useState(true);

  const [phase, setPhase] = useState<Phase>("queue");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [exercise, setExercise] = useState<Exercise | null>(null);
  const [index, setIndex] = useState(0);
  const [answer, setAnswer] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<SubmitAnswerResponse | null>(null);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [history, setHistory] = useState<AnswerRecord[]>([]);

  const currentQuestion: Question | null = useMemo(() => {
    if (!exercise) return null;
    return exercise.questions[index] ?? null;
  }, [exercise, index]);

  const {
    data: queue = null,
    isFetching: queueLoading,
    error: queueError,
    refetch: loadQueue,
  } = useQuery({
    queryKey: ["review-queue", includeVocab, includeChars, includeUnscheduled],
    queryFn: () =>
      fetchReviewQueue({
        limit: 50,
        include_vocabulary: includeVocab,
        include_characters: includeChars,
        include_unscheduled: includeUnscheduled,
      }),
  });

  const startVocabularyReview = async () => {
    if (!queue) return;
    const n =
      queue.due_vocabulary_count +
      (includeUnscheduled ? queue.unscheduled_vocabulary_count : 0);
    const count = Math.min(Math.max(n, 1), 20);

    setLoading(true);
    setError(null);
    try {
      const data = await generateVocabularyRecall({
        count,
        knowledge_status: null,
        direction: "meaning_to_hanzi",
      });
      setExercise(data);
      setIndex(0);
      setAnswer("");
      setFeedback(null);
      setHistory([]);
      setStartedAt(Date.now());
      setPhase("active");
    } catch (err) {
      setError(errorDetail(err));
    } finally {
      setLoading(false);
    }
  };

  const startCharacterReview = async () => {
    if (!queue) return;
    const n =
      queue.due_character_count +
      (includeUnscheduled ? queue.unscheduled_character_count : 0);
    const count = Math.min(Math.max(n, 1), 20);

    setLoading(true);
    setError(null);
    try {
      const data = await generateCharacterRecognition({
        count,
        knowledge_status: null,
        direction: "character_to_meaning",
      });
      setExercise(data);
      setIndex(0);
      setAnswer("");
      setFeedback(null);
      setHistory([]);
      setStartedAt(Date.now());
      setPhase("active");
    } catch (err) {
      setError(errorDetail(err));
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitAnswer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!exercise || !currentQuestion || submitting || feedback) return;

    setSubmitting(true);
    setError(null);
    const elapsed =
      startedAt != null ? Math.max(0, Date.now() - startedAt) : undefined;

    try {
      const response = await submitAnswer({
        exercise_id: exercise.id,
        question_id: currentQuestion.id,
        question_type: currentQuestion.type,
        raw_answer: answer,
        correct_answers: currentQuestion.correct_answers,
        vocabulary_id: currentQuestion.vocabulary_id,
        character: currentQuestion.character,
        response_time_ms: elapsed,
      });
      setFeedback(response);
      setHistory((prev) => [...prev, { question: currentQuestion, response }]);
    } catch (err) {
      setError(errorDetail(err));
    } finally {
      setSubmitting(false);
    }
  };

  const goNext = () => {
    if (!exercise) return;
    const next = index + 1;
    if (next >= exercise.question_count) {
      setPhase("summary");
      void loadQueue();
      return;
    }
    setIndex(next);
    setAnswer("");
    setFeedback(null);
    setStartedAt(Date.now());
    setError(null);
  };

  const backToQueue = () => {
    setPhase("queue");
    setExercise(null);
    setIndex(0);
    setAnswer("");
    setFeedback(null);
    setHistory([]);
    void loadQueue();
  };

  const correctCount = history.filter((h) => h.response.is_correct).length;
  const vocabItems = queue?.items.filter((i) => i.kind === "vocabulary") ?? [];
  const charItems = queue?.items.filter((i) => i.kind === "character") ?? [];

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      <header className="border-b border-border pb-4">
        <h1 className="flex items-center gap-2 text-2xl font-bold text-foreground">
          <Sparkles className="text-primary" /> Smart review
        </h1>
        <p className="text-sm text-muted-foreground">
          Prioritised items from your knowledge profile (due + unscheduled).
        </p>
      </header>

      {(error || queueError) && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
          {error ?? errorDetail(queueError)}
        </div>
      )}

      {phase === "queue" && (
        <div className="space-y-5">
          <div className="flex flex-wrap items-center gap-3 text-sm">
            <label className="flex items-center gap-1.5 text-muted-foreground">
              <input
                type="checkbox"
                checked={includeVocab}
                onChange={(e) => setIncludeVocab(e.target.checked)}
                className="rounded border-input"
              />
              Vocabulary
            </label>
            <label className="flex items-center gap-1.5 text-muted-foreground">
              <input
                type="checkbox"
                checked={includeChars}
                onChange={(e) => setIncludeChars(e.target.checked)}
                className="rounded border-input"
              />
              Characters
            </label>
            <label className="flex items-center gap-1.5 text-muted-foreground">
              <input
                type="checkbox"
                checked={includeUnscheduled}
                onChange={(e) => setIncludeUnscheduled(e.target.checked)}
                className="rounded border-input"
              />
              Include unscheduled
            </label>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => void loadQueue()}
              disabled={loading || queueLoading}
              className="ml-auto text-muted-foreground"
            >
              <RefreshCw
                className={`h-3.5 w-3.5 ${loading || queueLoading ? "animate-spin" : ""}`}
              />
              Refresh
            </Button>
          </div>

          {queue && (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <StatCard label="Due vocab" value={queue.due_vocabulary_count} />
              <StatCard label="Due chars" value={queue.due_character_count} />
              <StatCard
                label="Unsched. vocab"
                value={queue.unscheduled_vocabulary_count}
                muted
              />
              <StatCard
                label="Unsched. chars"
                value={queue.unscheduled_character_count}
                muted
              />
            </div>
          )}

          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              onClick={() => void startVocabularyReview()}
              disabled={loading || !queue || !includeVocab}
            >
              Review vocabulary <ChevronRight className="h-4 w-4" />
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => void startCharacterReview()}
              disabled={loading || !queue || !includeChars}
            >
              Review characters <ChevronRight className="h-4 w-4" />
            </Button>
          </div>

          {!loading && !queueLoading && queue && queue.items.length === 0 && (
            <div className="rounded-xl border border-dashed border-border py-12 text-center text-sm text-muted-foreground">
              Nothing in the review queue right now.
              <br />
              Import text or practise so items become due / unscheduled.
            </div>
          )}

          <div className="space-y-4">
            {vocabItems.length > 0 && (
              <QueueSection title="Vocabulary" items={vocabItems} />
            )}
            {charItems.length > 0 && (
              <QueueSection title="Characters" items={charItems} />
            )}
          </div>
        </div>
      )}

      {phase === "active" && exercise && currentQuestion && (
        <div className="space-y-5">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>
              {exercise.type === "vocabulary_recall"
                ? "Vocabulary review"
                : "Character review"}
            </span>
            <span className="font-medium text-foreground">
              {Math.min(index + 1, exercise.question_count)} /{" "}
              {exercise.question_count}
            </span>
          </div>

          <Card>
            <CardContent className="space-y-6 p-8 text-center">
              <p className="text-sm uppercase tracking-wide text-muted-foreground">
                Prompt
              </p>
              <p className="wrap-break-word text-4xl font-bold text-foreground">
                {currentQuestion.prompt}
              </p>

              {!feedback ? (
                <form onSubmit={handleSubmitAnswer} className="space-y-4">
                  <input
                    type="text"
                    autoFocus
                    value={answer}
                    onChange={(e) => setAnswer(e.target.value)}
                    placeholder="Your answer (pinyin: ni3 or nǐ)..."
                    className={fieldClassName}
                  />
                  <Button
                    type="submit"
                    disabled={submitting || !answer.trim()}
                    className="w-full"
                  >
                    {submitting ? "Checking..." : "Check answer"}
                  </Button>
                </form>
              ) : (
                <div className="space-y-4">
                  <div
                    className={cn(
                      "flex items-start gap-3 rounded-lg border p-4 text-left",
                      feedback.is_correct
                        ? "border-success/30 bg-success/10 text-success"
                        : "border-destructive/30 bg-destructive/10 text-destructive",
                    )}
                  >
                    {feedback.is_correct ? (
                      <CheckCircle className="mt-0.5 h-5 w-5 shrink-0" />
                    ) : (
                      <XCircle className="mt-0.5 h-5 w-5 shrink-0" />
                    )}
                    <div>
                      <p className="font-semibold">
                        {feedback.is_correct ? "Correct!" : "Not quite"}
                      </p>
                      {!feedback.is_correct && currentQuestion && (
                        <>
                          <p className="mt-1 text-sm">
                            You answered:{" "}
                            <span className="font-medium">
                              {feedback.raw_answer || "—"}
                            </span>
                          </p>
                          <p className="text-sm">
                            Expected:{" "}
                            <span className="font-medium">
                              {currentQuestion.correct_answers
                                .map(formatAnswerForDisplay)
                                .join(" · ")}
                            </span>
                          </p>
                          {expandAcceptedTerms(currentQuestion.correct_answers)
                            .length > 1 && (
                            <p className="text-sm opacity-90">
                              Any of these also count:{" "}
                              {expandAcceptedTerms(
                                currentQuestion.correct_answers,
                              )
                                .map(formatAnswerForDisplay)
                                .join(", ")}
                            </p>
                          )}
                        </>
                      )}
                      {feedback.new_status && (
                        <p className="mt-1 text-sm opacity-80">
                          Status: {feedback.previous_status ?? "—"} →{" "}
                          {feedback.new_status}
                        </p>
                      )}
                    </div>
                  </div>
                  <Button type="button" onClick={goNext} className="w-full">
                    {index + 1 >= exercise.question_count
                      ? "See summary"
                      : "Next"}
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          <div className="flex justify-center">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={backToQueue}
              className="text-muted-foreground"
            >
              Back to queue
            </Button>
          </div>
        </div>
      )}

      {phase === "summary" && exercise && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-success" /> Review complete
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="rounded-lg border border-border bg-muted/50 p-3">
                <span className="block text-2xl font-bold text-foreground">
                  {exercise.question_count}
                </span>
                <span className="text-xs text-muted-foreground">Questions</span>
              </div>
              <div className="rounded-lg border border-border bg-muted/50 p-3">
                <span className="block text-2xl font-bold text-success">
                  {correctCount}
                </span>
                <span className="text-xs text-muted-foreground">Correct</span>
              </div>
              <div className="rounded-lg border border-border bg-muted/50 p-3">
                <span className="block text-2xl font-bold text-destructive">
                  {history.length - correctCount}
                </span>
                <span className="text-xs text-muted-foreground">Incorrect</span>
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="secondary" onClick={backToQueue}>
                Back to queue
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

const StatCard: React.FC<{
  label: string;
  value: number;
  muted?: boolean;
}> = ({ label, value, muted }) => (
  <div
    className={cn(
      "rounded-xl border p-3 text-center",
      muted
        ? "border-border bg-muted/50 text-muted-foreground"
        : "border-primary/20 bg-primary/10 text-foreground",
    )}
  >
    <span className="block text-2xl font-bold">{value}</span>
    <span className="text-xs opacity-80">{label}</span>
  </div>
);

const QueueSection: React.FC<{
  title: string;
  items: ReviewQueueItem[];
}> = ({ title, items }) => (
  <Card className="overflow-hidden p-0">
    <div className="border-b border-border bg-muted/50 px-4 py-2 text-sm font-semibold text-foreground">
      {title} ({items.length})
    </div>
    <ul className="max-h-64 divide-y divide-border overflow-y-auto">
      {items.map((item, i) => (
        <li
          key={`${item.kind}-${item.vocabulary_id ?? item.character}-${i}`}
          className="flex items-center justify-between gap-3 px-4 py-2.5 text-sm"
        >
          <div className="min-w-0">
            <p className="truncate font-medium text-foreground">
              {item.kind === "vocabulary"
                ? `${item.text} · ${item.pinyin}`
                : item.character}
            </p>
            {item.kind === "vocabulary" && item.meaning && (
              <p className="truncate text-xs text-muted-foreground">
                {item.meaning}
              </p>
            )}
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <Badge variant={item.reason === "due" ? "primary" : "outline"}>
              {item.reason}
            </Badge>
            <StatusBadge status={item.status} />
          </div>
        </li>
      ))}
    </ul>
  </Card>
);

import React, { useCallback, useEffect, useMemo, useState } from "react";
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
import type {
  ReviewQueueItem,
  ReviewQueueResponse,
} from "../types/reviewQueue";

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

export const SmartReviewView: React.FC = () => {
  const [queue, setQueue] = useState<ReviewQueueResponse | null>(null);
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

  const loadQueue = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchReviewQueue({
        limit: 50,
        include_vocabulary: includeVocab,
        include_characters: includeChars,
        include_unscheduled: includeUnscheduled,
      });
      setQueue(data);
    } catch (err) {
      setError(errorDetail(err));
      setQueue(null);
    } finally {
      setLoading(false);
    }
  }, [includeVocab, includeChars, includeUnscheduled]);

  useEffect(() => {
    void loadQueue();
  }, [loadQueue]);

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
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      <header className="border-b pb-4">
        <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
          <Sparkles className="text-fuchsia-600" /> Smart review
        </h1>
        <p className="text-slate-500 text-sm">
          Prioritised items from your knowledge profile (due + unscheduled).
        </p>
      </header>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      {phase === "queue" && (
        <div className="space-y-5">
          <div className="flex flex-wrap gap-3 items-center text-sm">
            <label className="flex items-center gap-1.5 text-slate-600">
              <input
                type="checkbox"
                checked={includeVocab}
                onChange={(e) => setIncludeVocab(e.target.checked)}
              />
              Vocabulary
            </label>
            <label className="flex items-center gap-1.5 text-slate-600">
              <input
                type="checkbox"
                checked={includeChars}
                onChange={(e) => setIncludeChars(e.target.checked)}
              />
              Characters
            </label>
            <label className="flex items-center gap-1.5 text-slate-600">
              <input
                type="checkbox"
                checked={includeUnscheduled}
                onChange={(e) => setIncludeUnscheduled(e.target.checked)}
              />
              Include unscheduled
            </label>
            <button
              type="button"
              onClick={() => void loadQueue()}
              disabled={loading}
              className="ml-auto flex items-center gap-1 text-slate-500 hover:text-slate-700"
            >
              <RefreshCw
                className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`}
              />
              Refresh
            </button>
          </div>

          {queue && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <StatCard
                label="Due vocab"
                value={queue.due_vocabulary_count}
                tone="fuchsia"
              />
              <StatCard
                label="Due chars"
                value={queue.due_character_count}
                tone="violet"
              />
              <StatCard
                label="Unsched. vocab"
                value={queue.unscheduled_vocabulary_count}
                tone="slate"
              />
              <StatCard
                label="Unsched. chars"
                value={queue.unscheduled_character_count}
                tone="slate"
              />
            </div>
          )}

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => void startVocabularyReview()}
              disabled={loading || !queue || !includeVocab}
              className="flex items-center gap-2 bg-fuchsia-600 hover:bg-fuchsia-700 disabled:opacity-50 text-white font-medium px-4 py-2.5 rounded-lg transition"
            >
              Review vocabulary <ChevronRight className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={() => void startCharacterReview()}
              disabled={loading || !queue || !includeChars}
              className="flex items-center gap-2 bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white font-medium px-4 py-2.5 rounded-lg transition"
            >
              Review characters <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {!loading && queue && queue.items.length === 0 && (
            <div className="text-center py-12 text-slate-500 text-sm border border-dashed border-slate-300 rounded-xl">
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
          <div className="flex items-center justify-between text-sm text-slate-500">
            <span>
              {exercise.type === "vocabulary_recall"
                ? "Vocabulary review"
                : "Character review"}
            </span>
            <span className="font-medium text-slate-700">
              {Math.min(index + 1, exercise.question_count)} /{" "}
              {exercise.question_count}
            </span>
          </div>

          <div className="bg-white p-8 rounded-xl border border-slate-200 shadow-sm text-center space-y-6">
            <p className="text-sm uppercase tracking-wide text-slate-400">
              Prompt
            </p>
            <p className="text-4xl font-bold text-slate-900 wrap-break-word">
              {currentQuestion.prompt}
            </p>

            {!feedback ? (
              <form onSubmit={handleSubmitAnswer} className="space-y-4">
                <input
                  type="text"
                  autoFocus
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  placeholder="Type your answer..."
                  className="w-full text-center text-xl border border-slate-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-fuchsia-500 focus:border-fuchsia-500"
                />
                <button
                  type="submit"
                  disabled={submitting || !answer.trim()}
                  className="w-full bg-fuchsia-600 hover:bg-fuchsia-700 disabled:opacity-50 text-white font-medium py-2.5 rounded-lg transition"
                >
                  {submitting ? "Checking..." : "Check answer"}
                </button>
              </form>
            ) : (
              <div className="space-y-4">
                <div
                  className={`p-4 rounded-lg border flex items-start gap-3 text-left ${
                    feedback.is_correct
                      ? "bg-emerald-50 border-emerald-200 text-emerald-800"
                      : "bg-red-50 border-red-200 text-red-800"
                  }`}
                >
                  {feedback.is_correct ? (
                    <CheckCircle className="w-5 h-5 mt-0.5 shrink-0" />
                  ) : (
                    <XCircle className="w-5 h-5 mt-0.5 shrink-0" />
                  )}
                  <div>
                    <p className="font-semibold">
                      {feedback.is_correct ? "Correct" : "Incorrect"}
                    </p>
                    {!feedback.is_correct && (
                      <p className="text-sm mt-1">
                        Expected:{" "}
                        <span className="font-medium">
                          {currentQuestion.correct_answers.join(" / ")}
                        </span>
                      </p>
                    )}
                    {feedback.new_status && (
                      <p className="text-sm mt-1 opacity-80">
                        Status: {feedback.previous_status ?? "—"} →{" "}
                        {feedback.new_status}
                      </p>
                    )}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={goNext}
                  className="w-full flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-900 text-white font-medium py-2.5 rounded-lg transition"
                >
                  {index + 1 >= exercise.question_count
                    ? "See summary"
                    : "Next"}
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>

          <div className="flex justify-center">
            <button
              type="button"
              onClick={backToQueue}
              className="text-sm text-slate-500 hover:text-slate-700"
            >
              Back to queue
            </button>
          </div>
        </div>
      )}

      {phase === "summary" && exercise && (
        <div className="space-y-5 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-emerald-600" /> Review complete
          </h2>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="bg-slate-50 p-3 rounded-lg border">
              <span className="block text-2xl font-bold text-slate-800">
                {exercise.question_count}
              </span>
              <span className="text-xs text-slate-500">Questions</span>
            </div>
            <div className="bg-emerald-50 p-3 rounded-lg border border-emerald-100">
              <span className="block text-2xl font-bold text-emerald-700">
                {correctCount}
              </span>
              <span className="text-xs text-emerald-600">Correct</span>
            </div>
            <div className="bg-red-50 p-3 rounded-lg border border-red-100">
              <span className="block text-2xl font-bold text-red-700">
                {history.length - correctCount}
              </span>
              <span className="text-xs text-red-600">Incorrect</span>
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={backToQueue}
              className="px-4 py-2 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 transition"
            >
              Back to queue
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

const StatCard: React.FC<{
  label: string;
  value: number;
  tone: "fuchsia" | "violet" | "slate";
}> = ({ label, value, tone }) => {
  const tones = {
    fuchsia: "bg-fuchsia-50 border-fuchsia-100 text-fuchsia-800",
    violet: "bg-violet-50 border-violet-100 text-violet-800",
    slate: "bg-slate-50 border-slate-200 text-slate-700",
  };
  return (
    <div className={`rounded-xl border p-3 text-center ${tones[tone]}`}>
      <span className="block text-2xl font-bold">{value}</span>
      <span className="text-xs opacity-80">{label}</span>
    </div>
  );
};

const QueueSection: React.FC<{
  title: string;
  items: ReviewQueueItem[];
}> = ({ title, items }) => (
  <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
    <div className="px-4 py-2 border-b bg-slate-50 text-sm font-semibold text-slate-700">
      {title} ({items.length})
    </div>
    <ul className="divide-y max-h-64 overflow-y-auto">
      {items.map((item, i) => (
        <li
          key={`${item.kind}-${item.vocabulary_id ?? item.character}-${i}`}
          className="px-4 py-2.5 flex items-center justify-between gap-3 text-sm"
        >
          <div className="min-w-0">
            <p className="font-medium text-slate-900 truncate">
              {item.kind === "vocabulary"
                ? `${item.text} · ${item.pinyin}`
                : item.character}
            </p>
            {item.kind === "vocabulary" && item.meaning && (
              <p className="text-slate-500 truncate text-xs">{item.meaning}</p>
            )}
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <span
              className={`text-xs px-2 py-0.5 rounded-full border ${
                item.reason === "due"
                  ? "bg-fuchsia-50 text-fuchsia-800 border-fuchsia-200"
                  : "bg-slate-50 text-slate-600 border-slate-200"
              }`}
            >
              {item.reason}
            </span>
            <span className="text-xs text-slate-400">{item.status}</span>
          </div>
        </li>
      ))}
    </ul>
  </div>
);

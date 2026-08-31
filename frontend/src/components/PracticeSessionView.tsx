import React, { useMemo, useState } from "react";
import {
  Brain,
  CheckCircle,
  XCircle,
  RefreshCw,
  ChevronRight,
  RotateCcw,
} from "lucide-react";

import {
  generateCharacterRecognition,
  generateVocabularyRecall,
  submitAnswer,
} from "../api/practice";
import type {
  Exercise,
  KnowledgeStatus,
  Question,
  RecallDirection,
  RecognitionDirection,
  SubmitAnswerResponse,
} from "../types/practice";
import { expandAcceptedTerms, formatAnswerForDisplay } from "../lib/pinyin";
import { Button, Card, CardContent, CardHeader, CardTitle } from "./ui";
import { cn } from "../lib/utils";

type PracticeMode = "vocabulary_recall" | "character_recognition";
type Phase = "setup" | "active" | "summary";

interface AnswerRecord {
  question: Question;
  response: SubmitAnswerResponse;
}

function errorDetail(err: unknown): string {
  const anyErr = err as { response?: { data?: { detail?: string } } };
  return anyErr.response?.data?.detail || "Something went wrong.";
}

const fieldClassName =
  "w-full rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-ring";

const answerFieldClassName =
  "w-full rounded-lg border border-input bg-background px-4 py-3 text-center text-xl text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-ring";

export const PracticeSessionView: React.FC = () => {
  // Setup
  const [mode, setMode] = useState<PracticeMode>("vocabulary_recall");
  const [count, setCount] = useState(10);
  const [knowledgeStatus, setKnowledgeStatus] = useState<KnowledgeStatus | "">(
    "",
  );
  const [vocabDirection, setVocabDirection] =
    useState<RecallDirection>("meaning_to_hanzi");
  const [charDirection, setCharDirection] = useState<RecognitionDirection>(
    "character_to_meaning",
  );

  // Session
  const [phase, setPhase] = useState<Phase>("setup");
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

  const progressLabel = exercise
    ? `${Math.min(index + 1, exercise.question_count)} / ${exercise.question_count}`
    : "";

  const correctCount = history.filter((h) => h.response.is_correct).length;

  const startSession = async () => {
    setLoading(true);
    setError(null);
    setFeedback(null);
    setHistory([]);
    setIndex(0);
    setAnswer("");

    try {
      const data =
        mode === "vocabulary_recall"
          ? await generateVocabularyRecall({
              count,
              knowledge_status: knowledgeStatus || null,
              direction: vocabDirection,
            })
          : await generateCharacterRecognition({
              count,
              knowledge_status: knowledgeStatus || null,
              direction: charDirection,
            });

      setExercise(data);
      setPhase("active");
      setStartedAt(Date.now());
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
      return;
    }
    setIndex(next);
    setAnswer("");
    setFeedback(null);
    setStartedAt(Date.now());
    setError(null);
  };

  const resetToSetup = () => {
    setPhase("setup");
    setExercise(null);
    setIndex(0);
    setAnswer("");
    setFeedback(null);
    setHistory([]);
    setError(null);
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-6">
      <header className="border-b border-border pb-4">
        <h1 className="flex items-center gap-2 text-2xl font-bold text-foreground">
          <Brain className="text-primary" /> Practice
        </h1>
        <p className="text-sm text-muted-foreground">
          Recall vocabulary or recognise characters from your knowledge profile.
        </p>
      </header>

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* ---------- SETUP ---------- */}
      {phase === "setup" && (
        <Card>
          <CardContent className="space-y-5">
            <div>
              <label className="mb-2 block text-sm font-medium text-foreground">
                Mode
              </label>
              <div className="flex gap-2">
                <ModeButton
                  active={mode === "vocabulary_recall"}
                  onClick={() => setMode("vocabulary_recall")}
                  label="Vocabulary recall"
                />
                <ModeButton
                  active={mode === "character_recognition"}
                  onClick={() => setMode("character_recognition")}
                  label="Character recognition"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-foreground">
                  Questions
                </label>
                <input
                  type="number"
                  min={1}
                  max={50}
                  value={count}
                  onChange={(e) => setCount(Number(e.target.value) || 1)}
                  className={fieldClassName}
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-foreground">
                  Knowledge status
                </label>
                <select
                  value={knowledgeStatus}
                  onChange={(e) =>
                    setKnowledgeStatus(e.target.value as KnowledgeStatus | "")
                  }
                  className={fieldClassName}
                >
                  <option value="">Any</option>
                  <option value="new">New</option>
                  <option value="learning">Learning</option>
                  <option value="known">Known</option>
                </select>
              </div>
            </div>

            {mode === "vocabulary_recall" ? (
              <div>
                <label className="mb-1 block text-sm font-medium text-foreground">
                  Direction
                </label>
                <select
                  value={vocabDirection}
                  onChange={(e) =>
                    setVocabDirection(e.target.value as RecallDirection)
                  }
                  className={fieldClassName}
                >
                  <option value="meaning_to_hanzi">Meaning → Hanzi</option>
                  <option value="hanzi_to_meaning">Hanzi → Meaning</option>
                  <option value="pinyin_to_hanzi">Pinyin → Hanzi</option>
                </select>
              </div>
            ) : (
              <div>
                <label className="mb-1 block text-sm font-medium text-foreground">
                  Direction
                </label>
                <select
                  value={charDirection}
                  onChange={(e) =>
                    setCharDirection(e.target.value as RecognitionDirection)
                  }
                  className={fieldClassName}
                >
                  <option value="character_to_meaning">
                    Character → Meaning
                  </option>
                  <option value="character_to_pinyin">
                    Character → Pinyin
                  </option>
                  <option value="meaning_to_character">
                    Meaning → Character
                  </option>
                  <option value="pinyin_to_character">
                    Pinyin → Character
                  </option>
                </select>
              </div>
            )}

            <div className="flex justify-end pt-2">
              <Button type="button" onClick={startSession} disabled={loading}>
                {loading ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" /> Starting...
                  </>
                ) : (
                  <>
                    Start practice <ChevronRight className="h-4 w-4" />
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ---------- ACTIVE ---------- */}
      {phase === "active" && exercise && currentQuestion && (
        <div className="space-y-5">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>
              {exercise.type === "vocabulary_recall"
                ? "Vocabulary recall"
                : "Character recognition"}
            </span>
            <span className="font-medium text-foreground">{progressLabel}</span>
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
                    className={answerFieldClassName}
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
                    <div className="space-y-1">
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
                          <p className="mt-2 text-xs opacity-75">
                            Tip: pinyin accepts tone numbers (ni3) or marks
                            (nǐ).
                          </p>
                        </>
                      )}
                      {feedback.new_status && (
                        <p className="mt-1 text-sm opacity-80">
                          Knowledge: {feedback.previous_status ?? "—"} →{" "}
                          {feedback.new_status}
                        </p>
                      )}
                    </div>
                  </div>

                  <Button type="button" onClick={goNext} className="w-full">
                    {index + 1 >= exercise.question_count
                      ? "See summary"
                      : "Next question"}
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
              onClick={resetToSetup}
              className="text-muted-foreground"
            >
              <RotateCcw className="h-3.5 w-3.5" /> End session
            </Button>
          </div>
        </div>
      )}

      {/* ---------- SUMMARY ---------- */}
      {phase === "summary" && exercise && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-success" /> Session complete
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

            <ul className="divide-y divide-border overflow-hidden rounded-lg border border-border">
              {history.map(({ question, response }) => (
                <li
                  key={question.id}
                  className="flex items-center justify-between gap-3 bg-card px-4 py-3 text-sm"
                >
                  <div className="min-w-0">
                    <p className="truncate font-medium text-foreground">
                      {question.prompt}
                    </p>
                    <p className="truncate text-muted-foreground">
                      Your answer: {response.raw_answer || "—"}
                    </p>
                  </div>
                  {response.is_correct ? (
                    <CheckCircle className="h-5 w-5 shrink-0 text-success" />
                  ) : (
                    <XCircle className="h-5 w-5 shrink-0 text-destructive" />
                  )}
                </li>
              ))}
            </ul>

            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="secondary" onClick={resetToSetup}>
                Back to setup
              </Button>
              <Button type="button" onClick={startSession} disabled={loading}>
                Practice again
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

const ModeButton: React.FC<{
  active: boolean;
  onClick: () => void;
  label: string;
}> = ({ active, onClick, label }) => (
  <button
    type="button"
    onClick={onClick}
    className={cn(
      "flex-1 rounded-lg border px-3 py-2 text-sm font-medium transition",
      active
        ? "border-primary/40 bg-primary/10 text-foreground"
        : "border-border bg-card text-muted-foreground hover:border-primary/30 hover:text-foreground",
    )}
  >
    {label}
  </button>
);

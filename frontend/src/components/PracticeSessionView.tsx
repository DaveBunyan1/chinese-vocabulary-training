import React, { useEffect, useMemo, useState } from "react";
import {
  Brain,
  CheckCircle,
  XCircle,
  RefreshCw,
  ChevronRight,
  RotateCcw,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import {
  generateCharacterRecognition,
  generateVocabularyRecall,
  submitAnswer,
} from "../api/practice";
import { fetchCategories } from "../api/categories";
import type {
  Exercise,
  KnowledgeStatus,
  Question,
  RecallDirection,
  RecognitionDirection,
  SubmitAnswerResponse,
} from "../types/practice";
import type { Category } from "../types/categories";
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
  const [count, setCount] = useState(5);
  const [knowledgeStatus, setKnowledgeStatus] = useState<KnowledgeStatus | "">(
    "",
  );
  const [categoryId, setCategoryId] = useState<string>("");
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

  const { data: categoriesData } = useQuery({
    queryKey: ["categories"],
    queryFn: fetchCategories,
  });
  const categories: Category[] = categoriesData?.categories ?? [];

  const currentQuestion: Question | null = useMemo(() => {
    if (!exercise) return null;
    return exercise.questions[index] ?? null;
  }, [exercise, index]);

  const isMcq = Boolean(
    currentQuestion?.is_multiple_choice &&
    currentQuestion.options &&
    currentQuestion.options.length > 0,
  );

  const progressLabel = exercise
    ? `${Math.min(index + 1, exercise.question_count)} / ${exercise.question_count}`
    : "";

  const correctCount = history.filter((h) => h.response.is_correct).length;

  useEffect(() => {
    setAnswer("");
  }, [index, exercise?.id]);

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
              category_id: categoryId || null,
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
    if (!answer.trim()) {
      setError("Please select or enter an answer.");
      return;
    }

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
          Sessions default to 5 multiple-choice questions.
        </p>
      </header>

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      {phase === "setup" && (
        <Card>
          <CardContent className="space-y-5 pt-6">
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
                <p className="mt-1 text-xs text-muted-foreground">
                  Default 5 — each question has up to 5 answer choices.
                </p>
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

            {mode === "vocabulary_recall" && (
              <div>
                <label className="mb-1 block text-sm font-medium text-foreground">
                  Category
                </label>
                <select
                  value={categoryId}
                  onChange={(e) => setCategoryId(e.target.value)}
                  className={fieldClassName}
                >
                  <option value="">Any category</option>
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                      {c.hsk_level != null ? ` (HSK ${c.hsk_level})` : ""}
                    </option>
                  ))}
                </select>
              </div>
            )}

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

            <Button
              type="button"
              onClick={startSession}
              disabled={loading}
              className="w-full"
            >
              {loading ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" /> Starting…
                </>
              ) : (
                "Start practice"
              )}
            </Button>
          </CardContent>
        </Card>
      )}

      {phase === "active" && exercise && currentQuestion && (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>
              Question {progressLabel}
              {exercise.knowledge_status_filter
                ? ` · ${exercise.knowledge_status_filter}`
                : ""}
            </span>
            <span>
              Score {correctCount}/{history.length}
            </span>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-center text-3xl font-semibold tracking-wide">
                {currentQuestion.prompt}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {!feedback ? (
                <form onSubmit={handleSubmitAnswer} className="space-y-4">
                  {isMcq ? (
                    <div>
                      <label className="mb-1 block text-sm font-medium text-foreground">
                        Choose an answer
                      </label>
                      <select
                        value={answer}
                        onChange={(e) => setAnswer(e.target.value)}
                        className={fieldClassName}
                        disabled={submitting}
                      >
                        <option value="">— Select —</option>
                        {currentQuestion.options.map((opt) => (
                          <option key={opt.text} value={opt.text}>
                            {opt.text}
                          </option>
                        ))}
                      </select>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {currentQuestion.options.length} choices
                      </p>
                    </div>
                  ) : (
                    <input
                      type="text"
                      value={answer}
                      onChange={(e) => setAnswer(e.target.value)}
                      placeholder="Type your answer"
                      className={answerFieldClassName}
                      autoFocus
                      disabled={submitting}
                    />
                  )}
                  <Button
                    type="submit"
                    disabled={submitting || !answer.trim()}
                    className="w-full"
                  >
                    {submitting ? "Checking…" : "Check answer"}
                  </Button>
                </form>
              ) : (
                <div className="space-y-4">
                  <div
                    className={cn(
                      "rounded-lg border p-4",
                      feedback.is_correct
                        ? "border-success/40 bg-success/10 text-success"
                        : "border-destructive/40 bg-destructive/10 text-destructive",
                    )}
                  >
                    <div className="flex items-start gap-2">
                      {feedback.is_correct ? (
                        <CheckCircle className="mt-0.5 h-5 w-5 shrink-0" />
                      ) : (
                        <XCircle className="mt-0.5 h-5 w-5 shrink-0" />
                      )}
                      <div className="min-w-0 flex-1">
                        <p className="font-medium">
                          {feedback.is_correct ? "Correct!" : "Not quite"}
                        </p>
                        <p className="mt-1 text-sm opacity-90">
                          Your answer:{" "}
                          <span className="font-medium">
                            {formatAnswerForDisplay(feedback.raw_answer)}
                          </span>
                        </p>
                        {!feedback.is_correct && (
                          <p className="mt-1 text-sm opacity-90">
                            Expected:{" "}
                            <span className="font-medium">
                              {currentQuestion.correct_answers
                                .map(formatAnswerForDisplay)
                                .join(" / ")}
                            </span>
                          </p>
                        )}
                        {currentQuestion.correct_answers.length > 1 && (
                          <p className="mt-2 text-xs opacity-75">
                            Any of these also count:{" "}
                            {expandAcceptedTerms(
                              currentQuestion.correct_answers,
                            ).join(", ")}
                          </p>
                        )}
                        {feedback.new_status && (
                          <p className="mt-1 text-sm opacity-80">
                            Knowledge: {feedback.previous_status ?? "—"} →{" "}
                            {feedback.new_status}
                          </p>
                        )}
                      </div>
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

            <ul className="max-h-64 space-y-2 overflow-y-auto text-sm">
              {history.map(({ question, response }) => (
                <li
                  key={question.id}
                  className="flex items-start gap-2 rounded-md border border-border px-3 py-2"
                >
                  {response.is_correct ? (
                    <CheckCircle className="mt-0.5 h-4 w-4 shrink-0 text-success" />
                  ) : (
                    <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
                  )}
                  <div className="min-w-0">
                    <p className="font-medium text-foreground">
                      {question.prompt}
                    </p>
                    <p className="text-muted-foreground">
                      {formatAnswerForDisplay(response.raw_answer)}
                      {!response.is_correct && (
                        <>
                          {" "}
                          →{" "}
                          {question.correct_answers
                            .map(formatAnswerForDisplay)
                            .join(" / ")}
                        </>
                      )}
                    </p>
                  </div>
                </li>
              ))}
            </ul>

            <Button type="button" onClick={resetToSetup} className="w-full">
              Practice again
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

function ModeButton({
  active,
  onClick,
  label,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex-1 rounded-lg border px-3 py-2 text-sm font-medium transition-colors",
        active
          ? "border-primary bg-primary text-primary-foreground"
          : "border-border bg-background text-foreground hover:bg-muted",
      )}
    >
      {label}
    </button>
  );
}

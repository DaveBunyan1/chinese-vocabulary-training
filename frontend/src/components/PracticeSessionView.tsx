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
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      <header className="border-b pb-4">
        <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
          <Brain className="text-indigo-600" /> Practice
        </h1>
        <p className="text-slate-500 text-sm">
          Recall vocabulary or recognise characters from your knowledge profile.
        </p>
      </header>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* ---------- SETUP ---------- */}
      {phase === "setup" && (
        <div className="space-y-5 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
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
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Questions
              </label>
              <input
                type="number"
                min={1}
                max={50}
                value={count}
                onChange={(e) => setCount(Number(e.target.value) || 1)}
                className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Knowledge status
              </label>
              <select
                value={knowledgeStatus}
                onChange={(e) =>
                  setKnowledgeStatus(e.target.value as KnowledgeStatus | "")
                }
                className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
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
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Direction
              </label>
              <select
                value={vocabDirection}
                onChange={(e) =>
                  setVocabDirection(e.target.value as RecallDirection)
                }
                className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="meaning_to_hanzi">Meaning → Hanzi</option>
                <option value="hanzi_to_meaning">Hanzi → Meaning</option>
                <option value="pinyin_to_hanzi">Pinyin → Hanzi</option>
              </select>
            </div>
          ) : (
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Direction
              </label>
              <select
                value={charDirection}
                onChange={(e) =>
                  setCharDirection(e.target.value as RecognitionDirection)
                }
                className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="character_to_meaning">
                  Character → Meaning
                </option>
                <option value="character_to_pinyin">Character → Pinyin</option>
                <option value="meaning_to_character">
                  Meaning → Character
                </option>
                <option value="pinyin_to_character">Pinyin → Character</option>
              </select>
            </div>
          )}

          <div className="flex justify-end pt-2">
            <button
              type="button"
              onClick={startSession}
              disabled={loading}
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-medium px-5 py-2.5 rounded-lg shadow transition"
            >
              {loading ? (
                <>
                  <RefreshCw className="animate-spin w-4 h-4" /> Starting...
                </>
              ) : (
                <>
                  Start practice <ChevronRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* ---------- ACTIVE ---------- */}
      {phase === "active" && exercise && currentQuestion && (
        <div className="space-y-5">
          <div className="flex items-center justify-between text-sm text-slate-500">
            <span>
              {exercise.type === "vocabulary_recall"
                ? "Vocabulary recall"
                : "Character recognition"}
            </span>
            <span className="font-medium text-slate-700">{progressLabel}</span>
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
                  className="w-full text-center text-xl border border-slate-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
                <button
                  type="submit"
                  disabled={submitting || !answer.trim()}
                  className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-medium py-2.5 rounded-lg transition"
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
                    : "Next question"}
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>

          <div className="flex justify-center">
            <button
              type="button"
              onClick={resetToSetup}
              className="text-sm text-slate-500 hover:text-slate-700 flex items-center gap-1"
            >
              <RotateCcw className="w-3.5 h-3.5" /> End session
            </button>
          </div>
        </div>
      )}

      {/* ---------- SUMMARY ---------- */}
      {phase === "summary" && exercise && (
        <div className="space-y-5 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-emerald-600" /> Session
            complete
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

          <ul className="divide-y border rounded-lg overflow-hidden">
            {history.map(({ question, response }) => (
              <li
                key={question.id}
                className="flex items-center justify-between gap-3 px-4 py-3 text-sm bg-white"
              >
                <div className="min-w-0">
                  <p className="font-medium text-slate-800 truncate">
                    {question.prompt}
                  </p>
                  <p className="text-slate-500 truncate">
                    Your answer: {response.raw_answer || "—"}
                  </p>
                </div>
                {response.is_correct ? (
                  <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0" />
                ) : (
                  <XCircle className="w-5 h-5 text-red-500 shrink-0" />
                )}
              </li>
            ))}
          </ul>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={resetToSetup}
              className="px-4 py-2 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 transition"
            >
              Back to setup
            </button>
            <button
              type="button"
              onClick={startSession}
              disabled={loading}
              className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white transition disabled:opacity-50"
            >
              Practice again
            </button>
          </div>
        </div>
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
    className={`flex-1 px-3 py-2 rounded-lg border text-sm font-medium transition ${
      active
        ? "bg-indigo-50 border-indigo-300 text-indigo-800"
        : "bg-white border-slate-300 text-slate-600 hover:border-slate-400"
    }`}
  >
    {label}
  </button>
);

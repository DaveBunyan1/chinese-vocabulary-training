import React, { useState } from "react";

import { Sparkles, BookOpen, CheckCircle, RefreshCw } from "lucide-react";
import type { TextImportResponse } from "../types/textImport";
import { importChineseText } from "../api/textImport";

export const TextImportView: React.FC = () => {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TextImportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const data = await importChineseText({ raw_text: text });
      setResult(data);
    } catch (err: unknown) {
      const detail =
        err &&
        typeof err === "object" &&
        "response" in err &&
        (err as { response?: { data?: { detail?: string } } }).response?.data
          ?.detail;
      setError(typeof detail === "string" ? detail : "Failed to analyze text.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <header className="border-b pb-4">
        <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
          <BookOpen className="text-amber-600" /> Build My Knowledge
        </h1>
        <p className="text-slate-500 text-sm">
          Paste raw Chinese text to extract vocabulary, auto-assign HSK
          categories, and record exposure.
        </p>
      </header>

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <textarea
          rows={6}
          className="w-full p-4 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 font-sans text-lg dark:text-slate-400"
          placeholder="Paste Chinese text here... (e.g., 我喜欢学中文。)"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={loading || !text.trim()}
            className="flex items-center gap-2 bg-amber-600 hover:bg-amber-700 disabled:opacity-50 text-white font-medium px-5 py-2.5 rounded-lg shadow transition"
          >
            {loading ? (
              <>
                <RefreshCw className="animate-spin w-4 h-4" /> Analyzing...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" /> Import & Analyze
              </>
            )}
          </button>
        </div>
      </form>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* Results View */}
      {result && (
        <div className="space-y-6 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h2 className="text-lg font-semibold flex items-center gap-2 text-emerald-700">
            <CheckCircle className="w-5 h-5" /> Import Summary
          </h2>

          {/* Metric Badges */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-slate-50 p-3 rounded-lg border text-center">
              <span className="block text-2xl font-bold text-slate-800">
                {result.total_tokens}
              </span>
              <span className="text-xs text-slate-500">Tokens Analyzed</span>
            </div>
            <div className="bg-emerald-50 p-3 rounded-lg border border-emerald-100 text-center">
              <span className="block text-2xl font-bold text-emerald-700">
                {result.created_vocabulary_count}
              </span>
              <span className="text-xs text-emerald-600">New Words Added</span>
            </div>
            <div className="bg-amber-50 p-3 rounded-lg border border-amber-100 text-center">
              <span className="block text-2xl font-bold text-amber-700">
                {result.updated_vocabulary_knowledge_count}
              </span>
              <span className="text-xs text-amber-600">Vocab Exposures</span>
            </div>
            <div className="bg-blue-50 p-3 rounded-lg border border-blue-100 text-center">
              <span className="block text-2xl font-bold text-blue-700">
                {result.updated_character_knowledge_count}
              </span>
              <span className="text-xs text-blue-600">Char Exposures</span>
            </div>
          </div>

          {/* Extracted Vocabulary Items */}
          <div>
            <h3 className="text-sm font-medium text-slate-600 mb-3">
              Extracted Vocabulary Items:
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {result.imported_items.map((item) => (
                <div
                  key={item.id}
                  className="p-3 border rounded-lg hover:border-amber-300 transition bg-slate-50"
                >
                  <div className="flex justify-between items-baseline">
                    <span className="text-xl font-bold text-slate-900">
                      {item.text}
                    </span>
                    <span className="text-sm font-medium text-amber-700">
                      {item.pinyin}
                    </span>
                  </div>
                  <p className="text-sm text-slate-600 mt-1">{item.meaning}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

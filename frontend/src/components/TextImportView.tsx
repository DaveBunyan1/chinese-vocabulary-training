import React, { useState } from "react";
import { Sparkles, BookOpen, CheckCircle, RefreshCw } from "lucide-react";

import type { TextImportResponse } from "../types/textImport";
import { importChineseText } from "../api/textImport";
import { Button, Card, CardContent, CardHeader, CardTitle } from "./ui";

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
    <div className="mx-auto max-w-4xl space-y-8 p-6">
      <header className="border-b border-border pb-4">
        <h1 className="flex items-center gap-2 text-2xl font-bold text-foreground">
          <BookOpen className="text-primary" /> Build My Knowledge
        </h1>
        <p className="text-sm text-muted-foreground">
          Paste raw Chinese text to extract vocabulary, auto-assign HSK
          categories, and record exposure.
        </p>
      </header>

      <form onSubmit={handleSubmit} className="space-y-4">
        <textarea
          rows={6}
          className="w-full rounded-lg border border-input bg-background p-4 text-lg text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-ring"
          placeholder="Paste Chinese text here... (e.g., 我喜欢学中文。)"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <div className="flex justify-end">
          <Button type="submit" disabled={loading || !text.trim()} size="lg">
            {loading ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" /> Analyzing...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" /> Import & Analyze
              </>
            )}
          </Button>
        </div>
      </form>

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      {result && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-success">
              <CheckCircle className="h-5 w-5" /> Import Summary
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              <Metric value={result.total_tokens} label="Tokens Analyzed" />
              <Metric
                value={result.created_vocabulary_count}
                label="New Words Added"
                emphasis="success"
              />
              <Metric
                value={result.updated_vocabulary_knowledge_count}
                label="Vocab Exposures"
                emphasis="warning"
              />
              <Metric
                value={result.updated_character_knowledge_count}
                label="Char Exposures"
                emphasis="primary"
              />
            </div>

            <div>
              <h3 className="mb-3 text-sm font-medium text-muted-foreground">
                Extracted Vocabulary Items
              </h3>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                {result.imported_items.map((item) => (
                  <div
                    key={item.id}
                    className="rounded-lg border border-border bg-muted/50 p-3 transition hover:border-primary/40"
                  >
                    <div className="flex items-baseline justify-between gap-2">
                      <span className="text-xl font-bold text-foreground">
                        {item.text}
                      </span>
                      <span className="text-sm font-medium text-primary">
                        {item.pinyin}
                      </span>
                    </div>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {item.meaning}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

const Metric: React.FC<{
  value: number;
  label: string;
  emphasis?: "success" | "warning" | "primary";
}> = ({ value, label, emphasis }) => {
  const valueClass =
    emphasis === "success"
      ? "text-success"
      : emphasis === "warning"
        ? "text-warning"
        : emphasis === "primary"
          ? "text-primary"
          : "text-foreground";

  return (
    <div className="rounded-lg border border-border bg-muted/50 p-3 text-center">
      <span className={`block text-2xl font-bold ${valueClass}`}>{value}</span>
      <span className="text-xs text-muted-foreground">{label}</span>
    </div>
  );
};

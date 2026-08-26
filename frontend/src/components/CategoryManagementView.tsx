import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  FolderTree,
  Plus,
  RefreshCw,
  Trash2,
  ChevronRight,
} from "lucide-react";

import {
  assignCategory,
  createCategory,
  fetchCategories,
  fetchCategoryVocabulary,
  unassignCategory,
} from "../api/categories";
import { fetchVocabularyDashboard } from "../api/vocabularyDashboard";
import type { Category, CategoryVocabularyItem } from "../types/categories";
import type { VocabularyDashboardItem } from "../types/vocabularyDashboard";

function errorDetail(err: unknown): string {
  const anyErr = err as { response?: { data?: { detail?: string } } };
  const detail = anyErr.response?.data?.detail;
  if (typeof detail === "string") return detail;
  return "Something went wrong.";
}

export const CategoryManagementView: React.FC = () => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [assigned, setAssigned] = useState<CategoryVocabularyItem[]>([]);
  const [allVocab, setAllVocab] = useState<VocabularyDashboardItem[]>([]);

  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Create form
  const [newName, setNewName] = useState("");
  const [newType, setNewType] = useState<"custom" | "topic">("custom");
  const [newParentId, setNewParentId] = useState("");

  // Assign search
  const [assignSearch, setAssignSearch] = useState("");

  const selected = useMemo(
    () => categories.find((c) => c.id === selectedId) ?? null,
    [categories, selectedId],
  );

  const manageable = useMemo(
    () => categories.filter((c) => c.type === "custom" || c.type === "topic"),
    [categories],
  );

  const loadCategories = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchCategories();
      setCategories(res.categories);
    } catch (err) {
      setError(errorDetail(err));
    } finally {
      setLoading(false);
    }
  }, []);

  const loadAssigned = useCallback(async (categoryId: string) => {
    try {
      const res = await fetchCategoryVocabulary(categoryId);
      setAssigned(res.items);
    } catch (err) {
      setError(errorDetail(err));
      setAssigned([]);
    }
  }, []);

  const loadAllVocab = useCallback(async () => {
    try {
      const res = await fetchVocabularyDashboard({});
      setAllVocab(res.items);
    } catch {
      /* non-fatal */
    }
  }, []);

  useEffect(() => {
    void loadCategories();
    void loadAllVocab();
  }, [loadCategories, loadAllVocab]);

  useEffect(() => {
    if (selectedId) {
      void loadAssigned(selectedId);
    } else {
      setAssigned([]);
    }
  }, [selectedId, loadAssigned]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const res = await createCategory({
        name: newName.trim(),
        type: newType,
        parent_id: newParentId || null,
      });
      setNewName("");
      setNewParentId("");
      await loadCategories();
      setSelectedId(res.category.id);
    } catch (err) {
      setError(errorDetail(err));
    } finally {
      setBusy(false);
    }
  };

  const handleAssign = async (vocabularyId: string) => {
    if (!selectedId) return;
    setBusy(true);
    setError(null);
    try {
      await assignCategory({
        vocabulary_id: vocabularyId,
        category_id: selectedId,
      });
      await loadAssigned(selectedId);
    } catch (err) {
      setError(errorDetail(err));
    } finally {
      setBusy(false);
    }
  };

  const handleUnassign = async (vocabularyId: string) => {
    if (!selectedId) return;
    setBusy(true);
    setError(null);
    try {
      await unassignCategory(vocabularyId, selectedId);
      await loadAssigned(selectedId);
    } catch (err) {
      setError(errorDetail(err));
    } finally {
      setBusy(false);
    }
  };

  const assignedIds = useMemo(
    () => new Set(assigned.map((a) => a.vocabulary_id)),
    [assigned],
  );

  const candidates = useMemo(() => {
    const needle = assignSearch.trim().toLowerCase();
    return allVocab
      .filter((v) => !assignedIds.has(v.vocabulary_id))
      .filter((v) => {
        if (!needle) return true;
        return (
          v.text.toLowerCase().includes(needle) ||
          v.pinyin.toLowerCase().includes(needle) ||
          v.meaning.toLowerCase().includes(needle)
        );
      })
      .slice(0, 30);
  }, [allVocab, assignedIds, assignSearch]);

  const roots = categories.filter((c) => !c.parent_id);
  const childrenOf = (id: string) =>
    categories.filter((c) => c.parent_id === id);

  const canManageSelected =
    selected && (selected.type === "custom" || selected.type === "topic");

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <header className="border-b pb-4 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <FolderTree className="text-orange-600" /> Categories
          </h1>
          <p className="text-slate-500 text-sm">
            Create topic/custom categories and assign vocabulary items.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadCategories()}
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: category list + create */}
        <div className="space-y-4">
          <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-4 space-y-2 max-h-112 overflow-y-auto">
            <h2 className="text-sm font-semibold text-slate-700 mb-2">
              All categories
            </h2>
            {roots.map((root) => (
              <div key={root.id}>
                <CategoryRow
                  category={root}
                  selected={selectedId === root.id}
                  onSelect={() => setSelectedId(root.id)}
                />
                {childrenOf(root.id).map((child) => (
                  <CategoryRow
                    key={child.id}
                    category={child}
                    selected={selectedId === child.id}
                    onSelect={() => setSelectedId(child.id)}
                    nested
                  />
                ))}
              </div>
            ))}
            {categories.length === 0 && !loading && (
              <p className="text-sm text-slate-400 py-4 text-center">
                No categories yet.
              </p>
            )}
          </div>

          <form
            onSubmit={handleCreate}
            className="bg-white border border-slate-200 rounded-xl shadow-sm p-4 space-y-3"
          >
            <h2 className="text-sm font-semibold text-slate-700 flex items-center gap-1">
              <Plus className="w-4 h-4" /> New category
            </h2>
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Name (e.g. Food, Travel…)"
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
            />
            <div className="grid grid-cols-2 gap-2">
              <select
                value={newType}
                onChange={(e) =>
                  setNewType(e.target.value as "custom" | "topic")
                }
                className="border border-slate-300 rounded-lg px-3 py-2 text-sm"
              >
                <option value="custom">Custom</option>
                <option value="topic">Topic</option>
              </select>
              <select
                value={newParentId}
                onChange={(e) => setNewParentId(e.target.value)}
                className="border border-slate-300 rounded-lg px-3 py-2 text-sm"
              >
                <option value="">No parent</option>
                {manageable.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            <button
              type="submit"
              disabled={busy || !newName.trim()}
              className="w-full bg-orange-600 hover:bg-orange-700 disabled:opacity-50 text-white text-sm font-medium py-2 rounded-lg transition"
            >
              Create
            </button>
          </form>
        </div>

        {/* Right: assignments */}
        <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-4 space-y-4 min-h-96">
          {!selected ? (
            <p className="text-sm text-slate-400 text-center py-16">
              Select a category to manage assignments.
            </p>
          ) : (
            <>
              <div>
                <h2 className="text-lg font-semibold text-slate-800">
                  {selected.name}
                </h2>
                <p className="text-xs text-slate-500">
                  {selected.type}
                  {selected.parent_id ? " · subcategory" : ""}
                  {!canManageSelected && " · read-only (HSK/system)"}
                </p>
              </div>

              <div>
                <h3 className="text-sm font-medium text-slate-600 mb-2">
                  Assigned ({assigned.length})
                </h3>
                {assigned.length === 0 ? (
                  <p className="text-sm text-slate-400">No items yet.</p>
                ) : (
                  <ul className="space-y-1 max-h-40 overflow-y-auto">
                    {assigned.map((item) => (
                      <li
                        key={item.vocabulary_id}
                        className="flex items-center justify-between gap-2 px-2 py-1.5 rounded-lg hover:bg-slate-50 text-sm"
                      >
                        <span>
                          <span className="font-medium text-slate-900">
                            {item.text}
                          </span>{" "}
                          <span className="text-slate-500">{item.pinyin}</span>
                        </span>
                        {canManageSelected && (
                          <button
                            type="button"
                            onClick={() =>
                              void handleUnassign(item.vocabulary_id)
                            }
                            disabled={busy}
                            className="text-red-500 hover:text-red-700 p-1"
                            title="Remove"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {canManageSelected && (
                <div className="border-t pt-3 space-y-2">
                  <h3 className="text-sm font-medium text-slate-600">
                    Add vocabulary
                  </h3>
                  <input
                    type="search"
                    value={assignSearch}
                    onChange={(e) => setAssignSearch(e.target.value)}
                    placeholder="Search your vocabulary..."
                    className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                  />
                  <ul className="space-y-1 max-h-48 overflow-y-auto">
                    {candidates.map((v) => (
                      <li
                        key={v.vocabulary_id}
                        className="flex items-center justify-between gap-2 px-2 py-1.5 rounded-lg hover:bg-orange-50 text-sm"
                      >
                        <span>
                          <span className="font-medium">{v.text}</span>{" "}
                          <span className="text-slate-500">{v.pinyin}</span>
                        </span>
                        <button
                          type="button"
                          onClick={() => void handleAssign(v.vocabulary_id)}
                          disabled={busy}
                          className="text-orange-600 hover:text-orange-800 text-xs font-medium flex items-center gap-0.5"
                        >
                          Add <ChevronRight className="w-3 h-3" />
                        </button>
                      </li>
                    ))}
                    {candidates.length === 0 && (
                      <li className="text-sm text-slate-400 py-2 text-center">
                        No matching unassigned words.
                      </li>
                    )}
                  </ul>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

const CategoryRow: React.FC<{
  category: Category;
  selected: boolean;
  onSelect: () => void;
  nested?: boolean;
}> = ({ category, selected, onSelect, nested }) => (
  <button
    type="button"
    onClick={onSelect}
    className={`w-full text-left px-3 py-2 rounded-lg text-sm transition flex items-center justify-between ${
      nested ? "ml-4" : ""
    } ${
      selected
        ? "bg-orange-50 text-orange-900 border border-orange-200"
        : "hover:bg-slate-50 text-slate-700"
    }`}
  >
    <span className="font-medium">{category.name}</span>
    <span className="text-xs text-slate-400 uppercase">{category.type}</span>
  </button>
);

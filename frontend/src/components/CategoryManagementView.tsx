import React, { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  FolderTree,
  Plus,
  RefreshCw,
  Trash2,
  ChevronRight,
  Pencil,
} from "lucide-react";

import {
  assignCategory,
  createCategory,
  deleteCategory,
  fetchCategories,
  fetchCategoryVocabulary,
  unassignCategory,
  updateCategory,
} from "../api/categories";
import { fetchVocabularyDashboard } from "../api/vocabularyDashboard";
import type { Category } from "../types/categories";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle } from "./ui";
import { cn } from "../lib/utils";

function errorDetail(err: unknown): string {
  const anyErr = err as { response?: { data?: { detail?: string } } };
  const detail = anyErr.response?.data?.detail;
  if (typeof detail === "string") return detail;
  return "Something went wrong.";
}

const fieldClassName =
  "w-full rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-ring";

export const CategoryManagementView: React.FC = () => {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const [busy, setBusy] = useState(false);

  // Create form
  const [newName, setNewName] = useState("");
  const [newType, setNewType] = useState<"custom" | "topic">("custom");
  const [newParentId, setNewParentId] = useState("");

  // Assign search
  const [assignSearch, setAssignSearch] = useState("");
  const [editName, setEditName] = useState("");
  const [editing, setEditing] = useState(false);

  const queryClient = useQueryClient();
  const [mutationError, setMutationError] = useState<string | null>(null);

  const {
    data: categoriesData,
    isFetching: loading,
    error: categoriesError,
    refetch: refetchCategories,
  } = useQuery({
    queryKey: ["categories"],
    queryFn: fetchCategories,
  });
  const categories = useMemo(
    () => categoriesData?.categories ?? [],
    [categoriesData],
  );

  const { data: allVocabData } = useQuery({
    queryKey: ["vocabulary-dashboard", "all-for-categories"],
    queryFn: () => fetchVocabularyDashboard({}),
  });
  const allVocab = useMemo(() => allVocabData?.items ?? [], [allVocabData]);

  const { data: assignedData } = useQuery({
    queryKey: ["category-vocabulary", selectedId],
    queryFn: () => fetchCategoryVocabulary(selectedId!),
    enabled: Boolean(selectedId),
  });
  const assigned = useMemo(
    () => (selectedId ? (assignedData?.items ?? []) : []),
    [selectedId, assignedData],
  );

  const error =
    mutationError ?? (categoriesError ? errorDetail(categoriesError) : null);

  const selected = useMemo(
    () => categories.find((c) => c.id === selectedId) ?? null,
    [categories, selectedId],
  );

  const manageable = useMemo(
    () => categories.filter((c) => c.type === "custom" || c.type === "topic"),
    [categories],
  );

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;
    setBusy(true);
    setMutationError(null);
    try {
      const res = await createCategory({
        name: newName.trim(),
        type: newType,
        parent_id: newParentId || null,
      });
      setNewName("");
      setNewParentId("");
      await refetchCategories();
      setSelectedId(res.category.id);
    } catch (err) {
      setMutationError(errorDetail(err));
    } finally {
      setBusy(false);
    }
  };

  const handleAssign = async (vocabularyId: string) => {
    if (!selectedId) return;
    setBusy(true);
    setMutationError(null);
    try {
      await assignCategory({
        vocabulary_id: vocabularyId,
        category_id: selectedId,
      });
      await queryClient.invalidateQueries({
        queryKey: ["category-vocabulary", selectedId],
      });
    } catch (err) {
      setMutationError(errorDetail(err));
    } finally {
      setBusy(false);
    }
  };

  const handleUnassign = async (vocabularyId: string) => {
    if (!selectedId) return;
    setBusy(true);
    setMutationError(null);
    try {
      await unassignCategory(vocabularyId, selectedId);
      await queryClient.invalidateQueries({
        queryKey: ["category-vocabulary", selectedId],
      });
    } catch (err) {
      setMutationError(errorDetail(err));
    } finally {
      setBusy(false);
    }
  };

  const startEdit = () => {
    if (!selected) return;
    setEditName(selected.name);
    setEditing(true);
  };

  const handleRename = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedId || !editName.trim()) return;
    setBusy(true);
    setMutationError(null);
    try {
      await updateCategory(selectedId, { name: editName.trim() });
      setEditing(false);
      await refetchCategories();
      await queryClient.invalidateQueries({ queryKey: ["categories"] });
    } catch (err) {
      setMutationError(errorDetail(err));
    } finally {
      setBusy(false);
    }
  };

  const handleDeleteCategory = async () => {
    if (!selectedId || !selected) return;
    const ok = window.confirm(
      `Delete category "${selected.name}"? Vocabulary will be unassigned from it.`,
    );
    if (!ok) return;
    setBusy(true);
    setMutationError(null);
    try {
      await deleteCategory(selectedId);
      setSelectedId(null);
      setEditing(false);
      await refetchCategories();
      await queryClient.invalidateQueries({ queryKey: ["categories"] });
      await queryClient.invalidateQueries({
        queryKey: ["vocabulary-dashboard"],
      });
    } catch (err) {
      setMutationError(errorDetail(err));
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
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <header className="flex items-start justify-between gap-4 border-b border-border pb-4">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold text-foreground">
            <FolderTree className="text-primary" /> Categories
          </h1>
          <p className="text-sm text-muted-foreground">
            Create topic/custom categories and assign vocabulary items.
          </p>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => void refetchCategories()}
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

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Left: category list + create */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">All categories</CardTitle>
            </CardHeader>
            <CardContent className="max-h-112 space-y-2 overflow-y-auto pt-3">
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
                <p className="py-4 text-center text-sm text-muted-foreground">
                  No categories yet.
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardContent className="space-y-3">
              <h2 className="flex items-center gap-1 text-sm font-semibold text-foreground">
                <Plus className="h-4 w-4" /> New category
              </h2>
              <form onSubmit={handleCreate} className="space-y-3">
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="Name (e.g. Food, Travel…)"
                  className={fieldClassName}
                />
                <div className="grid grid-cols-2 gap-2">
                  <select
                    value={newType}
                    onChange={(e) =>
                      setNewType(e.target.value as "custom" | "topic")
                    }
                    className={fieldClassName}
                  >
                    <option value="custom">Custom</option>
                    <option value="topic">Topic</option>
                  </select>
                  <select
                    value={newParentId}
                    onChange={(e) => setNewParentId(e.target.value)}
                    className={fieldClassName}
                  >
                    <option value="">No parent</option>
                    {manageable.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>
                <Button
                  type="submit"
                  disabled={busy || !newName.trim()}
                  className="w-full"
                >
                  Create
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Right: assignments */}
        <Card className="min-h-96">
          <CardContent className="space-y-4">
            {!selected ? (
              <p className="py-16 text-center text-sm text-muted-foreground">
                Select a category to manage assignments.
              </p>
            ) : (
              <>
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      {editing && canManageSelected ? (
                        <form
                          onSubmit={handleRename}
                          className="flex flex-wrap items-center gap-2"
                        >
                          <input
                            value={editName}
                            onChange={(e) => setEditName(e.target.value)}
                            className={cn(fieldClassName, "min-w-32 flex-1")}
                            autoFocus
                          />
                          <Button
                            type="submit"
                            size="sm"
                            disabled={busy || !editName.trim()}
                          >
                            Save
                          </Button>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => setEditing(false)}
                          >
                            Cancel
                          </Button>
                        </form>
                      ) : (
                        <h2 className="text-lg font-semibold text-foreground">
                          {selected.name}
                        </h2>
                      )}
                    </div>
                    {canManageSelected && !editing && (
                      <div className="flex shrink-0 gap-1">
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={startEdit}
                          disabled={busy}
                          title="Rename"
                          className="text-muted-foreground hover:text-primary"
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={() => void handleDeleteCategory()}
                          disabled={busy}
                          title="Delete category"
                          className="text-muted-foreground hover:text-destructive"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    )}
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {selected.type}
                    {selected.parent_id ? " · subcategory" : ""}
                    {!canManageSelected && " · read-only (HSK/system)"}
                  </p>
                </div>

                <div>
                  <h3 className="mb-2 text-sm font-medium text-muted-foreground">
                    Assigned ({assigned.length})
                  </h3>
                  {assigned.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                      No items yet.
                    </p>
                  ) : (
                    <ul className="max-h-40 space-y-1 overflow-y-auto">
                      {assigned.map((item) => (
                        <li
                          key={item.vocabulary_id}
                          className="flex items-center justify-between gap-2 rounded-lg px-2 py-1.5 text-sm hover:bg-muted"
                        >
                          <span>
                            <span className="font-medium text-foreground">
                              {item.text}
                            </span>{" "}
                            <span className="text-muted-foreground">
                              {item.pinyin}
                            </span>
                          </span>
                          {canManageSelected && (
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              onClick={() =>
                                void handleUnassign(item.vocabulary_id)
                              }
                              disabled={busy}
                              title="Remove"
                              className="h-8 w-8 text-destructive hover:text-destructive"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          )}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                {canManageSelected && (
                  <div className="space-y-2 border-t border-border pt-3">
                    <h3 className="text-sm font-medium text-muted-foreground">
                      Add vocabulary
                    </h3>
                    <input
                      type="search"
                      value={assignSearch}
                      onChange={(e) => setAssignSearch(e.target.value)}
                      placeholder="Search your vocabulary..."
                      className={fieldClassName}
                    />
                    <ul className="max-h-48 space-y-1 overflow-y-auto">
                      {candidates.map((v) => (
                        <li
                          key={v.vocabulary_id}
                          className="flex items-center justify-between gap-2 rounded-lg px-2 py-1.5 text-sm hover:bg-muted"
                        >
                          <span>
                            <span className="font-medium text-foreground">
                              {v.text}
                            </span>{" "}
                            <span className="text-muted-foreground">
                              {v.pinyin}
                            </span>
                          </span>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => void handleAssign(v.vocabulary_id)}
                            disabled={busy}
                            className="text-primary"
                          >
                            Add <ChevronRight className="h-3 w-3" />
                          </Button>
                        </li>
                      ))}
                      {candidates.length === 0 && (
                        <li className="py-2 text-center text-sm text-muted-foreground">
                          No matching unassigned words.
                        </li>
                      )}
                    </ul>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
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
    className={cn(
      "flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm transition",
      nested && "ml-4",
      selected
        ? "border border-primary/30 bg-primary/10 text-foreground"
        : "text-foreground hover:bg-muted",
    )}
  >
    <span className="font-medium">{category.name}</span>
    <Badge variant="outline" className="uppercase">
      {category.type}
    </Badge>
  </button>
);

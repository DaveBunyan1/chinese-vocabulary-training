import { useState } from "react";
import {
  BarChart3,
  BookOpen,
  Brain,
  FolderTree,
  Languages,
  LayoutList,
  Sparkles,
} from "lucide-react";

import { TextImportView } from "./components/TextImportView";
import { PracticeSessionView } from "./components/PracticeSessionView";
import { VocabularyDashboardView } from "./components/VocabularyDashboardView";
import { CharacterDashboardView } from "./components/CharacterDashboardView";
import { CategoryManagementView } from "./components/CategoryManagementView";
import { ProgressStatsView } from "./components/ProgressStatsView";
import { SmartReviewView } from "./components/SmartReviewView";
import { ThemeToggle } from "./components/ui/ThemeToggle";

type Tab =
  | "import"
  | "practice"
  | "vocabulary"
  | "characters"
  | "categories"
  | "progress"
  | "review";

function App() {
  const [tab, setTab] = useState<Tab>("import");

  return (
    <div className="min-h-screen bg-background text-foreground">
      <nav className="border-b border-border bg-card">
        <div className="mx-auto flex max-w-5xl items-center gap-1 overflow-x-auto px-6">
          <TabButton
            active={tab === "import"}
            onClick={() => setTab("import")}
            icon={<BookOpen className="w-4 h-4" />}
            label="Build knowledge"
          />
          <TabButton
            active={tab === "vocabulary"}
            onClick={() => setTab("vocabulary")}
            icon={<LayoutList className="w-4 h-4" />}
            label="Vocabulary"
          />
          <TabButton
            active={tab === "characters"}
            onClick={() => setTab("characters")}
            icon={<Languages className="w-4 h-4" />}
            label="Characters"
          />
          <TabButton
            active={tab === "categories"}
            onClick={() => setTab("categories")}
            icon={<FolderTree className="w-4 h-4" />}
            label="Categories"
          />
          <TabButton
            active={tab === "review"}
            onClick={() => setTab("review")}
            icon={<Sparkles className="w-4 h-4" />}
            label="Smart review"
          />
          <TabButton
            active={tab === "practice"}
            onClick={() => setTab("practice")}
            icon={<Brain className="w-4 h-4" />}
            label="Practice"
          />
          <TabButton
            active={tab === "progress"}
            onClick={() => setTab("progress")}
            icon={<BarChart3 className="w-4 h-4" />}
            label="Progress"
          />
          <div className="ml-auto flex shrink-0 items-center py-2 pl-2">
            <ThemeToggle />
          </div>
        </div>
      </nav>

      <main>
        {tab === "import" && <TextImportView />}
        {tab === "vocabulary" && <VocabularyDashboardView />}
        {tab === "characters" && <CharacterDashboardView />}
        {tab === "categories" && <CategoryManagementView />}
        {tab === "review" && <SmartReviewView />}
        {tab === "practice" && <PracticeSessionView />}
        {tab === "progress" && <ProgressStatsView />}
      </main>
    </div>
  );
}

const TabButton: React.FC<{
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}> = ({ active, onClick, icon, label }) => (
  <button
    type="button"
    onClick={onClick}
    className={`flex items-center gap-2 whitespace-nowrap border-b-2 px-4 py-3 text-sm font-medium transition ${
      active
        ? "border-primary text-primary"
        : "border-transparent text-muted-foreground hover:text-foreground"
    }`}
  >
    {icon}
    {label}
  </button>
);

export default App;

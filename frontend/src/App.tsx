import { useState } from "react";
import { BookOpen, Brain } from "lucide-react";

import { TextImportView } from "./components/TextImportView";
import { PracticeSessionView } from "./components/PracticeSessionView";

type Tab = "import" | "practice";

function App() {
  const [tab, setTab] = useState<Tab>("import");

  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="border-b bg-white">
        <div className="max-w-4xl mx-auto px-6 flex gap-1">
          <TabButton
            active={tab === "import"}
            onClick={() => setTab("import")}
            icon={<BookOpen className="w-4 h-4" />}
            label="Build knowledge"
          />
          <TabButton
            active={tab === "practice"}
            onClick={() => setTab("practice")}
            icon={<Brain className="w-4 h-4" />}
            label="Practice"
          />
        </div>
      </nav>

      <main>
        {tab === "import" ? <TextImportView /> : <PracticeSessionView />}
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
    className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition ${
      active
        ? "border-indigo-600 text-indigo-700"
        : "border-transparent text-slate-500 hover:text-slate-700"
    }`}
  >
    {icon}
    {label}
  </button>
);

export default App;

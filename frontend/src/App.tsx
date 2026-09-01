import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "./components/layout/AppShell";
import { HomePage } from "./components/home/HomePage";
import { TextImportView } from "./components/TextImportView";
import { PracticeSessionView } from "./components/PracticeSessionView";
import { VocabularyDashboardView } from "./components/VocabularyDashboardView";
import { CharacterDashboardView } from "./components/CharacterDashboardView";
import { CategoryManagementView } from "./components/CategoryManagementView";
import { ProgressStatsView } from "./components/ProgressStatsView";
import { SmartReviewView } from "./components/SmartReviewView";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<HomePage />} />
          <Route path="import" element={<TextImportView />} />
          <Route path="vocabulary" element={<VocabularyDashboardView />} />
          <Route path="characters" element={<CharacterDashboardView />} />
          <Route path="categories" element={<CategoryManagementView />} />
          <Route path="review" element={<SmartReviewView />} />
          <Route path="practice" element={<PracticeSessionView />} />
          <Route path="progress" element={<ProgressStatsView />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

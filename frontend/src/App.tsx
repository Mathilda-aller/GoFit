import { Navigate, Route, Routes } from "react-router";
import {
  CardPage,
  DouyinPage,
  ImportPage,
  LibraryPage,
} from "./pages/EntryPages";
import { MePage } from "./pages/MePage";
import { PlanDetailPage, PlansPage, SelectActionPage } from "./pages/PlanPages";
import {
  CompletePage,
  ExperiencePage,
  SafetyPage,
  TrainingPage,
} from "./pages/TrainingPages";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/demo/douyin/video_lateral_raise_demo" replace />} />
      <Route path="/demo/douyin/:videoId" element={<DouyinPage />} />
      <Route path="/import/:videoId" element={<ImportPage />} />
      <Route path="/cards/:cardId" element={<CardPage />} />
      <Route path="/plans" element={<PlansPage />} />
      <Route path="/plans/:planId" element={<PlanDetailPage />} />
      <Route path="/plans/:planId/select" element={<SelectActionPage />} />
      <Route path="/library" element={<LibraryPage />} />
      <Route path="/train/:sessionId" element={<TrainingPage />} />
      <Route path="/train/:sessionId/complete" element={<CompletePage />} />
      <Route path="/experience/:exerciseId" element={<ExperiencePage />} />
      <Route path="/safety" element={<SafetyPage />} />
      <Route path="/me" element={<MePage />} />
      <Route path="*" element={<Navigate to="/plans" replace />} />
    </Routes>
  );
}

import { useEffect } from "react";
import { Navigate, Route, Routes } from "react-router";
import { LianguoBuddyPage } from "./features/lianguo/LianguoBuddyPage";
import {
  CardPage,
  DemoVideoListPage,
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
import { useAppStore } from "./store";

export default function App() {
  const hydrateFromBackend = useAppStore((state) => state.hydrateFromBackend);
  useEffect(() => {
    void hydrateFromBackend();
  }, [hydrateFromBackend]);
  return (
    <>
      <Routes>
        <Route path="/" element={<Navigate to="/demo/douyin/video_lateral_raise_demo" replace />} />
        <Route path="/demo/douyin/:videoId" element={<DouyinPage />} />
        <Route path="/demo-videos" element={<DemoVideoListPage />} />
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
        <Route path="/me/buddy" element={<LianguoBuddyPage />} />
        <Route path="*" element={<Navigate to="/plans" replace />} />
      </Routes>
    </>
  );
}

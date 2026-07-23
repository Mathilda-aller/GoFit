import { useQuery } from "@tanstack/react-query";
import { businessApi, toFrontendActionCard, toFrontendExperienceGroups } from "./business-api";
import { actionCards, cardIds, getDemoExperience } from "./mocks/data";

const demoFallbackEnabled = import.meta.env.VITE_ENABLE_DEMO_FALLBACK === "true";

const wait = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms));

export const mockRepository = {
  async getActionCard(cardId: string) {
    await wait(120);
    return actionCards[cardId] ?? null;
  },
  async listActionCards() {
    await wait(160);
    return cardIds.map((id) => actionCards[id]);
  },
};

export function useActionCard(cardId: string | undefined) {
  return useQuery({
    queryKey: ["action-card", cardId],
    queryFn: async () => {
      const id = cardId ?? "";
      try {
        return toFrontendActionCard(await businessApi.getActionCard(id));
      } catch (error) {
        if (demoFallbackEnabled) {
          const fallback = await mockRepository.getActionCard(id);
          if (fallback) return fallback;
        }
        throw error;
      }
    },
    enabled: Boolean(cardId),
    staleTime: 30_000,
    retry: 1,
  });
}

export function useActionCards() {
  return useQuery({
    queryKey: ["action-cards"],
    queryFn: async () => {
      try {
        return (await businessApi.listActionCards()).map(toFrontendActionCard);
      } catch (error) {
        if (demoFallbackEnabled) return mockRepository.listActionCards();
        throw error;
      }
    },
    staleTime: 30_000,
    retry: 1,
  });
}

export function useRecommendations(planId: string | undefined) {
  return useQuery({
    queryKey: ["recommendations", planId],
    queryFn: async () => {
      const result = await businessApi.recommendations(planId ?? "");
      return result.items.map((item) => ({
        cardId: item.card.id,
        response: toFrontendActionCard(item.card),
        reason: item.reasonText,
      }));
    },
    enabled: Boolean(planId),
    staleTime: 10_000,
    retry: 1,
  });
}

export function useExperiences(exerciseId: string, currentVideoId?: string, fromTraining = false) {
  return useQuery({
    queryKey: ["experiences", exerciseId, currentVideoId, fromTraining],
    queryFn: async () => {
      try {
        const result = await businessApi.experiences(exerciseId, "ARMS_FELT_MORE", currentVideoId, fromTraining);
        return { ...result, frontendGroups: toFrontendExperienceGroups(result) };
      } catch {
        const demo = getDemoExperience(exerciseId);
        return {
          exerciseId: demo.exerciseId,
          exerciseName: demo.exerciseName,
          problemTag: "ARMS_FELT_MORE",
          problemTitle: demo.problemTitle,
          commentCount: demo.commentCount,
          sourceVideoCount: demo.sourceVideoCount,
          sourceNote: `演示来源：${demo.sourceVideoCount} 条同动作视频下的 ${demo.commentCount} 条关联评论`,
          safetyTriggered: false,
          groups: [],
          frontendGroups: demo.groups,
        };
      }
    },
    staleTime: 30_000,
    retry: 1,
  });
}

export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: businessApi.me,
    staleTime: 10_000,
    retry: 1,
  });
}

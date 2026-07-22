import { get, set } from "idb-keyval";
import { create } from "zustand";
import { createJSONStorage, persist, type StateStorage } from "zustand/middleware";
import type { Plan, Sensation, TrainingSession } from "./domain";

const idbStorage: StateStorage = {
  getItem: async (name) => (await get<string>(name)) ?? null,
  setItem: async (name, value) => set(name, value),
  removeItem: async (name) => set(name, null),
};

type AppState = {
  plans: Plan[];
  sessions: TrainingSession[];
  collectedCardIds: string[];
  uninterestedCardIds: string[];
  helpfulExperienceIds: string[];
  createPlan: (name?: string, initialCardId?: string) => string;
  deletePlan: (planId: string) => void;
  renamePlan: (planId: string, name: string) => void;
  addCardToPlan: (planId: string, cardId: string) => void;
  removeCardFromPlan: (planId: string, cardId: string) => void;
  moveCard: (planId: string, cardId: string, direction: -1 | 1) => void;
  toggleCollected: (cardId: string) => void;
  markUninterested: (cardId: string) => void;
  startSession: (planId: string) => string | null;
  setCurrentIndex: (sessionId: string, index: number) => void;
  skipItem: (sessionId: string, itemId: string) => void;
  submitFeedback: (
    sessionId: string,
    itemId: string,
    sensation: Sensation,
    feltRegion?: string,
  ) => void;
  completeSession: (sessionId: string) => void;
  endSession: (sessionId: string) => void;
  markHelpful: (experienceId: string) => void;
  resetDemo: () => void;
};

const initialPlans: Plan[] = [
  {
    id: "plan_back_previous",
    name: "上次练背",
    cardIds: ["video_reverse_fly_demo", "video_shoulder_press_demo"],
    updatedAt: "2026-07-20T09:30:00.000Z",
    useCount: 2,
  },
];

function updatedPlan(plan: Plan, cardIds = plan.cardIds): Plan {
  return { ...plan, cardIds, updatedAt: new Date().toISOString() };
}

export const useAppStore = create<AppState>()(
  persist(
    (setState, getState) => ({
      plans: initialPlans,
      sessions: [],
      collectedCardIds: ["video_reverse_fly_demo"],
      uninterestedCardIds: [],
      helpfulExperienceIds: [],
      createPlan: (name = "未命名练单", initialCardId) => {
        const id = `plan_${Date.now()}`;
        const plan: Plan = {
          id,
          name,
          cardIds: initialCardId ? [initialCardId] : [],
          updatedAt: new Date().toISOString(),
          useCount: 0,
        };
        setState((state) => ({ plans: [plan, ...state.plans] }));
        return id;
      },
      deletePlan: (planId) =>
        setState((state) => ({
          plans: state.plans.filter((plan) => plan.id !== planId),
          sessions: state.sessions.filter((session) => session.planId !== planId),
        })),
      renamePlan: (planId, name) =>
        setState((state) => ({
          plans: state.plans.map((plan) =>
            plan.id === planId ? { ...updatedPlan(plan), name: name.trim() || "未命名练单" } : plan,
          ),
        })),
      addCardToPlan: (planId, cardId) =>
        setState((state) => ({
          plans: state.plans.map((plan) =>
            plan.id === planId && !plan.cardIds.includes(cardId)
              ? updatedPlan(plan, [...plan.cardIds, cardId])
              : plan,
          ),
        })),
      removeCardFromPlan: (planId, cardId) =>
        setState((state) => ({
          plans: state.plans.map((plan) =>
            plan.id === planId
              ? updatedPlan(
                  plan,
                  plan.cardIds.filter((id) => id !== cardId),
                )
              : plan,
          ),
        })),
      moveCard: (planId, cardId, direction) =>
        setState((state) => ({
          plans: state.plans.map((plan) => {
            if (plan.id !== planId) return plan;
            const index = plan.cardIds.indexOf(cardId);
            const nextIndex = index + direction;
            if (index < 0 || nextIndex < 0 || nextIndex >= plan.cardIds.length) return plan;
            const cardIds = [...plan.cardIds];
            [cardIds[index], cardIds[nextIndex]] = [cardIds[nextIndex], cardIds[index]];
            return updatedPlan(plan, cardIds);
          }),
        })),
      toggleCollected: (cardId) =>
        setState((state) => ({
          collectedCardIds: state.collectedCardIds.includes(cardId)
            ? state.collectedCardIds.filter((id) => id !== cardId)
            : [...state.collectedCardIds, cardId],
        })),
      markUninterested: (cardId) =>
        setState((state) => ({
          uninterestedCardIds: [...new Set([...state.uninterestedCardIds, cardId])],
        })),
      startSession: (planId) => {
        const plan = getState().plans.find((candidate) => candidate.id === planId);
        if (!plan || plan.cardIds.length === 0) return null;
        const id = `session_${Date.now()}`;
        const session: TrainingSession = {
          id,
          planId,
          planName: plan.name,
          status: "IN_PROGRESS",
          currentIndex: 0,
          startedAt: new Date().toISOString(),
          items: plan.cardIds.map((cardId, index) => ({
            id: `${id}_item_${index}`,
            cardId,
            state: "NOT_STARTED",
          })),
        };
        setState((state) => ({
          plans: state.plans.map((candidate) =>
            candidate.id === planId ? { ...candidate, useCount: candidate.useCount + 1 } : candidate,
          ),
          sessions: [session, ...state.sessions.filter((item) => item.status !== "IN_PROGRESS")],
        }));
        return id;
      },
      setCurrentIndex: (sessionId, index) =>
        setState((state) => ({
          sessions: state.sessions.map((session) =>
            session.id === sessionId
              ? { ...session, currentIndex: Math.max(0, Math.min(index, session.items.length - 1)) }
              : session,
          ),
        })),
      skipItem: (sessionId, itemId) =>
        setState((state) => ({
          sessions: state.sessions.map((session) =>
            session.id === sessionId
              ? {
                  ...session,
                  items: session.items.map((item) =>
                    item.id === itemId ? { ...item, state: "SKIPPED" } : item,
                  ),
                  currentIndex: Math.min(session.currentIndex + 1, session.items.length - 1),
                }
              : session,
          ),
        })),
      submitFeedback: (sessionId, itemId, sensation, feltRegion) =>
        setState((state) => ({
          sessions: state.sessions.map((session) =>
            session.id === sessionId
              ? {
                  ...session,
                  items: session.items.map((item) =>
                    item.id === itemId
                      ? {
                          ...item,
                          sensation,
                          feltRegion,
                          state:
                            sensation === "DISCOMFORT" ? "STOPPED_DISCOMFORT" : "COMPLETED",
                        }
                      : item,
                  ),
                }
              : session,
          ),
        })),
      completeSession: (sessionId) =>
        setState((state) => ({
          sessions: state.sessions.map((session) =>
            session.id === sessionId ? { ...session, status: "COMPLETED" } : session,
          ),
        })),
      endSession: (sessionId) =>
        setState((state) => ({
          sessions: state.sessions.map((session) =>
            session.id === sessionId ? { ...session, status: "ENDED" } : session,
          ),
        })),
      markHelpful: (experienceId) =>
        setState((state) => ({
          helpfulExperienceIds: [...new Set([...state.helpfulExperienceIds, experienceId])],
        })),
      resetDemo: () =>
        setState({
          plans: initialPlans,
          sessions: [],
          collectedCardIds: ["video_reverse_fly_demo"],
          uninterestedCardIds: [],
          helpfulExperienceIds: [],
        }),
    }),
    {
      name: "gofit-demo-v1",
      storage: createJSONStorage(() => idbStorage),
      partialize: (state) => ({
        plans: state.plans,
        sessions: state.sessions,
        collectedCardIds: state.collectedCardIds,
        uninterestedCardIds: state.uninterestedCardIds,
        helpfulExperienceIds: state.helpfulExperienceIds,
      }),
    },
  ),
);

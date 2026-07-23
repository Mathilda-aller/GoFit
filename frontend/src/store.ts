import { get, set } from "idb-keyval";
import { create } from "zustand";
import { createJSONStorage, persist, type StateStorage } from "zustand/middleware";
import { businessApi, toFrontendPlan, toFrontendSession } from "./business-api";
import {
  completeBuddyProgress,
  DEFAULT_BUDDY_PROGRESS,
  equipBuddyItem as equipBuddyProgressItem,
  purchaseBuddyItem as purchaseBuddyProgressItem,
  type BuddyProgress,
} from "./features/lianguo/buddy-progress";
import type { ShopItem } from "./features/lianguo/kit";
import type { Plan, Sensation, TrainingSession } from "./domain";

const idbStorage: StateStorage = {
  getItem: async (name) => (await get<string>(name)) ?? null,
  setItem: async (name, value) => set(name, value),
  removeItem: async (name) => set(name, null),
};

export type BackendStatus = "checking" | "online" | "offline";

type AppState = {
  plans: Plan[];
  sessions: TrainingSession[];
  collectedCardIds: string[];
  uninterestedCardIds: string[];
  helpfulExperienceIds: string[];
  buddyProgress: BuddyProgress;
  backendStatus: BackendStatus;
  backendError?: string;
  hydrateFromBackend: () => Promise<void>;
  createPlan: (name?: string, initialCardId?: string) => Promise<string>;
  deletePlan: (planId: string) => Promise<void>;
  renamePlan: (planId: string, name: string) => Promise<void>;
  addCardToPlan: (planId: string, cardId: string) => Promise<void>;
  removeCardFromPlan: (planId: string, cardId: string) => Promise<void>;
  moveCard: (planId: string, cardId: string, direction: -1 | 1) => Promise<void>;
  toggleCollected: (cardId: string) => Promise<void>;
  markUninterested: (cardId: string) => void;
  startSession: (planId: string) => Promise<string | null>;
  setCurrentIndex: (sessionId: string, index: number) => void;
  skipItem: (sessionId: string, itemId: string) => Promise<void>;
  submitFeedback: (sessionId: string, itemId: string, sensation: Sensation, feltRegion?: string) => Promise<void>;
  completeSession: (sessionId: string) => void;
  endSession: (sessionId: string) => Promise<void>;
  markHelpful: (experienceId: string) => void;
  completeBuddyTraining: () => void;
  purchaseBuddyItem: (item: ShopItem) => void;
  equipBuddyItem: (item: ShopItem) => void;
  resetDemo: () => void;
};

const initialPlans: Plan[] = [
  {
    id: "plan_shoulder_back_demo",
    name: "肩背训练",
    cardIds: [
      "video_shoulder_press_demo",
      "video_lateral_raise_demo",
      "video_reverse_fly_demo",
      "video_lat_pulldown_demo",
      "video_seated_row_demo",
      "video_straight_arm_pulldown_demo",
    ],
    itemIdsByCardId: {},
    updatedAt: "2026-07-20T09:30:00.000Z",
    useCount: 2,
  },
];

let hydrationPromise: Promise<void> | null = null;

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "无法连接业务后端";
}

function updatedPlan(plan: Plan, cardIds = plan.cardIds): Plan {
  return { ...plan, cardIds, updatedAt: new Date().toISOString() };
}

function replacePlan(plans: Plan[], plan: Plan) {
  const exists = plans.some((candidate) => candidate.id === plan.id);
  return exists ? plans.map((candidate) => candidate.id === plan.id ? plan : candidate) : [plan, ...plans];
}

function localSession(plan: Plan): TrainingSession {
  const id = `session_${Date.now()}`;
  return {
    id,
    planId: plan.id,
    planName: plan.name,
    status: "IN_PROGRESS",
    currentIndex: 0,
    startedAt: new Date().toISOString(),
    items: plan.cardIds.map((cardId, index) => ({ id: `${id}_item_${index}`, cardId, state: "NOT_STARTED" })),
  };
}

export const useAppStore = create<AppState>()(
  persist(
    (setState, getState) => ({
      plans: initialPlans,
      sessions: [],
      collectedCardIds: ["video_reverse_fly_demo"],
      uninterestedCardIds: [],
      helpfulExperienceIds: [],
      buddyProgress: DEFAULT_BUDDY_PROGRESS,
      backendStatus: "checking",
      backendError: undefined,
      hydrateFromBackend: async () => {
        if (hydrationPromise) return hydrationPromise;
        setState({ backendStatus: "checking", backendError: undefined });
        hydrationPromise = (async () => {
          try {
            const [, planList, cards] = await Promise.all([
              businessApi.health(),
              businessApi.listPlans(),
              businessApi.listActionCards(),
            ]);
            const activeSession = planList.activeSession
              ? toFrontendSession(await businessApi.getSession(planList.activeSession.id))
              : null;
            setState((state) => ({
              plans: planList.items.map(toFrontendPlan),
              sessions: activeSession
                ? [activeSession, ...state.sessions.filter((session) => session.id !== activeSession.id && session.status !== "IN_PROGRESS")]
                : state.sessions.filter((session) => session.status !== "IN_PROGRESS"),
              collectedCardIds: cards.filter((card) => card.isSaved).map((card) => card.id),
              backendStatus: "online",
              backendError: undefined,
            }));
          } catch (error) {
            setState({ backendStatus: "offline", backendError: errorMessage(error) });
          } finally {
            hydrationPromise = null;
          }
        })();
        return hydrationPromise;
      },
      createPlan: async (name = "未命名练单", initialCardId) => {
        try {
          const plan = toFrontendPlan(await businessApi.createPlan(name, initialCardId));
          setState((state) => ({ plans: replacePlan(state.plans, plan), backendStatus: "online", backendError: undefined }));
          return plan.id;
        } catch (error) {
          const id = `plan_${Date.now()}`;
          const plan: Plan = { id, name, cardIds: initialCardId ? [initialCardId] : [], itemIdsByCardId: {}, updatedAt: new Date().toISOString(), useCount: 0 };
          setState((state) => ({ plans: [plan, ...state.plans], backendStatus: "offline", backendError: errorMessage(error) }));
          return id;
        }
      },
      deletePlan: async (planId) => {
        setState((state) => ({
          plans: state.plans.filter((plan) => plan.id !== planId),
          sessions: state.sessions.filter((session) => session.planId !== planId),
        }));
        try {
          await businessApi.updatePlan(planId, { status: "ARCHIVED" });
          setState({ backendStatus: "online", backendError: undefined });
        } catch (error) {
          setState({ backendStatus: "offline", backendError: errorMessage(error) });
        }
      },
      renamePlan: async (planId, rawName) => {
        const name = rawName.trim() || "未命名练单";
        setState((state) => ({ plans: state.plans.map((plan) => plan.id === planId ? { ...updatedPlan(plan), name } : plan) }));
        try {
          const plan = toFrontendPlan(await businessApi.updatePlan(planId, { name }));
          setState((state) => ({ plans: replacePlan(state.plans, plan), backendStatus: "online", backendError: undefined }));
        } catch (error) {
          setState({ backendStatus: "offline", backendError: errorMessage(error) });
        }
      },
      addCardToPlan: async (planId, cardId) => {
        const current = getState().plans.find((plan) => plan.id === planId);
        if (current && !current.cardIds.includes(cardId)) {
          setState((state) => ({ plans: state.plans.map((plan) => plan.id === planId ? updatedPlan(plan, [...plan.cardIds, cardId]) : plan) }));
        }
        try {
          const plan = toFrontendPlan(await businessApi.addPlanItem(planId, cardId));
          setState((state) => ({ plans: replacePlan(state.plans, plan), backendStatus: "online", backendError: undefined }));
        } catch (error) {
          setState({ backendStatus: "offline", backendError: errorMessage(error) });
        }
      },
      removeCardFromPlan: async (planId, cardId) => {
        const plan = getState().plans.find((candidate) => candidate.id === planId);
        const itemId = plan?.itemIdsByCardId?.[cardId];
        setState((state) => ({ plans: state.plans.map((candidate) => candidate.id === planId ? updatedPlan(candidate, candidate.cardIds.filter((id) => id !== cardId)) : candidate) }));
        if (!itemId) return;
        try {
          const remotePlan = toFrontendPlan(await businessApi.deletePlanItem(planId, itemId));
          setState((state) => ({ plans: replacePlan(state.plans, remotePlan), backendStatus: "online", backendError: undefined }));
        } catch (error) {
          setState({ backendStatus: "offline", backendError: errorMessage(error) });
        }
      },
      moveCard: async (planId, cardId, direction) => {
        const plan = getState().plans.find((candidate) => candidate.id === planId);
        if (!plan) return;
        const index = plan.cardIds.indexOf(cardId);
        const nextIndex = index + direction;
        if (index < 0 || nextIndex < 0 || nextIndex >= plan.cardIds.length) return;
        const cardIds = [...plan.cardIds];
        [cardIds[index], cardIds[nextIndex]] = [cardIds[nextIndex], cardIds[index]];
        setState((state) => ({ plans: state.plans.map((candidate) => candidate.id === planId ? updatedPlan(candidate, cardIds) : candidate) }));
        const orderedItemIds = cardIds.map((id) => plan.itemIdsByCardId?.[id]).filter((id): id is string => Boolean(id));
        if (orderedItemIds.length !== cardIds.length) return;
        try {
          const remotePlan = toFrontendPlan(await businessApi.updatePlan(planId, { orderedItemIds }));
          setState((state) => ({ plans: replacePlan(state.plans, remotePlan), backendStatus: "online", backendError: undefined }));
        } catch (error) {
          setState({ backendStatus: "offline", backendError: errorMessage(error) });
        }
      },
      toggleCollected: async (cardId) => {
        const saved = !getState().collectedCardIds.includes(cardId);
        setState((state) => ({ collectedCardIds: saved ? [...new Set([...state.collectedCardIds, cardId])] : state.collectedCardIds.filter((id) => id !== cardId) }));
        try {
          await businessApi.setCardSaved(cardId, saved);
          setState({ backendStatus: "online", backendError: undefined });
        } catch (error) {
          setState({ backendStatus: "offline", backendError: errorMessage(error) });
        }
      },
      markUninterested: (cardId) => setState((state) => ({ uninterestedCardIds: [...new Set([...state.uninterestedCardIds, cardId])] })),
      startSession: async (planId) => {
        const plan = getState().plans.find((candidate) => candidate.id === planId);
        if (!plan || !plan.cardIds.length) return null;
        try {
          const session = toFrontendSession(await businessApi.createSession(planId));
          setState((state) => ({
            plans: state.plans.map((candidate) => candidate.id === planId ? { ...candidate, useCount: candidate.useCount + 1 } : candidate),
            sessions: [session, ...state.sessions.filter((item) => item.status !== "IN_PROGRESS" && item.id !== session.id)],
            backendStatus: "online",
            backendError: undefined,
          }));
          return session.id;
        } catch (error) {
          const session = localSession(plan);
          setState((state) => ({ sessions: [session, ...state.sessions.filter((item) => item.status !== "IN_PROGRESS")], backendStatus: "offline", backendError: errorMessage(error) }));
          return session.id;
        }
      },
      setCurrentIndex: (sessionId, index) => setState((state) => ({
        sessions: state.sessions.map((session) => session.id === sessionId ? { ...session, currentIndex: Math.max(0, Math.min(index, session.items.length - 1)) } : session),
      })),
      skipItem: async (sessionId, itemId) => {
        setState((state) => ({ sessions: state.sessions.map((session) => session.id === sessionId ? {
          ...session,
          items: session.items.map((item) => item.id === itemId ? { ...item, state: "SKIPPED" } : item),
          currentIndex: Math.min(session.currentIndex + 1, session.items.length - 1),
        } : session) }));
        try {
          const session = toFrontendSession(await businessApi.updateSessionItem(sessionId, itemId, { itemStatus: "SKIPPED" }));
          setState((state) => ({ sessions: state.sessions.map((candidate) => candidate.id === sessionId ? session : candidate), backendStatus: "online", backendError: undefined }));
        } catch (error) {
          setState({ backendStatus: "offline", backendError: errorMessage(error) });
        }
      },
      submitFeedback: async (sessionId, itemId, sensation, feltRegion) => {
        setState((state) => ({ sessions: state.sessions.map((session) => {
          if (session.id !== sessionId) return session;
          const items = session.items.map((item) => item.id === itemId ? { ...item, sensation, feltRegion, state: sensation === "DISCOMFORT" ? "STOPPED_DISCOMFORT" as const : "COMPLETED" as const } : item);
          const nextIndex = items.findIndex((item) => item.state === "NOT_STARTED");
          return {
            ...session,
            items,
            currentIndex: nextIndex >= 0 ? nextIndex : session.currentIndex,
            status: nextIndex < 0 ? "COMPLETED" : session.status,
          };
        }) }));
        try {
          const result = await businessApi.submitFeedback(sessionId, itemId, sensation, feltRegion ? [feltRegion] : []);
          const session = toFrontendSession(result.session);
          setState((state) => ({ sessions: state.sessions.map((candidate) => candidate.id === sessionId ? session : candidate), backendStatus: "online", backendError: undefined }));
        } catch (error) {
          setState({ backendStatus: "offline", backendError: errorMessage(error) });
        }
      },
      completeSession: (sessionId) => setState((state) => ({ sessions: state.sessions.map((session) => session.id === sessionId ? { ...session, status: "COMPLETED" } : session) })),
      endSession: async (sessionId) => {
        setState((state) => ({ sessions: state.sessions.map((session) => session.id === sessionId ? { ...session, status: "ENDED" } : session) }));
        try {
          const session = toFrontendSession(await businessApi.endSession(sessionId));
          setState((state) => ({ sessions: state.sessions.map((candidate) => candidate.id === sessionId ? session : candidate), backendStatus: "online", backendError: undefined }));
        } catch (error) {
          setState({ backendStatus: "offline", backendError: errorMessage(error) });
        }
      },
      markHelpful: (experienceId) => setState((state) => ({ helpfulExperienceIds: [...new Set([...state.helpfulExperienceIds, experienceId])] })),
      completeBuddyTraining: () => setState((state) => ({ buddyProgress: completeBuddyProgress(state.buddyProgress) })),
      purchaseBuddyItem: (item) => setState((state) => ({ buddyProgress: purchaseBuddyProgressItem(state.buddyProgress, item) })),
      equipBuddyItem: (item) => setState((state) => ({ buddyProgress: equipBuddyProgressItem(state.buddyProgress, item) })),
      resetDemo: () => setState({
        plans: initialPlans,
        sessions: [],
        collectedCardIds: ["video_reverse_fly_demo"],
        uninterestedCardIds: [],
        helpfulExperienceIds: [],
        buddyProgress: DEFAULT_BUDDY_PROGRESS,
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
        buddyProgress: state.buddyProgress,
      }),
    },
  ),
);

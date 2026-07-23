import { actionCardResponseSchema, type ActionCardResponse, type ExperienceGroup, type Plan, type Sensation, type TrainingSession } from "./domain";
import { actionCards as mockActionCards } from "./mocks/data";

export const BUSINESS_API_BASE_URL = (import.meta.env.VITE_BUSINESS_API_URL || "/api/v1").replace(/\/$/, "");

export class BusinessApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly details?: unknown,
  ) {
    super(message);
    this.name = "BusinessApiError";
  }
}

type BusinessSourceVideo = {
  id: string;
  title: string;
  creatorName: string;
  sourceUrl: string;
  coverUrl: string | null;
};

export type BusinessActionCard = {
  id: string;
  videoId: string;
  exerciseId: string;
  actionName: string;
  bodyRegion: string;
  primaryMuscles: string[];
  secondaryMuscles: string[];
  equipment: string[];
  status: string;
  cardData: Record<string, unknown>;
  sourceVideo: BusinessSourceVideo;
  isSaved: boolean;
  experienceSummary: {
    exerciseId: string;
    commentCount: number;
    sourceVideoCount: number;
  } | null;
};

type BusinessPlanItem = {
  id: string;
  cardId: string;
  sortOrder: number;
  card: BusinessActionCard;
};

export type BusinessTrainingPlan = {
  id: string;
  userId: string;
  name: string;
  status: string;
  itemCount: number;
  bodyRegions: string[];
  cardNames: string[];
  createdAt: string;
  updatedAt: string;
  lastUsedAt: string | null;
  useCount: number;
  items: BusinessPlanItem[];
};

type BusinessSessionItem = {
  id: string;
  cardId: string;
  sortOrder: number;
  itemStatus: string;
  feedbackType: string | null;
  feltMuscles: string[];
  feedbackAt: string | null;
  card: BusinessActionCard;
};

export type BusinessTrainingSession = {
  id: string;
  userId: string;
  planId: string;
  planName: string;
  status: string;
  currentIndex: number;
  startedAt: string;
  completedAt: string | null;
  completedCount: number;
  totalCount: number;
  items: BusinessSessionItem[];
};

export type BusinessExperienceResult = {
  exerciseId: string;
  exerciseName: string;
  problemTag: string;
  problemTitle: string;
  commentCount: number;
  sourceVideoCount: number;
  sourceNote: string;
  safetyTriggered: boolean;
  groups: Array<{
    id: string;
    methodName: string;
    summary: string;
    mentionCount: number;
    sourceVideoCount: number;
    hasDisagreement: boolean;
    riskType: string;
    comments: Array<{
      id: string;
      content: string;
      authorName: string;
      sourceVideo: BusinessSourceVideo;
      sourceUrl: string | null;
    }>;
  }>;
};

export type BusinessMeSummary = {
  userId: string;
  nickname: string;
  completedSessionCount: number;
  completedActionCount: number;
  recentBodyRegions: string[];
  recentActions: string[];
  hasDiscomfortRecord: boolean;
};

type BusinessRecommendationResult = {
  requestId: string;
  ruleVersion: string;
  outcomeCode: string;
  items: Array<{
    card: BusinessActionCard;
    reasonCode: string;
    reasonText: string;
  }>;
};

type PlanListResponse = {
  activeSession: {
    id: string;
    planId: string;
    planName: string;
    status: string;
    completedCount: number;
    totalCount: number;
    startedAt: string;
  } | null;
  items: BusinessTrainingPlan[];
};

type FeedbackResult = {
  session: BusinessTrainingSession;
  problemTag: string | null;
  shouldShowSafety: boolean;
  nextItemId: string | null;
};

const standardActionAliases: Record<string, string> = {
  action_lateral_raise: "exercise_lateral_raise",
  action_front_raise: "exercise_front_raise",
  action_reverse_fly: "exercise_reverse_fly",
  action_shoulder_press: "exercise_shoulder_press",
  action_face_pull: "exercise_face_pull",
  action_lat_pulldown: "exercise_lat_pulldown",
  action_seated_cable_row: "exercise_seated_row",
  action_one_arm_dumbbell_row: "exercise_one_arm_row",
  action_chest_supported_row: "exercise_chest_supported_row",
  action_straight_arm_pulldown: "exercise_straight_arm_pulldown",
};

function apiUrl(path: string) {
  return `${BUSINESS_API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (init?.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  const response = await fetch(apiUrl(path), { ...init, headers });
  const contentType = response.headers.get("content-type") ?? "";
  const body = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    const message = typeof body === "object" && body && "detail" in body ? String(body.detail) : `Business API ${response.status}`;
    throw new BusinessApiError(message, response.status, body);
  }
  return body as T;
}

function timestampToMs(value: unknown, fallbackMs: number) {
  if (typeof value !== "string") return fallbackMs;
  const match = /^(\d+):(\d{2})$/.exec(value.trim());
  if (!match) return fallbackMs;
  return (Number(match[1]) * 60 + Number(match[2])) * 1000;
}

function stringValue(value: unknown, fallback: string) {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function cardSteps(card: BusinessActionCard) {
  const rawSteps = Array.isArray(card.cardData.steps) ? card.cardData.steps : [];
  return rawSteps.map((raw, index) => {
    const pair = Array.isArray(raw) ? raw : [];
    const startMs = timestampToMs(pair[1], index * 8000);
    return {
      order: index + 1,
      instruction: stringValue(pair[0], `${card.actionName}步骤 ${index + 1}`),
      startMs,
      endMs: startMs + 5000,
      evidenceIds: [`business-step-${card.id}-${index + 1}`],
    };
  });
}

export function toFrontendActionCard(card: BusinessActionCard): ActionCardResponse {
  const aiResult = card.cardData.aiResult;
  const curated = card.cardData.curatedMedia as {
    correctDemo?: { candidateId: string; mediaUrl: string };
    errorDemos?: Array<{ candidateId: string; mediaUrl: string }>;
  } | undefined;
  const artifacts = Array.isArray(card.cardData.mediaArtifacts)
    ? card.cardData.mediaArtifacts as Array<{ candidateId?: string; mediaUrl?: string }>
    : [];
  if (aiResult && typeof aiResult === "object") {
    const parsed = actionCardResponseSchema.parse(aiResult);
    const mediaByCandidate = new Map<string, string>();
    if (curated?.correctDemo) mediaByCandidate.set(curated.correctDemo.candidateId, curated.correctDemo.mediaUrl);
    for (const item of curated?.errorDemos ?? []) mediaByCandidate.set(item.candidateId, item.mediaUrl);
    for (const item of artifacts) {
      if (item.candidateId && item.mediaUrl && !mediaByCandidate.has(item.candidateId)) {
        mediaByCandidate.set(item.candidateId, item.mediaUrl);
      }
    }
    const attachUrl = <T extends { candidateId: string }>(media: T) => ({
      ...media,
      mediaUrl: mediaByCandidate.get(media.candidateId),
    });
    const contentSource = card.cardData.contentSource === "MOCK_FALLBACK" ? "MOCK_FALLBACK" : "AI";
    return actionCardResponseSchema.parse({
      ...parsed,
      contentSource,
      fallbackReason: typeof card.cardData.fallbackReason === "string" ? card.cardData.fallbackReason : undefined,
      sourceMediaUrl: typeof card.cardData.sourceMediaUrl === "string" ? card.cardData.sourceMediaUrl : undefined,
      actionCard: {
        ...parsed.actionCard,
        learningSide: {
          ...parsed.actionCard.learningSide,
          correctDemo: attachUrl(parsed.actionCard.learningSide.correctDemo),
          commonErrors: parsed.actionCard.learningSide.commonErrors.map((error) => ({
            ...error,
            errorDemo: attachUrl(error.errorDemo),
          })),
        },
        trainingSide: {
          ...parsed.actionCard.trainingSide,
          loopDemo: attachUrl(parsed.actionCard.trainingSide.loopDemo),
        },
      },
    });
  }
  const template = mockActionCards[card.id];
  const steps = cardSteps(card);
  const cue = stringValue(card.cardData.cue, `${card.actionName} · 保持控制`);
  const tip = stringValue(card.cardData.tip, "保持动作稳定；如有不适请停止训练。");
  const base = template ?? {
    schemaVersion: "1.1.0",
    requestId: `business-${card.id}`,
    status: "READY" as const,
    standardAction: { standardActionId: card.exerciseId, confidence: 1, decision: "BUSINESS_CARD" },
    actionCard: {
      sourceVideo: { videoId: card.id, title: card.sourceVideo.title, creatorName: card.sourceVideo.creatorName, sourceUrl: card.sourceVideo.sourceUrl },
      actionName: card.actionName,
      bodyRegion: card.bodyRegion,
      primaryMuscles: card.primaryMuscles,
      secondaryMuscles: card.secondaryMuscles,
      equipment: card.equipment,
      learningSide: {
        correctDemo: { kind: "CORRECT_DEMO" as const, candidateId: `business-${card.id}`, startMs: 0, endMs: 5000, evidenceIds: [`business-${card.id}`] },
        steps,
        keyReminders: [{ text: tip, evidenceIds: [`business-${card.id}`] }],
        commonErrors: [],
      },
      trainingSide: {
        loopDemo: { kind: "CORRECT_DEMO" as const, candidateId: `business-${card.id}`, startMs: 0, endMs: 5000, evidenceIds: [`business-${card.id}`] },
        quickCue: { text: cue, evidenceIds: [`business-${card.id}`] },
        quickTips: [{ text: tip, evidenceIds: [`business-${card.id}`] }],
      },
    },
    warnings: [],
    needsReviewReasons: [],
    provider: { name: "gofit-business", version: "0.1.0" },
  };
  return actionCardResponseSchema.parse({
    ...base,
    requestId: `business-${card.id}`,
    status: card.status === "READY" ? "READY" : card.status === "FAILED" ? "FAILED" : "NEEDS_REVIEW",
    standardAction: {
      ...base.standardAction,
      standardActionId: card.exerciseId,
      decision: "BUSINESS_CARD",
    },
    actionCard: {
      ...base.actionCard,
      sourceVideo: {
        videoId: card.id,
        title: card.sourceVideo.title,
        creatorName: card.sourceVideo.creatorName,
        sourceUrl: card.sourceVideo.sourceUrl,
      },
      actionName: card.actionName,
      bodyRegion: card.bodyRegion,
      primaryMuscles: card.primaryMuscles,
      secondaryMuscles: card.secondaryMuscles,
      equipment: card.equipment,
      learningSide: {
        ...base.actionCard.learningSide,
        correctDemo: {
          ...base.actionCard.learningSide.correctDemo,
          mediaUrl: curated?.correctDemo?.mediaUrl ?? base.actionCard.learningSide.correctDemo.mediaUrl,
        },
        steps: steps.length ? steps : base.actionCard.learningSide.steps,
        keyReminders: [{ text: tip, evidenceIds: [`business-${card.id}`] }],
        commonErrors: (curated?.errorDemos ?? []).map((media, index) => {
          const fallback = base.actionCard.learningSide.commonErrors[index];
          return fallback ? {
            ...fallback,
            errorDemo: { ...fallback.errorDemo, mediaUrl: media.mediaUrl },
          } : null;
        }).filter((item): item is NonNullable<typeof item> => item !== null),
      },
      trainingSide: {
        ...base.actionCard.trainingSide,
        loopDemo: {
          ...base.actionCard.trainingSide.loopDemo,
          mediaUrl: curated?.correctDemo?.mediaUrl ?? base.actionCard.trainingSide.loopDemo.mediaUrl,
        },
        quickCue: { text: cue, evidenceIds: [`business-${card.id}`] },
        quickTips: [{ text: tip, evidenceIds: [`business-${card.id}`] }],
      },
    },
    provider: { name: "gofit-business", version: "0.1.0" },
    contentSource: "SEED_DEMO",
    sourceMediaUrl: typeof card.cardData.sourceMediaUrl === "string" ? card.cardData.sourceMediaUrl : undefined,
  });
}

export function toFrontendPlan(plan: BusinessTrainingPlan): Plan {
  return {
    id: plan.id,
    name: plan.name,
    cardIds: plan.items.map((item) => item.cardId),
    itemIdsByCardId: Object.fromEntries(plan.items.map((item) => [item.cardId, item.id])),
    updatedAt: plan.updatedAt,
    useCount: plan.useCount,
  };
}

function itemState(status: string): TrainingSession["items"][number]["state"] {
  if (status === "COMPLETED") return "COMPLETED";
  if (status === "SKIPPED") return "SKIPPED";
  if (status === "STOPPED_FOR_DISCOMFORT") return "STOPPED_DISCOMFORT";
  return "NOT_STARTED";
}

export function toFrontendSession(session: BusinessTrainingSession): TrainingSession {
  return {
    id: session.id,
    planId: session.planId,
    planName: session.planName,
    status: session.status === "COMPLETED" ? "COMPLETED" : session.status === "ENDED" ? "ENDED" : "IN_PROGRESS",
    currentIndex: Math.max(0, Math.min(session.currentIndex, Math.max(session.items.length - 1, 0))),
    startedAt: session.startedAt,
    items: session.items.map((item) => ({
      id: item.id,
      cardId: item.cardId,
      state: itemState(item.itemStatus),
      sensation: (item.feedbackType as Sensation | null) ?? undefined,
      feltRegion: item.feltMuscles[0],
    })),
  };
}

export function toFrontendExperienceGroups(result: BusinessExperienceResult): ExperienceGroup[] {
  return result.groups.map((group) => ({
    id: group.id,
    title: group.methodName,
    summary: group.summary,
    mentions: group.mentionCount,
    sourceVideos: group.sourceVideoCount,
    disagreement: group.hasDisagreement ? "不同练友的体感可能不同，请以自己的舒适范围为准。" : "暂未发现明显分歧。",
    comments: group.comments.map((comment) => ({
      id: comment.id,
      content: comment.content,
      videoTitle: comment.sourceVideo.title,
      creatorName: comment.authorName,
    })),
  }));
}

export const businessApi = {
  health: () => request<{ status: string; service: string; ai_center: string }>("/health"),
  listActionCards: async () => (await request<{ items: BusinessActionCard[] }>(`/action-cards${import.meta.env.VITE_ENABLE_DEMO_FALLBACK === "true" ? "?includeDemo=true" : ""}`)).items,
  getActionCard: (cardId: string) => request<BusinessActionCard>(`/action-cards/${encodeURIComponent(cardId)}${import.meta.env.VITE_ENABLE_DEMO_FALLBACK === "true" ? "?includeDemo=true" : ""}`),
  setCardSaved: (cardId: string, saved: boolean) => request<BusinessActionCard>(`/action-cards/${encodeURIComponent(cardId)}/saved`, { method: saved ? "POST" : "DELETE" }),
  listPlans: () => request<PlanListResponse>("/plans"),
  createPlan: (name?: string, initialCardId?: string) => request<BusinessTrainingPlan>("/plans", {
    method: "POST",
    body: JSON.stringify({ name, initialCardId }),
  }),
  updatePlan: (planId: string, payload: { name?: string; status?: string; orderedItemIds?: string[] }) => request<BusinessTrainingPlan>(`/plans/${encodeURIComponent(planId)}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  }),
  addPlanItem: (planId: string, cardId: string) => request<BusinessTrainingPlan>(`/plans/${encodeURIComponent(planId)}/items`, {
    method: "POST",
    body: JSON.stringify({ cardId }),
  }),
  deletePlanItem: (planId: string, itemId: string) => request<BusinessTrainingPlan>(`/plans/${encodeURIComponent(planId)}/items/${encodeURIComponent(itemId)}`, { method: "DELETE" }),
  recommendations: (planId: string) => request<BusinessRecommendationResult>(`/recommendations?planId=${encodeURIComponent(planId)}`),
  createSession: (planId: string) => request<BusinessTrainingSession>(`/plans/${encodeURIComponent(planId)}/sessions`, { method: "POST" }),
  getSession: (sessionId: string) => request<BusinessTrainingSession>(`/sessions/${encodeURIComponent(sessionId)}`),
  updateSessionItem: (sessionId: string, itemId: string, payload: { itemStatus?: string; feedbackType?: Sensation; feltMuscles?: string[] }) => request<BusinessTrainingSession>(`/sessions/${encodeURIComponent(sessionId)}/items/${encodeURIComponent(itemId)}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  }),
  submitFeedback: (sessionId: string, itemId: string, feedbackType: Sensation, feltMuscles: string[] = []) => request<FeedbackResult>(`/sessions/${encodeURIComponent(sessionId)}/feedback`, {
    method: "POST",
    body: JSON.stringify({ itemId, feedbackType, feltMuscles }),
  }),
  endSession: (sessionId: string) => request<BusinessTrainingSession>(`/sessions/${encodeURIComponent(sessionId)}/end`, { method: "POST" }),
  experiences: (exerciseId: string, problemTag = "ARMS_FELT_MORE", currentVideoId?: string, fromTraining = false) => {
    const params = new URLSearchParams({ exerciseId: standardActionAliases[exerciseId] ?? exerciseId, problemTag, fromTraining: String(fromTraining) });
    if (currentVideoId) params.set("currentVideoId", currentVideoId);
    return request<BusinessExperienceResult>(`/experiences?${params}`);
  },
  me: () => request<BusinessMeSummary>("/me"),
  importVideo: (payload: { videoId: string; title?: string; creatorName?: string; sourceUrl?: string; assetFileName?: string }) => request<{ videoId: string; taskId: string; status: string; cardId: string | null; message: string; mediaUrl: string | null; contentSource: string | null; fallbackReason: string | null }>("/videos/import", {
    method: "POST",
    body: JSON.stringify(payload),
  }),
  processingStatus: (videoId: string) => request<{ taskId: string; videoId: string; status: string; cardId: string | null; errorMessage: string | null; contentSource: string | null; fallbackReason: string | null }>(`/videos/${encodeURIComponent(videoId)}/processing`),
};

import { describe, expect, it } from "vitest";
import { toFrontendActionCard, toFrontendPlan, type BusinessActionCard, type BusinessTrainingPlan } from "./business-api";

const businessCard: BusinessActionCard = {
  id: "lateral-raise",
  videoId: "video_lateral_raise",
  exerciseId: "exercise_lateral_raise",
  actionName: "哑铃侧平举",
  bodyRegion: "肩部",
  primaryMuscles: ["三角肌中束"],
  secondaryMuscles: ["三角肌前束"],
  equipment: ["哑铃"],
  status: "READY",
  cardData: {
    cue: "肩放松 → 肘带动 → 缓慢落",
    steps: [["站稳", "00:08"], ["肘部向外打开", "00:16"]],
    tip: "保持肩膀下沉",
  },
  sourceVideo: {
    id: "video_lateral_raise",
    title: "侧平举教学",
    creatorName: "测试教练",
    sourceUrl: "https://example.test/lateral-raise",
    coverUrl: null,
  },
  isSaved: false,
  experienceSummary: null,
};

describe("Business API adapters", () => {
  it("maps a business action card to the frontend AI card contract", () => {
    const result = toFrontendActionCard(businessCard);

    expect(result.actionCard.sourceVideo.videoId).toBe("lateral-raise");
    expect(result.standardAction.standardActionId).toBe("exercise_lateral_raise");
    expect(result.actionCard.trainingSide.quickCue.text).toContain("肘带动");
    expect(result.actionCard.learningSide.steps[0]?.startMs).toBe(8000);
    expect(result.provider.name).toBe("gofit-business");
  });

  it("preserves a real AI result and attaches only curated media URLs", () => {
    const correct = { kind: "CORRECT_DEMO", candidateId: "human-correct", startMs: 8000, endMs: 14000, evidenceIds: ["vision-1"] };
    const errorDemo = { kind: "ERROR_DEMO", candidateId: "human-error", startMs: 20000, endMs: 24000, evidenceIds: ["vision-2"] };
    const realCard: BusinessActionCard = {
      ...businessCard,
      id: "ai-real-card",
      cardData: {
        contentSource: "AI",
        sourceMediaUrl: "/api/v1/media/videos/original.mp4",
        curatedMedia: {
          correctDemo: { candidateId: "human-correct", mediaUrl: "/api/v1/media/curated/action/correct.mp4" },
          errorDemos: [{ candidateId: "human-error", mediaUrl: "/api/v1/media/curated/action/error.mp4" }],
        },
        aiResult: {
          schemaVersion: "1.1.0",
          requestId: "real-request",
          status: "READY",
          standardAction: { standardActionId: "action_lateral_raise", confidence: 0.98, decision: "MATCHED" },
          actionCard: {
            sourceVideo: { videoId: "video-fingerprint", title: "真实视频", creatorName: "真实作者", sourceUrl: "https://example.test/real" },
            actionName: "哑铃侧平举",
            bodyRegion: "肩部",
            primaryMuscles: ["三角肌中束"],
            secondaryMuscles: ["三角肌前束"],
            equipment: ["哑铃"],
            learningSide: {
              correctDemo: correct,
              steps: [1, 2, 3].map((order) => ({ order, instruction: `真实步骤 ${order}`, startMs: 8000, endMs: 10000, evidenceIds: ["vision-1"] })),
              keyReminders: [{ text: "真实提醒", evidenceIds: ["vision-1"] }],
              commonErrors: [{ mistake: "真实错误", correction: "真实纠正", errorDemo, evidenceIds: ["vision-2"] }],
            },
            trainingSide: { loopDemo: correct, quickCue: { text: "真实暗号", evidenceIds: ["vision-1"] }, quickTips: [{ text: "真实提示", evidenceIds: ["vision-1"] }] },
          },
          warnings: [],
          needsReviewReasons: [],
          provider: { name: "dashscope", version: "1" },
        },
      },
    };

    const result = toFrontendActionCard(realCard);

    expect(result.actionCard.learningSide.steps[0]?.instruction).toBe("真实步骤 1");
    expect(result.actionCard.learningSide.correctDemo.mediaUrl).toContain("correct.mp4");
    expect(result.actionCard.trainingSide.loopDemo.mediaUrl).toContain("correct.mp4");
    expect(result.actionCard.learningSide.commonErrors[0]?.errorDemo.mediaUrl).toContain("error.mp4");
    expect(result.contentSource).toBe("AI");
    expect(result.provider.name).toBe("dashscope");
  });

  it("keeps backend plan-item ids for delete and reorder mutations", () => {
    const plan: BusinessTrainingPlan = {
      id: "plan_1",
      userId: "demo_user_001",
      name: "今天练肩",
      status: "SAVED",
      itemCount: 1,
      bodyRegions: ["肩部"],
      cardNames: ["哑铃侧平举"],
      createdAt: "2026-07-22T00:00:00Z",
      updatedAt: "2026-07-22T00:00:00Z",
      lastUsedAt: null,
      useCount: 0,
      items: [{ id: "plan_item_1", cardId: "lateral-raise", sortOrder: 0, card: businessCard }],
    };

    expect(toFrontendPlan(plan)).toMatchObject({
      cardIds: ["lateral-raise"],
      itemIdsByCardId: { "lateral-raise": "plan_item_1" },
    });
  });
});

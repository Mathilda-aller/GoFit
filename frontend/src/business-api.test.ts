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
    expect(result.standardAction.standardActionId).toBe("action_lateral_raise");
    expect(result.actionCard.trainingSide.quickCue.text).toContain("肘带动");
    expect(result.actionCard.learningSide.steps[0]?.startMs).toBe(8000);
    expect(result.provider.name).toBe("gofit-business");
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

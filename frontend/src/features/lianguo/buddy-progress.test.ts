import { describe, expect, it } from "vitest";
import {
  BUDDY_XP_PER_TRAINING,
  completeBuddyProgress,
  DEFAULT_BUDDY_PROGRESS,
  equipBuddyItem,
  getBuddyTrainingCount,
  purchaseBuddyItem,
} from "./buddy-progress";
import { DEFAULT_SHOP_ITEMS } from "./kit";

const item = (id: string) => {
  const result = DEFAULT_SHOP_ITEMS.find((candidate) => candidate.id === id);
  if (!result) throw new Error(`Missing test shop item: ${id}`);
  return result;
};

describe("buddy progress", () => {
  it("adds XP and a recent record when completing training", () => {
    const result = completeBuddyProgress(DEFAULT_BUDDY_PROGRESS, "2026-07-23T10:00:00+08:00");

    expect(result.totalTrainingXp).toBe(BUDDY_XP_PER_TRAINING);
    expect(result.availableXp).toBe(BUDDY_XP_PER_TRAINING);
    expect(result.recentTrainings[0]).toMatchObject({
      completedAt: "2026-07-23T10:00:00+08:00",
      xp: BUDDY_XP_PER_TRAINING,
      title: "搭子小练打卡",
    });
    expect(getBuddyTrainingCount(result)).toBe(1);
  });

  it("derives cumulative count independently of the recent-record limit", () => {
    const progress = {
      ...DEFAULT_BUDDY_PROGRESS,
      totalTrainingXp: 1500,
      recentTrainings: Array.from({ length: 7 }, (_, index) => ({
        id: `training-${index}`,
        completedAt: "2026-07-23T10:00:00+08:00",
        xp: BUDDY_XP_PER_TRAINING,
      })),
    };

    expect(getBuddyTrainingCount(progress)).toBe(10);
  });

  it("purchases an item with available XP without reducing total XP", () => {
    const progress = {
      ...DEFAULT_BUDDY_PROGRESS,
      totalTrainingXp: 600,
      availableXp: 600,
    };
    const result = purchaseBuddyItem(progress, item("clothing-yoga-set"));

    expect(result.totalTrainingXp).toBe(600);
    expect(result.availableXp).toBe(0);
    expect(result.ownedItemIds).toContain("clothing-yoga-set");
  });

  it("does not change progress when XP is insufficient", () => {
    const progress = {
      ...DEFAULT_BUDDY_PROGRESS,
      availableXp: 149,
    };

    expect(() => purchaseBuddyItem(progress, item("hat-cap"))).toThrow("还差 1 XP");
    expect(progress.ownedItemIds).not.toContain("hat-cap");
  });

  it("equips only the purchased item category", () => {
    const progress = {
      ...DEFAULT_BUDDY_PROGRESS,
      ownedItemIds: [...DEFAULT_BUDDY_PROGRESS.ownedItemIds, "hair-ponytail"],
    };
    const result = equipBuddyItem(progress, item("hair-ponytail"));

    expect(result.equippedOutfit).toEqual({
      ...DEFAULT_BUDDY_PROGRESS.equippedOutfit,
      hairItemId: "hair-ponytail",
    });
  });
});

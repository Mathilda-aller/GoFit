import { DEFAULT_OUTFIT, type EquippedOutfit, type ShopItem, type TrainingRecord } from "./kit";

export const BUDDY_XP_PER_TRAINING = 150;
const MAX_RECENT_TRAININGS = 7;

export type BuddyProgress = {
  totalTrainingXp: number;
  availableXp: number;
  ownedItemIds: string[];
  equippedOutfit: EquippedOutfit;
  recentTrainings: TrainingRecord[];
};

export const DEFAULT_BUDDY_PROGRESS: BuddyProgress = {
  totalTrainingXp: 0,
  availableXp: 0,
  ownedItemIds: [
    DEFAULT_OUTFIT.clothingItemId,
    DEFAULT_OUTFIT.hairItemId,
    DEFAULT_OUTFIT.hatItemId,
  ],
  equippedOutfit: DEFAULT_OUTFIT,
  recentTrainings: [],
};

export function getBuddyTrainingCount(progress: BuddyProgress): number {
  return Math.floor(progress.totalTrainingXp / BUDDY_XP_PER_TRAINING);
}

export function completeBuddyProgress(
  progress: BuddyProgress,
  completedAt = new Date().toISOString(),
): BuddyProgress {
  const record: TrainingRecord = {
    id: `buddy_training_${Date.now()}`,
    title: "搭子小练打卡",
    completedAt,
    xp: BUDDY_XP_PER_TRAINING,
  };
  return {
    ...progress,
    totalTrainingXp: progress.totalTrainingXp + BUDDY_XP_PER_TRAINING,
    availableXp: progress.availableXp + BUDDY_XP_PER_TRAINING,
    recentTrainings: [record, ...progress.recentTrainings].slice(0, MAX_RECENT_TRAININGS),
  };
}

export function purchaseBuddyItem(progress: BuddyProgress, item: ShopItem): BuddyProgress {
  if (progress.ownedItemIds.includes(item.id)) return progress;
  if (progress.availableXp < item.price) {
    throw new Error(`还差 ${item.price - progress.availableXp} XP 才能解锁 ${item.name}`);
  }
  return {
    ...progress,
    availableXp: progress.availableXp - item.price,
    ownedItemIds: [...progress.ownedItemIds, item.id],
  };
}

export function equipBuddyItem(progress: BuddyProgress, item: ShopItem): BuddyProgress {
  if (!progress.ownedItemIds.includes(item.id)) {
    throw new Error("请先解锁后再穿戴");
  }
  if (item.category === "clothing") {
    return { ...progress, equippedOutfit: { ...progress.equippedOutfit, clothingItemId: item.id } };
  }
  if (item.category === "hair") {
    return { ...progress, equippedOutfit: { ...progress.equippedOutfit, hairItemId: item.id } };
  }
  return { ...progress, equippedOutfit: { ...progress.equippedOutfit, hatItemId: item.id } };
}

import { DEFAULT_OUTFIT, DEFAULT_SHOP_ITEMS, XP_PER_TRAINING } from './defaults'
import type { EquippedOutfit, ItemCategory, ShopItem, TrainingRecord } from './types'

export interface InternalFitnessState {
  totalTrainingCount: number
  totalTrainingXp: number
  availableXp: number
  ownedItemIds: string[]
  equippedOutfit: EquippedOutfit
  recentTrainings: TrainingRecord[]
}

export const createInitialInternalState = (items: ShopItem[] = DEFAULT_SHOP_ITEMS): InternalFitnessState => ({
  totalTrainingCount: 0,
  totalTrainingXp: 0,
  availableXp: 0,
  ownedItemIds: items.filter((item) => item.price === 0).map((item) => item.id),
  equippedOutfit: { ...DEFAULT_OUTFIT },
  recentTrainings: [],
})

export const completeInternalTraining = (
  state: InternalFitnessState,
  xpPerTraining = XP_PER_TRAINING,
  completedAt = new Date().toISOString(),
): InternalFitnessState => {
  const count = state.totalTrainingCount + 1
  return {
    ...state,
    totalTrainingCount: count,
    totalTrainingXp: state.totalTrainingXp + xpPerTraining,
    availableXp: state.availableXp + xpPerTraining,
    recentTrainings: [{ id: `training-${count}-${completedAt}`, completedAt, xp: xpPerTraining }, ...state.recentTrainings].slice(0, 7),
  }
}

export const purchaseInternalItem = (state: InternalFitnessState, item: ShopItem): InternalFitnessState => {
  if (state.ownedItemIds.includes(item.id)) return state
  if (state.availableXp < item.price) return state
  return {
    ...state,
    availableXp: state.availableXp - item.price,
    ownedItemIds: [...state.ownedItemIds, item.id],
  }
}

const outfitKey = (category: ItemCategory): keyof EquippedOutfit => {
  if (category === 'clothing') return 'clothingItemId'
  if (category === 'hair') return 'hairItemId'
  return 'hatItemId'
}

export const equipInternalItem = (state: InternalFitnessState, item: ShopItem): InternalFitnessState => {
  if (!state.ownedItemIds.includes(item.id)) return state
  return {
    ...state,
    equippedOutfit: { ...state.equippedOutfit, [outfitKey(item.category)]: item.id },
  }
}

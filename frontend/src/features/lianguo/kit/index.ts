export { LianguoFitness, default } from './LianguoFitness'
export { MuscleAvatar } from './components/MuscleAvatar'
export type { MuscleAvatarProps } from './components/MuscleAvatar'
export { BODY_ANCHORS, getBodyProportions, getHandBounds, getHandGeometry, getLegGeometry, getMuscleStageMetrics } from './components/muscleMetrics'
export type { HandBounds, HandGeometry, MuscleStageMetrics } from './components/muscleMetrics'
export { DEFAULT_OUTFIT, DEFAULT_SHOP_ITEMS, calculateGrowth, calculateLevel, getLevelFromXp, MAX_LEVEL, XP_PER_TRAINING } from './defaults'
export { addOptimisticTraining, EMPTY_OPTIMISTIC_TRAINING, reconcileOptimisticTraining, rollbackOptimisticTraining } from './optimistic'
export { completeInternalTraining, createInitialInternalState, equipInternalItem, purchaseInternalItem } from './internalState'
export type { InternalFitnessState } from './internalState'
export type { OptimisticTrainingState, TrainingTotals } from './optimistic'
export type {
  AsyncCallback,
  AvatarOutfit,
  ClothingStyle,
  EquippedOutfit,
  HairStyle,
  HatStyle,
  ItemCallback,
  ItemCategory,
  InternalLianguoFitnessProps,
  ControlledLianguoFitnessProps,
  LianguoFitnessProps,
  LianguoUser,
  ShopItem,
  TrainingRecord,
} from './types'
import './styles/lianguo.css'

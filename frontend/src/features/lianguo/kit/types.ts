export type ItemCategory = 'clothing' | 'hair' | 'hat'
export type ClothingStyle = 'white-tee' | 'sport-tank' | 'long-sleeve' | 'yoga-set' | 'skirt-set'
export type HairStyle = 'american-spikes' | 'textured-part' | 'buzz-cut' | 'ponytail' | 'big-waves' | 'korean-bob'
export type HatStyle = 'none' | 'cap'

export interface LianguoUser {
  id: string
  nickname: string
  avatarUrl?: string
}

export interface EquippedOutfit {
  clothingItemId: string
  hairItemId: string
  hatItemId: string
}

export interface ShopItem {
  id: string
  name: string
  category: ItemCategory
  price: number
  tag?: string
  color: string
  style: ClothingStyle | HairStyle | HatStyle
}

export interface TrainingRecord {
  id: string
  completedAt: string
  title?: string
  xp?: number
}

export type AsyncCallback<T = void> = () => T | Promise<T>
export type ItemCallback<T = void> = (item: ShopItem) => T | Promise<T>

interface CommonFitnessProps {
  shopItems?: ShopItem[]
  xpPerTraining?: number
  onClose?: AsyncCallback
  loading?: boolean
  disabled?: boolean
  errorMessage?: string
  className?: string
}

/** 默认的纯前端模式。所有业务状态仅保存在当前组件实例的内存中。 */
export interface InternalLianguoFitnessProps extends CommonFitnessProps {
  stateMode?: 'internal'
  user?: LianguoUser
}

/** 由宿主提供全部业务状态的高级模式，适合 API/Bridge 接入。 */
export interface ControlledLianguoFitnessProps extends CommonFitnessProps {
  stateMode: 'controlled'
  user: LianguoUser
  totalTrainingCount: number
  totalTrainingXp: number
  availableXp: number
  level?: number
  ownedItemIds: string[]
  equippedOutfit: EquippedOutfit
  recentTrainings: TrainingRecord[]
  /** 提交期间立即展示本次成长；默认 true。宿主仍须回传最新业务状态。 */
  optimistic?: boolean
  onCompleteTraining: AsyncCallback
  onPurchaseItem: ItemCallback
  onEquipItem: ItemCallback
  onRestart?: AsyncCallback
}

export type LianguoFitnessProps = InternalLianguoFitnessProps | ControlledLianguoFitnessProps

export interface AvatarOutfit {
  clothingStyle: ClothingStyle
  hairStyle: HairStyle
  hairColor: string
  hatStyle: HatStyle
  hatColor: string
}

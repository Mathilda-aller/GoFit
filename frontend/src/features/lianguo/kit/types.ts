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

export interface LianguoFitnessProps {
  user: LianguoUser
  totalTrainingCount: number
  totalTrainingXp: number
  availableXp: number
  level?: number
  ownedItemIds: string[]
  equippedOutfit: EquippedOutfit
  recentTrainings: TrainingRecord[]
  shopItems?: ShopItem[]
  xpPerTraining?: number
  onCompleteTraining: AsyncCallback
  onPurchaseItem: ItemCallback
  onEquipItem: ItemCallback
  onClose?: AsyncCallback
  loading?: boolean
  disabled?: boolean
  errorMessage?: string
  className?: string
}

export interface AvatarOutfit {
  clothingStyle: ClothingStyle
  hairStyle: HairStyle
  hairColor: string
  hatStyle: HatStyle
  hatColor: string
}

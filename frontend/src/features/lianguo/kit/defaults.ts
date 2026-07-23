import type { EquippedOutfit, ShopItem } from './types'

export const MAX_LEVEL = 7
export const DEFAULT_OUTFIT: EquippedOutfit = {
  clothingItemId: 'clothing-sport-tank',
  hairItemId: 'hair-buzz-cut',
  hatItemId: 'hat-none',
}

export const DEFAULT_SHOP_ITEMS: ShopItem[] = [
  { id: 'clothing-sport-tank', name: '运动背心', price: 0, color: '#ff376d', category: 'clothing', style: 'sport-tank', tag: '默认拥有' },
  { id: 'clothing-white-tee', name: '白色短袖 T 恤', price: 300, color: '#fff', category: 'clothing', style: 'white-tee', tag: '清爽百搭' },
  { id: 'clothing-long-sleeve', name: '运动长袖', price: 450, color: '#26364d', category: 'clothing', style: 'long-sleeve', tag: '藏蓝卫衣' },
  { id: 'clothing-yoga-set', name: '莫兰迪瑜伽套装', price: 600, color: '#7d83b5', category: 'clothing', style: 'yoga-set', tag: '一体修身' },
  { id: 'clothing-skirt-set', name: '粉白短裙套装', price: 750, color: '#f29ab6', category: 'clothing', style: 'skirt-set', tag: '轻盈 A 字' },
  { id: 'hair-buzz-cut', name: '寸头', price: 0, color: '#211b19', category: 'hair', style: 'buzz-cut', tag: '默认拥有' },
  { id: 'hair-american-spikes', name: '美式前刺', price: 300, color: '#211b19', category: 'hair', style: 'american-spikes', tag: '立体前刺' },
  { id: 'hair-textured-part', name: '微分碎盖', price: 450, color: '#251d1a', category: 'hair', style: 'textured-part', tag: '蓬松碎盖' },
  { id: 'hair-ponytail', name: '高扎马尾', price: 600, color: '#4a3028', category: 'hair', style: 'ponytail', tag: '轻盈利落' },
  { id: 'hair-big-waves', name: '丰盈大波浪', price: 750, color: '#54352c', category: 'hair', style: 'big-waves', tag: '丰盈卷发' },
  { id: 'hair-korean-bob', name: '韩式短发', price: 450, color: '#493129', category: 'hair', style: 'korean-bob', tag: '轻盈内扣' },
  { id: 'hat-none', name: '不戴帽子', price: 0, color: '#f8fafc', category: 'hat', style: 'none', tag: '清爽' },
  { id: 'hat-cap', name: '训练鸭舌帽', price: 150, color: '#161d2a', category: 'hat', style: 'cap', tag: '街头' },
]

export const XP_PER_TRAINING = 150

/** 0 XP 为 Lv.1；每 150 XP 提升一级，900 XP 起为 Lv.7，之后 XP 继续累计。 */
export const calculateLevel = (xp: number, xpPerTraining = XP_PER_TRAINING): number => {
  const step = Math.max(1, xpPerTraining)
  return Math.min(MAX_LEVEL, Math.max(1, Math.floor(Math.max(0, xp) / step) + 1))
}

/** 返回七个离散成长阶段：0、1/6、2/6、3/6、4/6、5/6、1。 */
export const calculateGrowth = (xp: number, xpPerTraining = XP_PER_TRAINING): number =>
  (calculateLevel(xp, xpPerTraining) - 1) / (MAX_LEVEL - 1)

/** @deprecated 请使用 calculateLevel。 */
export const getLevelFromXp = calculateLevel

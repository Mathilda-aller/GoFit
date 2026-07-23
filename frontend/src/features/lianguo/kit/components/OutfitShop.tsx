import type { AvatarOutfit, EquippedOutfit, ItemCategory, ShopItem } from '../types'
import { MuscleAvatar } from './MuscleAvatar'

interface OutfitShopProps {
  items: ShopItem[]
  ownedItemIds: string[]
  equippedOutfit: EquippedOutfit
  outfit: AvatarOutfit
  growth: number
  availableXp: number
  busyItemId?: string
  disabled: boolean
  onPurchase: (item: ShopItem) => void
  onEquip: (item: ShopItem) => void
  onBack: () => void
}

const categories: Array<[ItemCategory, string]> = [['clothing', '一体化服装'], ['hair', '发型'], ['hat', '帽子']]
const equippedId = (outfit: EquippedOutfit, category: ItemCategory) =>
  category === 'clothing' ? outfit.clothingItemId : category === 'hair' ? outfit.hairItemId : outfit.hatItemId

export function OutfitShop(props: OutfitShopProps) {
  const previewOutfit = (item: ShopItem): AvatarOutfit => {
    if (item.category === 'clothing') return { ...props.outfit, clothingStyle: item.style as AvatarOutfit['clothingStyle'] }
    if (item.category === 'hair') return { ...props.outfit, hairStyle: item.style as AvatarOutfit['hairStyle'], hairColor: item.color }
    return { ...props.outfit, hatStyle: item.style as AvatarOutfit['hatStyle'], hatColor: item.color }
  }
  return <section className="lianguo-shop">
    <header className="lianguo-shop-header">
      <div><span className="lianguo-eyebrow">成长衣橱</span><h2>卡通换装商店</h2><p>用训练获得的 XP 解锁搭配，成长等级不会因消费降低。</p></div>
      <div className="lianguo-wallet">✦ {props.availableXp} XP</div>
    </header>
    <div className="lianguo-shop-layout">
      <aside className="lianguo-shop-preview">
        <MuscleAvatar growth={props.growth} outfit={props.outfit} />
        <button type="button" onClick={props.onBack}>回到训练</button>
      </aside>
      <div className="lianguo-shop-grid">
        {categories.map(([category, label]) => <section className="lianguo-shop-category" key={category}>
          <h3>{label}</h3>
          <div className="lianguo-item-list">
            {props.items.filter((item) => item.category === category).map((item) => {
              const owned = props.ownedItemIds.includes(item.id)
              const equipped = equippedId(props.equippedOutfit, category) === item.id
              const locked = !owned && props.availableXp < item.price
              const busy = props.busyItemId === item.id
              return <button className={`lianguo-item ${equipped ? 'lianguo-item-equipped' : ''}`} key={item.id} type="button"
                disabled={props.disabled || busy || locked} onClick={() => owned ? props.onEquip(item) : props.onPurchase(item)}>
                <div className="lianguo-item-preview"><MuscleAvatar growth={props.growth} outfit={previewOutfit(item)} /></div>
                <span className="lianguo-item-tag">{item.tag}</span><strong>{item.name}</strong>
                <small>{busy ? '正在处理…' : equipped ? '穿戴中' : owned ? '点击穿戴' : locked ? `还差 ${item.price - props.availableXp} XP` : `${item.price} XP 解锁`}</small>
              </button>
            })}
          </div>
        </section>)}
      </div>
    </div>
  </section>
}

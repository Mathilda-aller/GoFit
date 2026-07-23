import { useMemo, useState } from 'react'
import { ArrowLeft } from 'lucide-react'
import { DEFAULT_SHOP_ITEMS, getLevelFromXp, MAX_LEVEL } from './defaults'
import type { AvatarOutfit, ItemCategory, LianguoFitnessProps, ShopItem } from './types'
import { OutfitShop } from './components/OutfitShop'
import { ProgressPanel } from './components/ProgressPanel'
import { TrainingFeedback, type FeedbackState } from './components/TrainingFeedback'
import { TrainingPanel } from './components/TrainingPanel'
import './styles/lianguo.css'

const itemFor = (items: ShopItem[], id: string, category: ItemCategory) =>
  items.find((item) => item.id === id && item.category === category) ?? items.find((item) => item.category === category)

const errorText = (error: unknown) => error instanceof Error ? error.message : '操作未完成，请稍后重试'

export function LianguoFitness({
  user,
  totalTrainingCount,
  totalTrainingXp,
  availableXp,
  level: controlledLevel,
  ownedItemIds,
  equippedOutfit,
  recentTrainings,
  shopItems = DEFAULT_SHOP_ITEMS,
  xpPerTraining = 150,
  onCompleteTraining,
  onPurchaseItem,
  onEquipItem,
  onClose,
  loading = false,
  disabled = false,
  errorMessage,
  className = '',
}: LianguoFitnessProps) {
  const [view, setView] = useState<'training' | 'shop'>('training')
  const [feedback, setFeedback] = useState<FeedbackState>({ kind: 'idle' })
  const [busyItemId, setBusyItemId] = useState<string>()
  const [trainingBusy, setTrainingBusy] = useState(false)
  const [animationKey, setAnimationKey] = useState(0)
  const level = controlledLevel ?? getLevelFromXp(totalTrainingXp, xpPerTraining)
  const growth = (Math.min(MAX_LEVEL, Math.max(1, level)) - 1) / (MAX_LEVEL - 1)
  const progress = Math.min(1, totalTrainingCount / MAX_LEVEL)
  const isDisabled = loading || disabled

  const outfit = useMemo<AvatarOutfit>(() => {
    const clothing = itemFor(shopItems, equippedOutfit.clothingItemId, 'clothing')
    const hair = itemFor(shopItems, equippedOutfit.hairItemId, 'hair')
    const hat = itemFor(shopItems, equippedOutfit.hatItemId, 'hat')
    return {
      clothingStyle: (clothing?.style ?? 'sport-tank') as AvatarOutfit['clothingStyle'],
      hairStyle: (hair?.style ?? 'buzz-cut') as AvatarOutfit['hairStyle'],
      hairColor: hair?.color ?? '#211b19',
      hatStyle: (hat?.style ?? 'none') as AvatarOutfit['hatStyle'],
      hatColor: hat?.color ?? '#161d2a',
    }
  }, [equippedOutfit, shopItems])

  const completeTraining = async () => {
    setTrainingBusy(true)
    setFeedback({ kind: 'loading', message: '正在记录本次训练…' })
    try {
      await onCompleteTraining()
      setAnimationKey((value) => value + 1)
      setFeedback({ kind: 'success', message: `训练已记录，获得 ${xpPerTraining} XP` })
    } catch (error) {
      setFeedback({ kind: 'error', message: errorText(error) })
    } finally {
      setTrainingBusy(false)
    }
  }

  const runItemAction = async (item: ShopItem, action: (value: ShopItem) => void | Promise<void>, success: string) => {
    setBusyItemId(item.id)
    setFeedback({ kind: 'loading', message: '正在处理搭配…' })
    try {
      await action(item)
      setFeedback({ kind: 'success', message: success })
    } catch (error) {
      setFeedback({ kind: 'error', message: errorText(error) })
    } finally {
      setBusyItemId(undefined)
    }
  }

  const close = async () => {
    if (!onClose) return
    setFeedback({ kind: 'loading', message: '正在返回…' })
    try {
      await onClose()
    } catch (error) {
      setFeedback({ kind: 'error', message: errorText(error) })
    }
  }

  return <div className={`lianguo-root ${className}`} aria-label={`${user.nickname}的搭子中心`}>
    <nav className="lianguo-nav" aria-label="主要导航">
      {onClose ? <button className="lianguo-nav-back" type="button" onClick={() => void close()} aria-label="返回我的页面"><ArrowLeft aria-hidden="true" /><span>返回</span></button> : null}
      <button className={view === 'training' ? 'lianguo-nav-active' : ''} type="button" onClick={() => setView('training')}><span>✦</span>训练</button>
      <button className={view === 'shop' ? 'lianguo-nav-active' : ''} type="button" onClick={() => setView('shop')}><span>▣</span>商店</button>
      <div className="lianguo-nav-xp">{availableXp} XP</div>
    </nav>
    <main className="lianguo-main">
      <TrainingFeedback state={errorMessage ? { kind: 'error', message: errorMessage } : feedback} onDismiss={() => setFeedback({ kind: 'idle' })} />
      {view === 'training' ? <div className="lianguo-training-view">
        <section className="lianguo-intro">
          <span className="lianguo-eyebrow">每次训练，都算成长</span>
          <h1>打卡升级，<br />小人变壮。</h1>
          <p>完成训练会增加累计训练 XP 与可用 XP。商城仅消费可用 XP，不影响角色等级。</p>
          <ProgressPanel count={totalTrainingCount} level={level} totalXp={totalTrainingXp} availableXp={availableXp} progress={progress} />
          <div className="lianguo-mood"><b>今天也练过了</b><span>一点点坚持，也会在角色身上留下变化。</span></div>
        </section>
        <TrainingPanel level={level} growth={growth} outfit={outfit} recentTrainings={recentTrainings} xpPerTraining={xpPerTraining} availableXp={availableXp} animationKey={animationKey} busy={trainingBusy || loading} disabled={disabled} onComplete={() => void completeTraining()} />
        <aside className="lianguo-side-notes"><div><b>成长看得见</b><p>肩背、手臂与腿部会随等级逐步变强。</p></div><div><b>每练一次都到账</b><p>满级后仍可继续获得 XP，解锁喜欢的穿搭。</p></div></aside>
      </div> : <OutfitShop items={shopItems} ownedItemIds={ownedItemIds} equippedOutfit={equippedOutfit} outfit={outfit} growth={growth} availableXp={availableXp} busyItemId={busyItemId} disabled={isDisabled} onPurchase={(item) => void runItemAction(item, onPurchaseItem, `已解锁 ${item.name}`)} onEquip={(item) => void runItemAction(item, onEquipItem, `已穿戴 ${item.name}`)} onBack={() => setView('training')} />}
    </main>
  </div>
}

export default LianguoFitness

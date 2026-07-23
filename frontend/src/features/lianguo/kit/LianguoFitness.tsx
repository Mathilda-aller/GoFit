import { useLayoutEffect, useMemo, useRef, useState } from 'react'
import { ArrowLeft } from 'lucide-react'
import { calculateGrowth, calculateLevel, DEFAULT_SHOP_ITEMS, MAX_LEVEL } from './defaults'
import { completeInternalTraining, createInitialInternalState, equipInternalItem, purchaseInternalItem } from './internalState'
import {
  addOptimisticTraining,
  EMPTY_OPTIMISTIC_TRAINING,
  reconcileOptimisticTraining,
  rollbackOptimisticTraining,
  type TrainingTotals,
} from './optimistic'
import type {
  AvatarOutfit,
  ControlledLianguoFitnessProps,
  EquippedOutfit,
  InternalLianguoFitnessProps,
  ItemCategory,
  LianguoFitnessProps,
  LianguoUser,
  ShopItem,
  TrainingRecord,
} from './types'
import { OutfitShop } from './components/OutfitShop'
import { ProgressPanel } from './components/ProgressPanel'
import { TrainingFeedback, type FeedbackState } from './components/TrainingFeedback'
import { TrainingPanel } from './components/TrainingPanel'
import './styles/lianguo.css'

const DEFAULT_USER: LianguoUser = { id: 'local-user', nickname: '练过用户' }
const itemFor = (items: ShopItem[], id: string, category: ItemCategory) =>
  items.find((item) => item.id === id && item.category === category) ?? items.find((item) => item.category === category)
const errorText = (error: unknown) => error instanceof Error ? error.message : '操作未完成，请稍后重试'

interface FitnessViewProps {
  user: LianguoUser
  totalTrainingCount: number
  totalTrainingXp: number
  availableXp: number
  level?: number
  growth?: number
  ownedItemIds: string[]
  equippedOutfit: EquippedOutfit
  recentTrainings: TrainingRecord[]
  shopItems: ShopItem[]
  xpPerTraining: number
  animationKey: number
  trainingBusy: boolean
  busyItemId?: string
  loading: boolean
  disabled: boolean
  errorMessage?: string
  className: string
  onCompleteTraining: () => void
  onPurchaseItem: (item: ShopItem) => void
  onEquipItem: (item: ShopItem) => void
  onClose?: () => void
  onRestart?: () => void
  feedback: FeedbackState
  onDismissFeedback: () => void
}

function FitnessView(props: FitnessViewProps) {
  const [view, setView] = useState<'training' | 'shop'>('training')
  const level = props.level ?? calculateLevel(props.totalTrainingXp, props.xpPerTraining)
  const growth = props.growth ?? calculateGrowth(props.totalTrainingXp, props.xpPerTraining)
  const progress = Math.min(1, Math.max(0, props.totalTrainingXp) / (props.xpPerTraining * (MAX_LEVEL - 1)))
  const outfit = useMemo<AvatarOutfit>(() => {
    const clothing = itemFor(props.shopItems, props.equippedOutfit.clothingItemId, 'clothing')
    const hair = itemFor(props.shopItems, props.equippedOutfit.hairItemId, 'hair')
    const hat = itemFor(props.shopItems, props.equippedOutfit.hatItemId, 'hat')
    return {
      clothingStyle: (clothing?.style ?? 'sport-tank') as AvatarOutfit['clothingStyle'],
      hairStyle: (hair?.style ?? 'buzz-cut') as AvatarOutfit['hairStyle'],
      hairColor: hair?.color ?? '#211b19',
      hatStyle: (hat?.style ?? 'none') as AvatarOutfit['hatStyle'],
      hatColor: hat?.color ?? '#161d2a',
    }
  }, [props.equippedOutfit, props.shopItems])

  const restart = props.onRestart ? () => {
    props.onRestart?.()
    setView('training')
  } : undefined

  return <div className={`lianguo-root ${props.className}`} aria-label={`${props.user.nickname}的搭子中心`}>
    <nav className="lianguo-nav" aria-label="主要导航">
      {props.onClose ? <button className="lianguo-nav-back" type="button" onClick={props.onClose} aria-label="返回我的页面"><ArrowLeft aria-hidden="true" /><span>返回</span></button> : null}
      <button className={view === 'training' ? 'lianguo-nav-active' : ''} type="button" onClick={() => setView('training')}><span>✦</span>训练</button>
      <button className={view === 'shop' ? 'lianguo-nav-active' : ''} type="button" onClick={() => setView('shop')}><span>▣</span>商店</button>
      <div className="lianguo-nav-xp">{props.availableXp} XP</div>
    </nav>
    <main className="lianguo-main">
      <TrainingFeedback state={props.errorMessage ? { kind: 'error', message: props.errorMessage } : props.feedback} onDismiss={props.onDismissFeedback} />
      {view === 'training' ? <div className="lianguo-training-view">
        <section className="lianguo-intro">
          <span className="lianguo-eyebrow">每次训练，都算成长</span>
          <h1>打卡升级，<br />小人变壮。</h1>
          <p>完成训练会增加累计训练 XP 与可用 XP。商城仅消费可用 XP，不影响角色等级。</p>
          <ProgressPanel count={props.totalTrainingCount} level={level} totalXp={props.totalTrainingXp} availableXp={props.availableXp} progress={progress} xpPerTraining={props.xpPerTraining} />
          <div className="lianguo-mood"><b>今天也练过了</b><span>一点点坚持，也会在角色身上留下变化。</span></div>
        </section>
        <TrainingPanel level={level} growth={growth} outfit={outfit} recentTrainings={props.recentTrainings} xpPerTraining={props.xpPerTraining} availableXp={props.availableXp} animationKey={props.animationKey} busy={props.trainingBusy || props.loading} disabled={props.disabled} onComplete={props.onCompleteTraining} onRestart={restart} />
        <aside className="lianguo-side-notes"><div><b>成长看得见</b><p>肩背、手臂与腿部会随等级逐步变强。</p></div><div><b>每练一次都到账</b><p>满级后仍可继续获得 XP，解锁喜欢的穿搭。</p></div></aside>
      </div> : <OutfitShop items={props.shopItems} ownedItemIds={props.ownedItemIds} equippedOutfit={props.equippedOutfit} outfit={outfit} growth={growth} availableXp={props.availableXp} busyItemId={props.busyItemId} disabled={props.loading || props.disabled} onPurchase={props.onPurchaseItem} onEquip={props.onEquipItem} onBack={() => setView('training')} />}
    </main>
  </div>
}

function InternalLianguoFitness({
  user = DEFAULT_USER,
  shopItems = DEFAULT_SHOP_ITEMS,
  xpPerTraining = 150,
  onClose,
  loading = false,
  disabled = false,
  errorMessage,
  className = '',
}: InternalLianguoFitnessProps) {
  const [state, setState] = useState(() => createInitialInternalState(shopItems))
  const [feedback, setFeedback] = useState<FeedbackState>({ kind: 'idle' })
  const [animationKey, setAnimationKey] = useState(0)

  const complete = () => {
    setState((value) => completeInternalTraining(value, xpPerTraining))
    setAnimationKey((value) => value + 1)
    setFeedback({ kind: 'success', message: `训练已记录，获得 ${xpPerTraining} XP` })
  }
  const purchase = (item: ShopItem) => {
    setState((value) => purchaseInternalItem(value, item))
    setFeedback({ kind: 'success', message: `已解锁 ${item.name}` })
  }
  const equip = (item: ShopItem) => {
    setState((value) => equipInternalItem(value, item))
    setFeedback({ kind: 'success', message: `已穿戴 ${item.name}` })
  }
  const restart = () => {
    setState(createInitialInternalState(shopItems))
    setAnimationKey(0)
    setFeedback({ kind: 'success', message: '已恢复初始状态' })
  }

  return <FitnessView {...state} user={user} shopItems={shopItems} xpPerTraining={xpPerTraining} animationKey={animationKey} trainingBusy={false} loading={loading} disabled={disabled} errorMessage={errorMessage} className={className} onCompleteTraining={complete} onPurchaseItem={purchase} onEquipItem={equip} onClose={onClose ? () => void onClose() : undefined} onRestart={restart} feedback={feedback} onDismissFeedback={() => setFeedback({ kind: 'idle' })} />
}

function ControlledLianguoFitness({
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
  optimistic = true,
  onCompleteTraining,
  onPurchaseItem,
  onEquipItem,
  onRestart,
  onClose,
  loading = false,
  disabled = false,
  errorMessage,
  className = '',
}: ControlledLianguoFitnessProps) {
  const [feedback, setFeedback] = useState<FeedbackState>({ kind: 'idle' })
  const [busyItemId, setBusyItemId] = useState<string>()
  const [trainingBusy, setTrainingBusy] = useState(false)
  const [animationKey, setAnimationKey] = useState(0)
  const [pending, setPending] = useState(EMPTY_OPTIMISTIC_TRAINING)
  const previousControlled = useRef<TrainingTotals>({ count: totalTrainingCount, xp: totalTrainingXp, availableXp })

  useLayoutEffect(() => {
    const previous = previousControlled.current
    const next = { count: totalTrainingCount, xp: totalTrainingXp, availableXp }
    setPending((value) => reconcileOptimisticTraining(value, previous, next))
    previousControlled.current = next
  }, [totalTrainingCount, totalTrainingXp, availableXp])

  const displayCount = totalTrainingCount + (optimistic ? pending.count : 0)
  const displayTotalXp = totalTrainingXp + (optimistic ? pending.xp : 0)
  const displayAvailableXp = availableXp + (optimistic ? pending.availableXp : 0)
  const level = controlledLevel === undefined ? calculateLevel(displayTotalXp, xpPerTraining) : Math.min(MAX_LEVEL, Math.max(1, controlledLevel + (optimistic ? pending.count : 0)))
  const growth = controlledLevel === undefined ? calculateGrowth(displayTotalXp, xpPerTraining) : (level - 1) / (MAX_LEVEL - 1)

  const complete = async () => {
    setTrainingBusy(true)
    setFeedback({ kind: 'loading', message: '正在记录本次训练…' })
    if (optimistic) setPending((value) => addOptimisticTraining(value, xpPerTraining))
    try {
      await onCompleteTraining()
      setAnimationKey((value) => value + 1)
      setFeedback({ kind: 'success', message: `训练已记录，获得 ${xpPerTraining} XP` })
    } catch (error) {
      if (optimistic) setPending((value) => rollbackOptimisticTraining(value, xpPerTraining))
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
  const restart = async () => {
    if (!onRestart) return
    setTrainingBusy(true)
    setFeedback({ kind: 'loading', message: '正在重置搭子…' })
    try {
      await onRestart()
      setPending(EMPTY_OPTIMISTIC_TRAINING)
      setAnimationKey(0)
      setFeedback({ kind: 'success', message: '已重置为 Lv.1' })
    } catch (error) {
      setFeedback({ kind: 'error', message: errorText(error) })
    } finally {
      setTrainingBusy(false)
    }
  }

  return <FitnessView user={user} totalTrainingCount={displayCount} totalTrainingXp={displayTotalXp} availableXp={displayAvailableXp} level={level} growth={growth} ownedItemIds={ownedItemIds} equippedOutfit={equippedOutfit} recentTrainings={recentTrainings} shopItems={shopItems} xpPerTraining={xpPerTraining} animationKey={animationKey} trainingBusy={trainingBusy} busyItemId={busyItemId} loading={loading} disabled={disabled} errorMessage={errorMessage} className={className} onCompleteTraining={() => void complete()} onPurchaseItem={(item) => void runItemAction(item, onPurchaseItem, `已解锁 ${item.name}`)} onEquipItem={(item) => void runItemAction(item, onEquipItem, `已穿戴 ${item.name}`)} onClose={onClose ? () => void close() : undefined} onRestart={onRestart ? () => void restart() : undefined} feedback={feedback} onDismissFeedback={() => setFeedback({ kind: 'idle' })} />
}

export function LianguoFitness(props: LianguoFitnessProps) {
  return props.stateMode === 'controlled' ? <ControlledLianguoFitness {...props} /> : <InternalLianguoFitness {...props} />
}

export default LianguoFitness

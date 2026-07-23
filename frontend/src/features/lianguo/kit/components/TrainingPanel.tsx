import type { AvatarOutfit, TrainingRecord } from '../types'
import { MuscleAvatar } from './MuscleAvatar'

interface TrainingPanelProps {
  level: number
  growth: number
  outfit: AvatarOutfit
  recentTrainings: TrainingRecord[]
  xpPerTraining: number
  availableXp: number
  animationKey: number
  busy: boolean
  disabled: boolean
  onComplete: () => void
  onRestart?: () => void
}

export function TrainingPanel(props: TrainingPanelProps) {
  const filled = Math.min(7, props.recentTrainings.length)
  return <section className="lianguo-phone" aria-label="训练打卡">
    <div className="lianguo-phone-top"><span>练过 Fit</span><b>成长中</b></div>
    <div className="lianguo-phone-title"><span>训练成长伙伴</span><strong>Lv.{props.level}</strong></div>
    <div className="lianguo-avatar-stage">
      <MuscleAvatar growth={props.growth} outfit={props.outfit} animationKey={props.animationKey} />
      <span key={props.animationKey} className="lianguo-gain">+{props.xpPerTraining} XP</span>
    </div>
    <div className="lianguo-training-strip">
      <small>最近 7 次训练</small>
      <div className="lianguo-week-dots">
        {Array.from({ length: 7 }, (_, index) => <span className={index < filled ? 'lianguo-dot-active' : ''} key={index}>{index + 1}</span>)}
      </div>
    </div>
    <button className="lianguo-primary" type="button" onClick={props.onComplete} disabled={props.busy || props.disabled}>
      <span aria-hidden="true">✦</span>{props.busy ? '正在记录…' : `完成训练 +${props.xpPerTraining} XP`}
    </button>
    <small className="lianguo-wallet-note">当前可用 {props.availableXp} XP</small>
    {props.onRestart ? <button className="lianguo-restart" type="button" onClick={props.onRestart} disabled={props.busy || props.disabled} aria-label="重置搭子到 Lv.1">重置为 Lv.1</button> : null}
  </section>
}

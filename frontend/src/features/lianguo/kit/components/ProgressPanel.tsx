interface ProgressPanelProps {
  count: number
  level: number
  totalXp: number
  availableXp: number
  progress: number
}

export function ProgressPanel({ count, level, totalXp, availableXp, progress }: ProgressPanelProps) {
  return <section className="lianguo-progress" aria-label="成长进度">
    <div className="lianguo-metrics">
      <div><b>{count}</b><span>累计训练</span></div>
      <div><b>Lv.{level}</b><span>肌肉阶段</span></div>
      <div><b>{availableXp}</b><span>可用 XP</span></div>
    </div>
    <div className="lianguo-xp-summary">
      <div className="lianguo-xp-row">
        <span>{level >= 5 ? '肌肉成长已满级' : `距离 Lv.${level + 1}`}</span>
        <b>{Math.round(progress * 100)}%</b>
      </div>
      <div className="lianguo-xp-bar"><i style={{ width: `${progress * 100}%` }} /></div>
      <small>累计训练 XP {totalXp} · 商城消费不会降低肌肉等级</small>
    </div>
  </section>
}

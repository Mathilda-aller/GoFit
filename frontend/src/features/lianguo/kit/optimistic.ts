export interface TrainingTotals {
  count: number
  xp: number
  availableXp: number
}

export type OptimisticTrainingState = TrainingTotals

export const EMPTY_OPTIMISTIC_TRAINING: OptimisticTrainingState = {
  count: 0,
  xp: 0,
  availableXp: 0,
}

export const addOptimisticTraining = (
  state: OptimisticTrainingState,
  xpPerTraining: number,
): OptimisticTrainingState => ({
  count: state.count + 1,
  xp: state.xp + xpPerTraining,
  availableXp: state.availableXp + xpPerTraining,
})

export const rollbackOptimisticTraining = (
  state: OptimisticTrainingState,
  xpPerTraining: number,
): OptimisticTrainingState => ({
  count: Math.max(0, state.count - 1),
  xp: Math.max(0, state.xp - xpPerTraining),
  availableXp: Math.max(0, state.availableXp - xpPerTraining),
})

/** Consume only positive controlled-prop changes, independently per field. */
export const reconcileOptimisticTraining = (
  state: OptimisticTrainingState,
  previous: TrainingTotals,
  next: TrainingTotals,
): OptimisticTrainingState => ({
  count: Math.max(0, state.count - Math.max(0, next.count - previous.count)),
  xp: Math.max(0, state.xp - Math.max(0, next.xp - previous.xp)),
  availableXp: Math.max(0, state.availableXp - Math.max(0, next.availableXp - previous.availableXp)),
})

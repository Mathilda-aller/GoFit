export type FeedbackState =
  | { kind: 'idle'; message?: undefined }
  | { kind: 'loading' | 'success' | 'error'; message: string }

export interface TrainingFeedbackProps {
  state: FeedbackState
  onDismiss?: () => void
}

export function TrainingFeedback({ state, onDismiss }: TrainingFeedbackProps) {
  if (state.kind === 'idle') return null
  return <div className={`lianguo-feedback lianguo-feedback-${state.kind}`} role={state.kind === 'error' ? 'alert' : 'status'} aria-live="polite">
    <span className="lianguo-feedback-icon">{state.kind === 'loading' ? '···' : state.kind === 'success' ? '✓' : '!'}</span>
    <span>{state.message}</span>
    {state.kind !== 'loading' && onDismiss ? <button type="button" onClick={onDismiss} aria-label="关闭提示">×</button> : null}
  </div>
}

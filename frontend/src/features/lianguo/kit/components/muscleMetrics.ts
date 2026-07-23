export interface MuscleStageMetrics {
  growth: number
  shoulderWidth: number
  shoulderBulgeHeight: number
  shoulderRoundness: number
  bicepBulge: number
  bicepPeakY: number
  chestBulge: number
  chestLineOpacity: number
  chestLineWidth: number
  waistWidth: number
  thighBulge: number
  calfBulge: number
  muscleDetailOpacity: number
  abCount: 0 | 2 | 4 | 6
}

export interface HandBounds {
  cx: number
  cy: number
  left: number
  right: number
  top: number
  bottom: number
}

export interface HandGeometry {
  left: HandBounds
  right: HandBounds
  leftForearmEnd: { x: number; y: number }
  rightForearmEnd: { x: number; y: number }
  overlap: number
}

export const BODY_ANCHORS = {
  centerX: 160,
  headTop: 35,
  headBottom: 139,
  shoulderY: 149,
  waistY: 216,
  hipY: 229,
  crotchY: 245,
  kneeY: 291,
  ankleY: 347,
  shoeBottomY: 368,
  shadowY: 374,
} as const

const CX = BODY_ANCHORS.centerX
const stageFits: readonly Omit<MuscleStageMetrics, 'growth'>[] = [
  { shoulderWidth: 90, shoulderBulgeHeight: 4.5, shoulderRoundness: 2, bicepBulge: 0, bicepPeakY: 184, chestBulge: 0, chestLineOpacity: 0.08, chestLineWidth: 1.5, waistWidth: 74, thighBulge: 2, calfBulge: 0, muscleDetailOpacity: 0.06, abCount: 0 },
  { shoulderWidth: 98, shoulderBulgeHeight: 5.5, shoulderRoundness: 3, bicepBulge: 2.5, bicepPeakY: 182, chestBulge: 2, chestLineOpacity: 0.16, chestLineWidth: 1.8, waistWidth: 74.5, thighBulge: 3.5, calfBulge: 0.3, muscleDetailOpacity: 0.14, abCount: 0 },
  { shoulderWidth: 106, shoulderBulgeHeight: 6.8, shoulderRoundness: 4.2, bicepBulge: 5, bicepPeakY: 180, chestBulge: 4.5, chestLineOpacity: 0.26, chestLineWidth: 2.1, waistWidth: 75, thighBulge: 5, calfBulge: 0.7, muscleDetailOpacity: 0.24, abCount: 2 },
  { shoulderWidth: 114, shoulderBulgeHeight: 8.2, shoulderRoundness: 5.5, bicepBulge: 7.5, bicepPeakY: 178, chestBulge: 7, chestLineOpacity: 0.38, chestLineWidth: 2.5, waistWidth: 75.5, thighBulge: 6.8, calfBulge: 1.8, muscleDetailOpacity: 0.36, abCount: 2 },
  { shoulderWidth: 124, shoulderBulgeHeight: 10, shoulderRoundness: 7, bicepBulge: 10, bicepPeakY: 176, chestBulge: 9.5, chestLineOpacity: 0.52, chestLineWidth: 2.9, waistWidth: 76, thighBulge: 8.5, calfBulge: 3.2, muscleDetailOpacity: 0.5, abCount: 4 },
  { shoulderWidth: 134, shoulderBulgeHeight: 11.5, shoulderRoundness: 8.5, bicepBulge: 13.5, bicepPeakY: 173, chestBulge: 12.5, chestLineOpacity: 0.68, chestLineWidth: 3.4, waistWidth: 76.5, thighBulge: 10.2, calfBulge: 5, muscleDetailOpacity: 0.66, abCount: 4 },
  { shoulderWidth: 144, shoulderBulgeHeight: 13, shoulderRoundness: 10, bicepBulge: 17, bicepPeakY: 170, chestBulge: 16, chestLineOpacity: 0.84, chestLineWidth: 4, waistWidth: 77, thighBulge: 12, calfBulge: 6.5, muscleDetailOpacity: 0.82, abCount: 6 },
]

const clampGrowth = (growth: number) => Math.min(1, Math.max(0, growth))
const lerp = (from: number, to: number, amount: number) => from + (to - from) * amount
const mirrorX = (x: number) => CX * 2 - x

/** Smoothly interpolates all seven authored fits; discrete ab rows switch at stage boundaries. */
export function getMuscleStageMetrics(growth: number): MuscleStageMetrics {
  const safeGrowth = clampGrowth(growth)
  const stagePosition = safeGrowth * (stageFits.length - 1)
  const fromIndex = Math.floor(stagePosition)
  const toIndex = Math.min(stageFits.length - 1, fromIndex + 1)
  const amount = stagePosition - fromIndex
  const from = stageFits[fromIndex]
  const to = stageFits[toIndex]
  return {
    growth: safeGrowth,
    shoulderWidth: lerp(from.shoulderWidth, to.shoulderWidth, amount),
    shoulderBulgeHeight: lerp(from.shoulderBulgeHeight, to.shoulderBulgeHeight, amount),
    shoulderRoundness: lerp(from.shoulderRoundness, to.shoulderRoundness, amount),
    bicepBulge: lerp(from.bicepBulge, to.bicepBulge, amount),
    bicepPeakY: lerp(from.bicepPeakY, to.bicepPeakY, amount),
    chestBulge: lerp(from.chestBulge, to.chestBulge, amount),
    chestLineOpacity: lerp(from.chestLineOpacity, to.chestLineOpacity, amount),
    chestLineWidth: lerp(from.chestLineWidth, to.chestLineWidth, amount),
    waistWidth: lerp(from.waistWidth, to.waistWidth, amount),
    thighBulge: lerp(from.thighBulge, to.thighBulge, amount),
    calfBulge: lerp(from.calfBulge, to.calfBulge, amount),
    muscleDetailOpacity: lerp(from.muscleDetailOpacity, to.muscleDetailOpacity, amount),
    abCount: amount === 0 ? from.abCount : to.abCount,
  }
}

/** Pure geometry used by SVG and tests. Forearm endpoints sit 2px inside each hand ellipse. */
export function getHandGeometry(growth: number): HandGeometry {
  const metrics = getMuscleStageMetrics(growth)
  const radiusX = 11.5 + metrics.bicepBulge * 0.08
  const radiusY = 12
  const leftCx = 82 - metrics.bicepBulge * 0.16
  const cy = 254
  const left = { cx: leftCx, cy, left: leftCx - radiusX, right: leftCx + radiusX, top: cy - radiusY, bottom: cy + radiusY }
  const right = { cx: mirrorX(left.cx), cy, left: mirrorX(left.right), right: mirrorX(left.left), top: left.top, bottom: left.bottom }
  const overlap = 2
  return {
    left,
    right,
    leftForearmEnd: { x: left.cx, y: left.top + overlap },
    rightForearmEnd: { x: right.cx, y: right.top + overlap },
    overlap,
  }
}

export const getHandBounds = (growth: number) => {
  const { left, right } = getHandGeometry(growth)
  return { left, right }
}

export function getBodyProportions() {
  const headHeight = BODY_ANCHORS.headBottom - BODY_ANCHORS.headTop
  const fullHeight = BODY_ANCHORS.shoeBottomY - BODY_ANCHORS.headTop
  const legSegment = BODY_ANCHORS.shoeBottomY - BODY_ANCHORS.crotchY
  return { headHeight, fullHeight, fullHeightInHeads: fullHeight / headHeight, legSegment, legShare: legSegment / fullHeight }
}

export function getLegGeometry(growth: number) {
  const { thighBulge, calfBulge } = getMuscleStageMetrics(growth)
  const ankleWidth = 18
  return { thighWidth: 24 + thighBulge, calfWidth: 20 + calfBulge, ankleWidth }
}

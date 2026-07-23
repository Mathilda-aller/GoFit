import { useId } from 'react'
import type { AvatarOutfit, ClothingStyle } from '../types'
import { AvatarHair } from './AvatarHair'
import { BODY_ANCHORS, getHandGeometry, getMuscleStageMetrics } from './muscleMetrics'

export interface MuscleAvatarProps {
  growth?: number
  outfit: AvatarOutfit
  animationKey?: number
  className?: string
}

const CX = BODY_ANCHORS.centerX

const outfitColors: Record<ClothingStyle, [string, string, string]> = {
  'white-tee': ['#fff', '#39445a', '#cbd5e1'],
  'sport-tank': ['#ff376d', '#263247', '#b81748'],
  'long-sleeve': ['#26364d', '#1d293b', '#60728c'],
  'yoga-set': ['#7d83b5', '#626b9f', '#aeb3d4'],
  'skirt-set': ['#fff8fb', '#f29ab6', '#d96f95'],
}

export function MuscleAvatar({ growth = 0, outfit, animationKey = 0, className = '' }: MuscleAvatarProps) {
  const id = useId().replaceAll(':', '')
  const metrics = getMuscleStageMetrics(growth)
  const { shoulderWidth, shoulderBulgeHeight, shoulderRoundness, bicepBulge, bicepPeakY, chestBulge, waistWidth, thighBulge, calfBulge } = metrics
  const shoulder = shoulderWidth / 2
  const waist = waistWidth / 2
  const [primary, secondary, detail] = outfitColors[outfit.clothingStyle]
  const skin = `lianguo-skin-${id}`
  const glow = `lianguo-glow-${id}`
  const torsoClip = `lianguo-torso-${id}`
  const longSleeve = outfit.clothingStyle === 'long-sleeve'
  const skirt = outfit.clothingStyle === 'skirt-set'
  const tank = outfit.clothingStyle === 'sport-tank' || outfit.clothingStyle === 'yoga-set'
  const yoga = outfit.clothingStyle === 'yoga-set'
  const longPants = longSleeve || yoga
  const hands = getHandGeometry(metrics.growth)

  const torso = `M${CX - shoulder} ${BODY_ANCHORS.shoulderY} Q${CX - shoulder + shoulderRoundness} ${BODY_ANCHORS.shoulderY - shoulderBulgeHeight} ${tank ? CX - 17 : CX - 23} 146 Q${CX} ${tank ? 169 : 158} ${tank ? CX + 17 : CX + 23} 146 Q${CX + shoulder - shoulderRoundness} ${BODY_ANCHORS.shoulderY - shoulderBulgeHeight} ${CX + shoulder} ${BODY_ANCHORS.shoulderY} C${CX + shoulder + chestBulge} 171 ${CX + waist + 4} 196 ${CX + waist} ${BODY_ANCHORS.hipY} L${CX - waist} ${BODY_ANCHORS.hipY} C${CX - waist - 4} 196 ${CX - shoulder - chestBulge} 171 ${CX - shoulder} ${BODY_ANCHORS.shoulderY}Z`
  const arm = (side: -1 | 1) => {
    const x = (distance: number) => CX + side * distance
    const hand = side === -1 ? hands.left : hands.right
    return `M${x(shoulder - 5)} ${BODY_ANCHORS.shoulderY} C${x(shoulder + shoulderRoundness + bicepBulge)} ${bicepPeakY} ${x(63 + bicepBulge)} ${bicepPeakY + 8} ${x(62 + bicepBulge * 0.55)} 199 C${x(64)} 216 ${x(70)} 232 ${hand.cx} ${hand.top + hands.overlap} L${x(61)} ${hand.top + hands.overlap + 3} C${x(57)} 226 ${x(53)} 209 ${x(51)} 194 C${x(49)} 171 ${x(shoulder - 12)} 155 ${x(shoulder - 5)} ${BODY_ANCHORS.shoulderY}Z`
  }
  const leg = (side: -1 | 1) => {
    const x = (distance: number) => CX + side * distance
    return `M${x(7)} ${BODY_ANCHORS.hipY} C${x(15)} 228 ${x(29 + thighBulge)} 235 ${x(29 + thighBulge)} 254 C${x(32 + thighBulge)} 271 ${x(28 + thighBulge * 0.45)} ${BODY_ANCHORS.kneeY} ${x(25 + calfBulge)} 310 C${x(29 + calfBulge)} 326 ${x(24 + calfBulge * 0.35)} 338 ${x(20)} ${BODY_ANCHORS.ankleY} L${x(11)} ${BODY_ANCHORS.ankleY} C${x(14)} 326 ${x(14)} 279 ${x(7)} ${BODY_ANCHORS.hipY}Z`
  }
  const lowerClothing = skirt
    ? `M${CX - waist} 221 L${CX + waist} 221 L${CX + 52 + thighBulge} 276 Q${CX} ${286 + thighBulge * 0.15} ${CX - 52 - thighBulge} 276Z`
    : longPants
      ? `M${CX - waist} 221 L${CX + waist} 221 L${CX + 41 + thighBulge} 257 L${CX + 25 + calfBulge} 338 L${CX + 11} 347 L${CX + 7} 245 L${CX - 7} 245 L${CX - 11} 347 L${CX - 25 - calfBulge} 338 L${CX - 41 - thighBulge} 257Z`
      : `M${CX - waist} 221 Q${CX} 232 ${CX + waist} 221 L${CX + 38 + thighBulge} 258 Q${CX} ${266 + thighBulge * 0.12} ${CX - 38 - thighBulge} 258Z`
  const chestLineY = 184 + chestBulge * 0.18
  const abRows = metrics.abCount / 2

  return <svg className={`lianguo-avatar ${className}`} viewBox="0 0 320 405" role="img" aria-label="练过七级成长角色">
    <defs>
      <linearGradient id={skin} x1="120" y1="35" x2="205" y2="368" gradientUnits="userSpaceOnUse"><stop stopColor="#ffe8cf" /><stop offset=".62" stopColor="#ffc089" /><stop offset="1" stopColor="#ef9d62" /></linearGradient>
      <radialGradient id={glow}><stop stopColor="#f8ff7a" stopOpacity=".85" /><stop offset=".55" stopColor="#72f2bc" stopOpacity=".2" /><stop offset="1" stopColor="#fff" stopOpacity="0" /></radialGradient>
      <clipPath id={torsoClip}><path d={torso} /></clipPath>
    </defs>
    <circle cx={CX} cy="205" r={112 + metrics.growth * 18} fill={`url(#${glow})`} />
    <ellipse cx={CX} cy={BODY_ANCHORS.shadowY} rx="88" ry="9" fill="#1f2937" opacity=".13" />
    <g className="lianguo-avatar-bob">
      <AvatarHair style={outfit.hairStyle} color={outfit.hairColor} hatStyle={outfit.hatStyle} hatColor={outfit.hatColor} layer="back" />
      <path d="M143 130v18q17 12 34 0v-18z" fill={`url(#${skin})`} stroke="#202a3a" strokeWidth="5" />
      {!longPants && <path d={leg(-1)} fill={`url(#${skin})`} stroke="#202a3a" strokeWidth="5" strokeLinejoin="round" />}
      {!longPants && <path d={leg(1)} fill={`url(#${skin})`} stroke="#202a3a" strokeWidth="5" strokeLinejoin="round" />}
      {longPants && <path d={lowerClothing} fill={secondary} stroke="#202a3a" strokeWidth="5" strokeLinejoin="round" />}
      <path d={arm(-1)} fill={longSleeve ? primary : `url(#${skin})`} stroke="#202a3a" strokeWidth="5" strokeLinejoin="round" />
      <path d={arm(1)} fill={longSleeve ? primary : `url(#${skin})`} stroke="#202a3a" strokeWidth="5" strokeLinejoin="round" />
      <path d={torso} fill={primary} stroke="#202a3a" strokeWidth="5" strokeLinejoin="round" />
      {!longPants && <path d={lowerClothing} fill={secondary} stroke="#202a3a" strokeWidth="5" strokeLinejoin="round" />}
      <g clipPath={`url(#${torsoClip})`} fill="none" stroke={detail} strokeLinecap="round" opacity={metrics.muscleDetailOpacity}>
        <path d={`M${CX} 168V${203 + chestBulge * 0.15}`} strokeWidth={metrics.chestLineWidth} opacity={metrics.chestLineOpacity} />
        <path d={`M${CX - 29 - chestBulge * 0.45} ${chestLineY} Q${CX - 15} ${chestLineY + 8} ${CX - 3} ${chestLineY + 2}`} strokeWidth={metrics.chestLineWidth} opacity={metrics.chestLineOpacity} />
        <path d={`M${CX + 29 + chestBulge * 0.45} ${chestLineY} Q${CX + 15} ${chestLineY + 8} ${CX + 3} ${chestLineY + 2}`} strokeWidth={metrics.chestLineWidth} opacity={metrics.chestLineOpacity} />
        {Array.from({ length: abRows }, (_, row) => <g key={row} strokeWidth={2.2 + metrics.growth}><path d={`M${CX - 17} ${207 + row * 10}q8 5 14 0`} /><path d={`M${CX + 3} ${207 + row * 10}q6 5 14 0`} /></g>)}
      </g>
      {longSleeve && <g fill="none" stroke={detail} strokeWidth="5" strokeLinecap="round"><path d={`M${hands.left.cx - 8} ${hands.left.top + 2}Q${hands.left.cx} ${hands.left.top + 6} ${hands.left.cx + 8} ${hands.left.top + 2}`} /><path d={`M${hands.right.cx - 8} ${hands.right.top + 2}Q${hands.right.cx} ${hands.right.top + 6} ${hands.right.cx + 8} ${hands.right.top + 2}`} /></g>}
      <ellipse cx={hands.left.cx} cy={hands.left.cy} rx={(hands.left.right - hands.left.left) / 2} ry={(hands.left.bottom - hands.left.top) / 2} fill={`url(#${skin})`} stroke="#202a3a" strokeWidth="5" />
      <ellipse cx={hands.right.cx} cy={hands.right.cy} rx={(hands.right.right - hands.right.left) / 2} ry={(hands.right.bottom - hands.right.top) / 2} fill={`url(#${skin})`} stroke="#202a3a" strokeWidth="5" />
      <path d="M111 346q17-7 35 1l4 17h-50q-3-12 11-18zM174 347q18-8 35 0 14 6 11 17h-50z" fill="#202b3d" stroke="#202a3a" strokeWidth="5" strokeLinejoin="round" />
      <rect x="115" y="35" width="90" height="104" rx="39" fill={`url(#${skin})`} stroke="#202a3a" strokeWidth="5" />
      <rect x="123" y="98" width="26" height="15" rx="8" fill="#ff8f9c" opacity=".42" /><rect x="171" y="98" width="26" height="15" rx="8" fill="#ff8f9c" opacity=".42" />
      <rect x="133" y="82" width="12" height="17" rx="6" fill="#202a3a" /><rect x="175" y="82" width="12" height="17" rx="6" fill="#202a3a" />
      <path d="M147 119q13 12 26 0" fill="none" stroke="#202a3a" strokeWidth="4" strokeLinecap="round" />
      <AvatarHair style={outfit.hairStyle} color={outfit.hairColor} hatStyle={outfit.hatStyle} hatColor={outfit.hatColor} layer="front" />
      {yoga && <path d={`M${CX - waist + 5} 229Q${CX} 238 ${CX + waist - 5} 229`} fill="none" stroke={detail} strokeWidth="3" opacity=".45" />}
    </g>
    <g key={animationKey} className="lianguo-avatar-burst"><rect x="55" y="135" width="210" height="180" rx="48" fill="none" stroke="#20d18b" strokeWidth="7" strokeDasharray="18 12" /></g>
  </svg>
}

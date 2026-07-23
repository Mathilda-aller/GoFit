import { useId } from 'react'
import type { AvatarOutfit, ClothingStyle } from '../types'
import { AvatarHair } from './AvatarHair'

export interface MuscleAvatarProps {
  growth?: number
  outfit: AvatarOutfit
  animationKey?: number
  className?: string
}

const outfitColors: Record<ClothingStyle, [string, string, string]> = {
  'white-tee': ['#fff', '#39445a', '#cbd5e1'],
  'sport-tank': ['#ff376d', '#263247', '#b81748'],
  'long-sleeve': ['#26364d', '#1d293b', '#60728c'],
  'yoga-set': ['#7d83b5', '#626b9f', '#aeb3d4'],
  'skirt-set': ['#fff8fb', '#f29ab6', '#d96f95'],
}

export function MuscleAvatar({ growth = 0, outfit, animationKey = 0, className = '' }: MuscleAvatarProps) {
  const id = useId().replaceAll(':', '')
  const g = Math.min(1, Math.max(0, growth))
  const shoulder = 45 + g * 15
  const arm = 13 + g * 10
  const thigh = 20 + g * 8
  const [primary, secondary, detail] = outfitColors[outfit.clothingStyle]
  const skin = `lianguo-skin-${id}`
  const glow = `lianguo-glow-${id}`
  const longSleeve = outfit.clothingStyle === 'long-sleeve'
  const skirt = outfit.clothingStyle === 'skirt-set'
  const tank = outfit.clothingStyle === 'sport-tank' || outfit.clothingStyle === 'yoga-set'
  const torso = `M${160 - shoulder} 158 Q132 145 ${tank ? 143 : 137} 148 Q160 ${tank ? 178 : 164} ${tank ? 177 : 183} 148 Q188 145 ${160 + shoulder} 158 Q${201 + g * 4} 202 ${194 + g * 4} 239 L${126 - g * 4} 239 Q${119 - g * 4} 202 ${160 - shoulder} 158Z`
  const leftArm = `M${160 - shoulder + 8} 158 C${116 - g * 8} 154 ${104 - g * 12} 183 ${106 - g * 10} 213 L111 281 Q120 293 129 281 L${128 + arm} 204 Q${135 + g * 2} 171 ${160 - shoulder + 8} 158Z`
  const rightArm = `M${160 + shoulder - 8} 158 C${204 + g * 8} 154 ${216 + g * 12} 183 ${214 + g * 10} 213 L209 281 Q200 293 191 281 L${192 - arm} 204 Q${185 - g * 2} 171 ${160 + shoulder - 8} 158Z`
  const leg = (side: -1 | 1) => {
    const inner = 160 + side * 7
    const outer = 160 + side * (16 + thigh)
    return `M${inner} 260 L${outer} 254 Q${outer + side * 5} 306 ${outer - side * 2} 344 L${outer - side * 7} 404 L${inner + side * 4} 404 Q${inner + side * 8} 340 ${inner} 260Z`
  }

  return <svg className={`lianguo-avatar ${className}`} viewBox="0 0 320 440" role="img" aria-label="练过成长角色">
    <defs>
      <linearGradient id={skin} x1="120" y1="40" x2="205" y2="405" gradientUnits="userSpaceOnUse">
        <stop stopColor="#ffe8cf" /><stop offset=".62" stopColor="#ffc089" /><stop offset="1" stopColor="#ef9d62" />
      </linearGradient>
      <radialGradient id={glow}><stop stopColor="#f8ff7a" stopOpacity=".85" /><stop offset=".55" stopColor="#72f2bc" stopOpacity=".2" /><stop offset="1" stopColor="#fff" stopOpacity="0" /></radialGradient>
    </defs>
    <circle cx="160" cy="225" r={120 + g * 18} fill={`url(#${glow})`} />
    <ellipse cx="160" cy="414" rx={68 + g * 20} ry="10" fill="#1f2937" opacity=".13" />
    <g className="lianguo-avatar-bob">
      <AvatarHair style={outfit.hairStyle} color={outfit.hairColor} hatStyle={outfit.hatStyle} hatColor={outfit.hatColor} layer="back" />
      <path d="M143 127v30q17 14 34 0v-30z" fill={`url(#${skin})`} stroke="#202a3a" strokeWidth="5" />
      <path d={leg(-1)} fill={skirt ? `url(#${skin})` : secondary} stroke="#202a3a" strokeWidth="5" strokeLinejoin="round" />
      <path d={leg(1)} fill={skirt ? `url(#${skin})` : secondary} stroke="#202a3a" strokeWidth="5" strokeLinejoin="round" />
      <path d={leftArm} fill={longSleeve ? primary : `url(#${skin})`} stroke="#202a3a" strokeWidth="5" strokeLinejoin="round" />
      <path d={rightArm} fill={longSleeve ? primary : `url(#${skin})`} stroke="#202a3a" strokeWidth="5" strokeLinejoin="round" />
      <path d={torso} fill={primary} stroke="#202a3a" strokeWidth="5" strokeLinejoin="round" />
      <path d={skirt ? `M124 231 L196 231 L218 305 Q160 317 102 305Z` : `M123 235 Q160 247 197 235 L204 272 Q160 282 116 272Z`} fill={secondary} stroke="#202a3a" strokeWidth="5" strokeLinejoin="round" />
      <path d="M112 404q18-8 35 0l4 17h-51q-3-12 12-17zm61 0q18-8 35 0 15 5 12 17h-51z" fill="#202b3d" stroke="#202a3a" strokeWidth="5" strokeLinejoin="round" />
      <rect x="115" y="35" width="90" height="104" rx="39" fill={`url(#${skin})`} stroke="#202a3a" strokeWidth="5" />
      <rect x="123" y="98" width="26" height="15" rx="8" fill="#ff8f9c" opacity=".42" /><rect x="171" y="98" width="26" height="15" rx="8" fill="#ff8f9c" opacity=".42" />
      <rect x="133" y="82" width="12" height="17" rx="6" fill="#202a3a" /><rect x="175" y="82" width="12" height="17" rx="6" fill="#202a3a" />
      <path d="M147 119q13 12 26 0" fill="none" stroke="#202a3a" strokeWidth="4" strokeLinecap="round" />
      <AvatarHair style={outfit.hairStyle} color={outfit.hairColor} hatStyle={outfit.hatStyle} hatColor={outfit.hatColor} layer="front" />
      <path d={`M${130 - g * 5} 201q30 15 ${60 + g * 10} 0`} fill="none" stroke={detail} strokeWidth="3" opacity=".55" />
    </g>
    <g key={animationKey} className="lianguo-avatar-burst"><rect x="65" y="118" width="190" height="190" rx="48" fill="none" stroke="#20d18b" strokeWidth="7" strokeDasharray="18 12" /></g>
  </svg>
}

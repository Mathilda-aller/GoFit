import type { HairStyle, HatStyle } from '../types'

interface AvatarHairProps {
  style: HairStyle
  color: string
  hatStyle: HatStyle
  hatColor: string
  layer: 'back' | 'front'
  growth?: number
}

const outline = '#202a3a'

export function AvatarHair({ style, color, hatStyle, hatColor, layer, growth = 0 }: AvatarHairProps) {
  const common = { fill: color, stroke: outline, strokeWidth: 5, strokeLinejoin: 'round' as const }
  const scale = 1 + Math.min(1, Math.max(0, growth)) * 0.045
  const transform = `translate(160 92) scale(${scale}) translate(-160 -92)`
  const back = style === 'ponytail' ? (
    <path {...common} d="M202 46c27-19 54 2 42 26 22 28 7 60-26 83 15-39-3-68-25-94z" />
  ) : style === 'big-waves' ? (
    <path {...common} d="M160 28c-58 0-67 50-56 91-22 24-12 55 12 66-8 24 10 38 31 19 9-15 5-40 13-54 8 14 4 39 13 54 21 19 39 5 31-19 24-11 34-42 12-66 11-41 2-91-56-91z" />
  ) : style === 'korean-bob' ? (
    <path {...common} d="M160 29c-55 0-63 50-53 103 8 38 35 49 53 36 18 13 45 2 53-36 10-53 2-103-53-103z" />
  ) : null

  let front
  if (style === 'american-spikes') {
    front = <path {...common} d="M115 79l4-39 13-12 12-11 12 12 10-15 12 15 13-13 13 17 9-6 3 52-16-16-21 8-20-10-21 12z" />
  } else if (style === 'textured-part') {
    front = <path {...common} d="M114 84c-4-45 17-66 49-66 34 0 57 23 43 67l-14 13-4-31-18 11-10-17-15 18-14-13-5 31z" />
  } else if (style === 'buzz-cut') {
    front = <path {...common} d="M116 73c3-35 20-51 44-51s41 16 44 51c-27-16-61-16-88 0z" />
  } else {
    front = <path {...common} d="M113 88c-3-51 17-70 49-70 36 0 54 24 45 71l-15 14-4-34c-17 17-42 7-55-2l-5 36z" />
  }

  if (layer === 'back') return <g transform={transform}>{back}</g>

  return <g transform={transform}>
    {hatStyle === 'none' && front}
    {hatStyle === 'cap' && <>
      <path d="M111 66c7-37 25-51 49-51s42 14 49 51c-30-13-68-13-98 0z" fill={hatColor} stroke={outline} strokeWidth="5" />
      <path d="M108 65c31-13 70-12 103 1l29 10c-20 12-52 4-72-1-22-6-41-3-60 1z" fill={hatColor} stroke={outline} strokeWidth="5" strokeLinejoin="round" />
    </>}
  </g>
}

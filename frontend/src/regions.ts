import type { Box, Point, Region, Size } from './types'

export const DEFAULT_RADIUS = 40
export const MIN_RADIUS = 5
export const MAX_RADIUS = 200
export const MIN_REGION_SIZE = 4

export type RegionChanges = Partial<Omit<Region, 'id'>>

export type RegionsAction =
  | { type: 'add'; region: Region }
  | { type: 'update'; id: string; changes: RegionChanges }
  | { type: 'remove'; id: string }
  | { type: 'clear' }

export function regionsReducer(regions: Region[], action: RegionsAction): Region[] {
  switch (action.type) {
    case 'add':
      return [...regions, action.region]
    case 'update':
      return regions.map((region) => (region.id === action.id ? { ...region, ...action.changes } : region))
    case 'remove':
      return regions.filter((region) => region.id !== action.id)
    case 'clear':
      return []
  }
}

export function regionFromDrag(start: Point, end: Point, image: Size, radius: number): Region | null {
  const box = clampToImage(
    {
      x: Math.min(start.x, end.x),
      y: Math.min(start.y, end.y),
      width: Math.abs(end.x - start.x),
      height: Math.abs(end.y - start.y),
    },
    image,
  )
  if (box.width < MIN_REGION_SIZE || box.height < MIN_REGION_SIZE) return null
  return { id: crypto.randomUUID(), ...box, radius }
}

export function clampToImage(box: Box, image: Size): Box {
  const left = Math.max(box.x, 0)
  const top = Math.max(box.y, 0)
  const right = Math.min(box.x + box.width, image.width)
  const bottom = Math.min(box.y + box.height, image.height)
  return { x: left, y: top, width: Math.max(right - left, 0), height: Math.max(bottom - top, 0) }
}

export function moveInside(box: Box, image: Size): Box {
  return {
    ...box,
    x: clamp(box.x, 0, image.width - box.width),
    y: clamp(box.y, 0, image.height - box.height),
  }
}

export function toApiRegions(regions: Region[]) {
  return regions.map(({ x, y, width, height, radius }) => ({
    x: Math.round(x),
    y: Math.round(y),
    width: Math.max(Math.round(width), 1),
    height: Math.max(Math.round(height), 1),
    radius: Math.round(radius),
  }))
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max)
}

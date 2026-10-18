import type { Box, Point, Region, Size } from './types'

export const DEFAULT_RADIUS = 40
export const MIN_RADIUS = 5
export const MAX_RADIUS = 200
export const MIN_REGION_SIZE = 4

const FULL_TURN = 360
const ROTATION_PRECISION = 10

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
  return { id: crypto.randomUUID(), ...box, radius, rotation: 0 }
}

export function clampToImage(box: Box, image: Size): Box {
  const left = Math.max(box.x, 0)
  const top = Math.max(box.y, 0)
  const right = Math.min(box.x + box.width, image.width)
  const bottom = Math.min(box.y + box.height, image.height)
  return { x: left, y: top, width: Math.max(right - left, 0), height: Math.max(bottom - top, 0) }
}

export function regionCorners({ x, y, width, height, rotation }: Region): Point[] {
  const center = { x: x + width / 2, y: y + height / 2 }
  const angle = (rotation * Math.PI) / 180
  const corners = [
    { x, y },
    { x: x + width, y },
    { x: x + width, y: y + height },
    { x, y: y + height },
  ]
  return corners.map((corner) => {
    const dx = corner.x - center.x
    const dy = corner.y - center.y
    return {
      x: center.x + dx * Math.cos(angle) - dy * Math.sin(angle),
      y: center.y + dx * Math.sin(angle) + dy * Math.cos(angle),
    }
  })
}

export function regionBounds(region: Region): Box {
  const corners = regionCorners(region)
  const xs = corners.map((corner) => corner.x)
  const ys = corners.map((corner) => corner.y)
  const left = Math.min(...xs)
  const top = Math.min(...ys)
  return { x: left, y: top, width: Math.max(...xs) - left, height: Math.max(...ys) - top }
}

export function toApiRegions(regions: Region[]) {
  return regions.map(({ x, y, width, height, radius, rotation }) => ({
    x: Math.round(x),
    y: Math.round(y),
    width: Math.max(Math.round(width), 1),
    height: Math.max(Math.round(height), 1),
    radius: Math.round(radius),
    rotation: Math.round((((rotation % FULL_TURN) + FULL_TURN) % FULL_TURN) * ROTATION_PRECISION) / ROTATION_PRECISION,
  }))
}

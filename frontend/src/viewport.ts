import type { Point, Size } from './types'

export const ZOOM_STEP = 1.2
export const MIN_SCALE = 0.02
export const MAX_SCALE = 8

const FIT_MARGIN = 16

export interface View {
  scale: number
  x: number
  y: number
}

export function fitView(image: Size, container: Size): View {
  const width = Math.max(container.width - 2 * FIT_MARGIN, 1)
  const height = Math.max(container.height - 2 * FIT_MARGIN, 1)
  const scale = Math.min(width / image.width, height / image.height, 1)
  return {
    scale,
    x: (container.width - image.width * scale) / 2,
    y: (container.height - image.height * scale) / 2,
  }
}

export function zoomAt(view: View, point: Point, factor: number): View {
  const scale = Math.min(Math.max(view.scale * factor, MIN_SCALE), MAX_SCALE)
  const ratio = scale / view.scale
  return {
    scale,
    x: point.x - (point.x - view.x) * ratio,
    y: point.y - (point.y - view.y) * ratio,
  }
}

import { useState } from 'react'
import type { Point, Size } from './types'
import { fitView, zoomAt, type View } from './viewport'

export function useViewport(image: Size, container: Size) {
  const [custom, setCustom] = useState<View | null>(null)
  const view = custom ?? fitView(image, container)
  const center = { x: container.width / 2, y: container.height / 2 }

  return {
    view,
    zoomAt: (point: Point, factor: number) => setCustom(zoomAt(view, point, factor)),
    zoomCentered: (factor: number) => setCustom(zoomAt(view, center, factor)),
    actualSize: () => setCustom(zoomAt(view, center, 1 / view.scale)),
    panBy: (dx: number, dy: number) => setCustom({ ...view, x: view.x + dx, y: view.y + dy }),
    fit: () => setCustom(null),
  }
}

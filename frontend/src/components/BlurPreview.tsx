import type Konva from 'konva'
import { useMemo } from 'react'
import { Group, Image as KonvaImage } from 'react-konva'
import { renderPreview } from '../previewCanvas'
import { regionBounds, regionCorners } from '../regions'
import type { Region } from '../types'

const MAX_PREVIEW_SCALE = 1

interface BlurPreviewProps {
  image: HTMLImageElement
  region: Region
  scale: number
}

export function BlurPreview({ image, region, scale }: BlurPreviewProps) {
  const previewScale = Math.min(scale, MAX_PREVIEW_SCALE)
  const preview = useMemo(
    () => renderPreview(image, regionBounds(region), region.radius, previewScale),
    [image, region, previewScale],
  )

  function clipToRegion(context: Konva.Context) {
    const [first, ...rest] = regionCorners(region)
    context.moveTo(first.x, first.y)
    rest.forEach((corner) => context.lineTo(corner.x, corner.y))
    context.closePath()
  }

  return (
    <Group clipFunc={clipToRegion} listening={false}>
      <KonvaImage image={preview.canvas} {...preview.box} />
    </Group>
  )
}

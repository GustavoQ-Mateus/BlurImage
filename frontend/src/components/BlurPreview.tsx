import { useMemo } from 'react'
import { Group, Image as KonvaImage } from 'react-konva'
import { renderPreview } from '../previewCanvas'
import type { Region } from '../types'

interface BlurPreviewProps {
  image: HTMLImageElement
  region: Region
  scale: number
}

export function BlurPreview({ image, region, scale }: BlurPreviewProps) {
  const { x, y, width, height, radius } = region
  const preview = useMemo(
    () => renderPreview(image, { x, y, width, height }, radius, scale),
    [image, x, y, width, height, radius, scale],
  )

  return (
    <Group clipX={x} clipY={y} clipWidth={width} clipHeight={height} listening={false}>
      <KonvaImage image={preview.canvas} {...preview.box} />
    </Group>
  )
}

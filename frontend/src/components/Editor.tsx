import type Konva from 'konva'
import { useEffect, useRef, useState } from 'react'
import { Image as KonvaImage, Layer, Rect, Stage, Transformer } from 'react-konva'
import { clampToImage, moveInside, regionFromDrag, type RegionChanges } from '../regions'
import type { Point, Region, Size } from '../types'
import { useElementSize } from '../useElementSize'
import { BlurPreview } from './BlurPreview'
import { RegionShape } from './RegionShape'

interface EditorProps {
  image: HTMLImageElement
  regions: Region[]
  selectedId: string | null
  radius: number
  onAdd: (region: Region) => void
  onUpdate: (id: string, changes: RegionChanges) => void
  onSelect: (id: string | null) => void
}

interface Drag {
  start: Point
  end: Point
}

export function Editor({ image, regions, selectedId, radius, onAdd, onUpdate, onSelect }: EditorProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const layerRef = useRef<Konva.Layer>(null)
  const transformerRef = useRef<Konva.Transformer>(null)
  const [drag, setDrag] = useState<Drag | null>(null)
  const container = useElementSize(containerRef)
  const imageSize: Size = { width: image.naturalWidth, height: image.naturalHeight }
  const scale = Math.min(container.width / imageSize.width, container.height / imageSize.height, 1) || 1

  useEffect(() => {
    const selectedNode = selectedId ? layerRef.current?.findOne(`#${selectedId}`) : undefined
    transformerRef.current?.nodes(selectedNode ? [selectedNode] : [])
  }, [selectedId, regions])

  function pointer(): Point | null {
    return layerRef.current?.getRelativePointerPosition() ?? null
  }

  function startDrag(event: Konva.KonvaEventObject<PointerEvent>) {
    if (event.target.name() === 'region' || event.target.getParent()?.className === 'Transformer') return
    const start = pointer()
    if (!start) return
    onSelect(null)
    setDrag({ start, end: start })
  }

  function continueDrag() {
    const end = pointer()
    if (!drag || !end) return
    setDrag({ ...drag, end })
  }

  function finishDrag() {
    if (!drag) return
    const region = regionFromDrag(drag.start, drag.end, imageSize, radius)
    setDrag(null)
    if (region) onAdd(region)
  }

  const draft = drag && regionFromDrag(drag.start, drag.end, imageSize, radius)

  return (
    <div ref={containerRef} className="editor">
      <Stage
        width={imageSize.width * scale}
        height={imageSize.height * scale}
        onPointerDown={startDrag}
        onPointerMove={continueDrag}
        onPointerUp={finishDrag}
      >
        <Layer ref={layerRef} scaleX={scale} scaleY={scale}>
          <KonvaImage image={image} name="background" />
          {regions.map((region) => (
            <BlurPreview key={`preview-${region.id}`} image={image} region={region} scale={scale} />
          ))}
          {regions.map((region) => (
            <RegionShape
              key={region.id}
              region={region}
              selected={region.id === selectedId}
              onSelect={() => onSelect(region.id)}
              onMove={(box) => onUpdate(region.id, moveInside(box, imageSize))}
              onResize={(box) => onUpdate(region.id, clampToImage(box, imageSize))}
            />
          ))}
          {draft && <Rect {...draft} stroke="#4da3ff" dash={[6, 4]} strokeScaleEnabled={false} listening={false} />}
          <Transformer ref={transformerRef} rotateEnabled={false} keepRatio={false} ignoreStroke />
        </Layer>
      </Stage>
    </div>
  )
}

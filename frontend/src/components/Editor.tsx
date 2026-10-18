import type Konva from 'konva'
import { useEffect, useRef, useState } from 'react'
import { Image as KonvaImage, Layer, Rect, Stage, Transformer } from 'react-konva'
import { regionFromDrag, type RegionChanges } from '../regions'
import type { Point, Region, Size } from '../types'
import { useElementSize } from '../useElementSize'
import { useSpaceKey } from '../useSpaceKey'
import { useViewport } from '../useViewport'
import { ZOOM_STEP } from '../viewport'
import { BlurPreview } from './BlurPreview'
import { RegionShape } from './RegionShape'
import { ZoomControls } from './ZoomControls'

const MIDDLE_BUTTON = 1
const ROTATION_SNAPS = [0, 45, 90, 135, 180, 225, 270, 315]
const ROTATION_SNAP_TOLERANCE = 5

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
  const stageRef = useRef<Konva.Stage>(null)
  const layerRef = useRef<Konva.Layer>(null)
  const transformerRef = useRef<Konva.Transformer>(null)
  const [drag, setDrag] = useState<Drag | null>(null)
  const [panFrom, setPanFrom] = useState<Point | null>(null)
  const spaceHeld = useSpaceKey()
  const container = useElementSize(containerRef)
  const imageSize: Size = { width: image.naturalWidth, height: image.naturalHeight }
  const viewport = useViewport(imageSize, container)
  const { view } = viewport

  useEffect(() => {
    const selectedNode = selectedId ? layerRef.current?.findOne(`#${selectedId}`) : undefined
    transformerRef.current?.nodes(selectedNode ? [selectedNode] : [])
  }, [selectedId, regions])

  function imagePointer(): Point | null {
    return layerRef.current?.getRelativePointerPosition() ?? null
  }

  function screenPointer(): Point | null {
    return stageRef.current?.getPointerPosition() ?? null
  }

  function handlePointerDown(event: Konva.KonvaEventObject<PointerEvent>) {
    if (event.evt.button === MIDDLE_BUTTON || spaceHeld) {
      setPanFrom(screenPointer())
      return
    }
    if (event.target.name() === 'region' || event.target.getParent()?.className === 'Transformer') return
    const start = imagePointer()
    if (!start) return
    onSelect(null)
    setDrag({ start, end: start })
  }

  function handlePointerMove() {
    const screen = screenPointer()
    if (panFrom && screen) {
      viewport.panBy(screen.x - panFrom.x, screen.y - panFrom.y)
      setPanFrom(screen)
      return
    }
    const end = imagePointer()
    if (drag && end) setDrag({ ...drag, end })
  }

  function handlePointerUp() {
    setPanFrom(null)
    if (!drag) return
    const region = regionFromDrag(drag.start, drag.end, imageSize, radius)
    setDrag(null)
    if (region) onAdd(region)
  }

  function handleWheel(event: Konva.KonvaEventObject<WheelEvent>) {
    event.evt.preventDefault()
    const screen = screenPointer()
    if (screen) viewport.zoomAt(screen, event.evt.deltaY < 0 ? ZOOM_STEP : 1 / ZOOM_STEP)
  }

  const draft = drag && regionFromDrag(drag.start, drag.end, imageSize, radius)

  return (
    <div ref={containerRef} className={spaceHeld || panFrom ? 'editor panning' : 'editor'}>
      <Stage
        ref={stageRef}
        width={container.width}
        height={container.height}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onWheel={handleWheel}
      >
        <Layer ref={layerRef} x={view.x} y={view.y} scaleX={view.scale} scaleY={view.scale}>
          <KonvaImage image={image} name="background" />
          {regions.map((region) => (
            <BlurPreview key={`preview-${region.id}`} image={image} region={region} scale={view.scale} />
          ))}
          {regions.map((region) => (
            <RegionShape
              key={region.id}
              region={region}
              selected={region.id === selectedId}
              draggable={!spaceHeld}
              onSelect={() => onSelect(region.id)}
              onChange={(changes) => onUpdate(region.id, changes)}
            />
          ))}
          {draft && <Rect {...draft} stroke="#4da3ff" dash={[6, 4]} strokeScaleEnabled={false} listening={false} />}
          <Transformer
            ref={transformerRef}
            keepRatio={false}
            ignoreStroke
            rotationSnaps={ROTATION_SNAPS}
            rotationSnapTolerance={ROTATION_SNAP_TOLERANCE}
          />
        </Layer>
      </Stage>
      <ZoomControls
        scale={view.scale}
        onZoom={viewport.zoomCentered}
        onActualSize={viewport.actualSize}
        onFit={viewport.fit}
      />
    </div>
  )
}

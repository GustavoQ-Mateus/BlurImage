import type Konva from 'konva'
import { Rect } from 'react-konva'
import type { RegionChanges } from '../regions'
import type { Region } from '../types'

interface RegionShapeProps {
  region: Region
  selected: boolean
  draggable: boolean
  onSelect: () => void
  onChange: (changes: RegionChanges) => void
}

export function RegionShape({ region, selected, draggable, onSelect, onChange }: RegionShapeProps) {
  function geometryAfterTransform(node: Konva.Rect): RegionChanges {
    const width = node.width() * node.scaleX()
    const height = node.height() * node.scaleY()
    node.scale({ x: 1, y: 1 })
    node.size({ width, height })
    node.offset({ x: width / 2, y: height / 2 })
    return { x: node.x() - width / 2, y: node.y() - height / 2, width, height, rotation: node.rotation() }
  }

  return (
    <Rect
      id={region.id}
      name="region"
      x={region.x + region.width / 2}
      y={region.y + region.height / 2}
      offsetX={region.width / 2}
      offsetY={region.height / 2}
      width={region.width}
      height={region.height}
      rotation={region.rotation}
      fill="transparent"
      stroke={selected ? '#4da3ff' : 'rgba(255, 255, 255, 0.8)'}
      strokeWidth={selected ? 2 : 1}
      dash={selected ? undefined : [6, 4]}
      strokeScaleEnabled={false}
      draggable={draggable}
      listening={draggable}
      onPointerDown={onSelect}
      onDragMove={(event) => onChange({ x: event.target.x() - region.width / 2, y: event.target.y() - region.height / 2 })}
      onTransform={(event) => onChange(geometryAfterTransform(event.target as Konva.Rect))}
    />
  )
}

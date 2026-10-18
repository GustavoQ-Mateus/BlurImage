import type Konva from 'konva'
import { Rect } from 'react-konva'
import type { Box, Region } from '../types'

interface RegionShapeProps {
  region: Region
  selected: boolean
  onSelect: () => void
  onMove: (box: Box) => void
  onResize: (box: Box) => void
}

export function RegionShape({ region, selected, onSelect, onMove, onResize }: RegionShapeProps) {
  function boxAfterResize(node: Konva.Rect): Box {
    const box = {
      x: node.x(),
      y: node.y(),
      width: node.width() * node.scaleX(),
      height: node.height() * node.scaleY(),
    }
    node.scale({ x: 1, y: 1 })
    return box
  }

  return (
    <Rect
      id={region.id}
      name="region"
      x={region.x}
      y={region.y}
      width={region.width}
      height={region.height}
      fill="transparent"
      stroke={selected ? '#4da3ff' : 'rgba(255, 255, 255, 0.8)'}
      strokeWidth={selected ? 2 : 1}
      dash={selected ? undefined : [6, 4]}
      strokeScaleEnabled={false}
      draggable
      onPointerDown={onSelect}
      onDragMove={(event) => onMove({ ...region, x: event.target.x(), y: event.target.y() })}
      onTransform={(event) => onResize(boxAfterResize(event.target as Konva.Rect))}
    />
  )
}

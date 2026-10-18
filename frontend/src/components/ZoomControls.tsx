import { ZOOM_STEP } from '../viewport'

interface ZoomControlsProps {
  scale: number
  onZoom: (factor: number) => void
  onActualSize: () => void
  onFit: () => void
}

export function ZoomControls({ scale, onZoom, onActualSize, onFit }: ZoomControlsProps) {
  return (
    <div className="zoom-controls">
      <button aria-label="Diminuir zoom" onClick={() => onZoom(1 / ZOOM_STEP)}>
        −
      </button>
      <button className="zoom-level" title="Tamanho real" onClick={onActualSize}>
        {Math.round(scale * 100)}%
      </button>
      <button aria-label="Aumentar zoom" onClick={() => onZoom(ZOOM_STEP)}>
        +
      </button>
      <button onClick={onFit}>Ajustar</button>
    </div>
  )
}

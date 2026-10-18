import { MAX_RADIUS, MIN_RADIUS } from '../regions'
import type { Region } from '../types'

interface RegionPanelProps {
  regions: Region[]
  selected: Region | null
  radius: number
  onSelect: (id: string) => void
  onRadiusChange: (radius: number) => void
  onRemove: (id: string) => void
  onClear: () => void
}

export function RegionPanel({
  regions,
  selected,
  radius,
  onSelect,
  onRadiusChange,
  onRemove,
  onClear,
}: RegionPanelProps) {
  return (
    <aside className="panel">
      <section>
        <h2>Intensidade</h2>
        <label className="slider">
          <input
            type="range"
            min={MIN_RADIUS}
            max={MAX_RADIUS}
            value={selected?.radius ?? radius}
            onChange={(event) => onRadiusChange(Number(event.target.value))}
          />
          <span>{selected?.radius ?? radius}px</span>
        </label>
        <p className="hint">{selected ? 'Região selecionada' : 'Próximas regiões'}</p>
      </section>

      <section className="regions">
        <h2>Regiões</h2>
        {regions.length === 0 && <p className="hint">Arraste sobre a foto para criar uma região.</p>}
        <ul>
          {regions.map((region, index) => (
            <li key={region.id}>
              <button
                className={region.id === selected?.id ? 'region active' : 'region'}
                onClick={() => onSelect(region.id)}
              >
                #{index + 1}
                <span>
                  {Math.round(region.width)}×{Math.round(region.height)} · {region.radius}px
                </span>
              </button>
              <button className="remove" aria-label={`Remover região ${index + 1}`} onClick={() => onRemove(region.id)}>
                ×
              </button>
            </li>
          ))}
        </ul>
        {regions.length > 0 && (
          <button className="secondary" onClick={onClear}>
            Remover todas
          </button>
        )}
      </section>
    </aside>
  )
}

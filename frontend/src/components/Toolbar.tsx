import type { ChangeEvent } from 'react'

const ACCEPTED_TYPES = 'image/jpeg,image/png,image/webp,image/heic,image/heif,.heic,.heif'

interface ToolbarProps {
  file: File | null
  image: HTMLImageElement | null
  status: string
  canExport: boolean
  onOpen: (file: File) => void
  onExport: () => void
}

export function Toolbar({ file, image, status, canExport, onOpen, onExport }: ToolbarProps) {
  function handleChange(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0]
    if (selected) onOpen(selected)
    event.target.value = ''
  }

  return (
    <header className="toolbar">
      <label className="button">
        Abrir
        <input type="file" accept={ACCEPTED_TYPES} onChange={handleChange} hidden />
      </label>
      {file && (
        <span className="file-info">
          {file.name}
          {image && ` · ${image.naturalWidth}×${image.naturalHeight}`}
        </span>
      )}
      <span className="status">{status}</span>
      <button className="primary" disabled={!canExport} onClick={onExport}>
        Exportar
      </button>
    </header>
  )
}

import { useEffect, useState } from 'react'
import { exportBlurred } from './blurApi'
import { Editor } from './components/Editor'
import { RegionPanel } from './components/RegionPanel'
import { Toolbar } from './components/Toolbar'
import { blurredFilename, downloadBlob } from './download'
import { DEFAULT_RADIUS } from './regions'
import { useImageFile } from './useImageFile'
import { useRegions } from './useRegions'

const WEBP_NOTE = 'WebP é exportado sem perda (lossless); o arquivo pode ficar maior.'

export default function App() {
  const { file, image, open } = useImageFile()
  const { regions, selected, select, add, update, remove, clear } = useRegions()
  const [radius, setRadius] = useState(DEFAULT_RADIUS)
  const [exporting, setExporting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    function handleKey(event: KeyboardEvent) {
      if (event.target instanceof HTMLInputElement) return
      if (event.key === 'Escape') select(null)
      if ((event.key === 'Delete' || event.key === 'Backspace') && selected) remove(selected.id)
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  })

  function handleOpen(next: File) {
    clear()
    setError('')
    open(next)
  }

  function handleRadiusChange(value: number) {
    if (selected) update(selected.id, { radius: value })
    else setRadius(value)
  }

  async function handleExport() {
    if (!file) return
    setExporting(true)
    setError('')
    try {
      downloadBlob(await exportBlurred(file, regions), blurredFilename(file.name))
    } catch (exportError) {
      setError(exportError instanceof Error ? exportError.message : 'Falha ao exportar.')
    } finally {
      setExporting(false)
    }
  }

  return (
    <div className="app">
      <Toolbar
        file={file}
        image={image}
        status={exporting ? 'Exportando…' : error || (file?.type === 'image/webp' ? WEBP_NOTE : '')}
        canExport={Boolean(image) && regions.length > 0 && !exporting}
        onOpen={handleOpen}
        onExport={handleExport}
      />
      <main className="workspace">
        {image ? (
          <Editor
            image={image}
            regions={regions}
            selectedId={selected?.id ?? null}
            radius={radius}
            onAdd={add}
            onUpdate={update}
            onSelect={select}
          />
        ) : (
          <div className="empty">Abra uma foto JPEG, PNG ou WebP para começar.</div>
        )}
        <RegionPanel
          regions={regions}
          selected={selected}
          radius={radius}
          onSelect={select}
          onRadiusChange={handleRadiusChange}
          onRemove={remove}
          onClear={clear}
        />
      </main>
      <footer className="shortcuts">Arraste para criar · Del remove · Esc tira a seleção</footer>
    </div>
  )
}

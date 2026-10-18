import { useEffect, useState } from 'react'
import { fetchPreview } from './blurApi'
import { isHeic } from './heic'

const OPEN_ERROR = 'Não foi possível abrir a imagem.'

export function useImageFile() {
  const [file, setFile] = useState<File | null>(null)
  const [image, setImage] = useState<HTMLImageElement | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!file) return
    let cancelled = false
    let url = ''
    const displayable = isHeic(file) ? fetchPreview(file) : Promise.resolve<Blob>(file)
    displayable
      .then((blob) => {
        if (cancelled) return
        url = URL.createObjectURL(blob)
        const element = new Image()
        element.onload = () => !cancelled && setImage(element)
        element.onerror = () => !cancelled && setError(OPEN_ERROR)
        element.src = url
      })
      .catch((reason: unknown) => !cancelled && setError(reason instanceof Error ? reason.message : OPEN_ERROR))
    return () => {
      cancelled = true
      if (url) URL.revokeObjectURL(url)
    }
  }, [file])

  function open(next: File) {
    setImage(null)
    setError('')
    setFile(next)
  }

  return { file, image, error, loading: Boolean(file) && !image && !error, open }
}

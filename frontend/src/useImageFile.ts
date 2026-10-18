import { useEffect, useState } from 'react'

export function useImageFile() {
  const [file, setFile] = useState<File | null>(null)
  const [image, setImage] = useState<HTMLImageElement | null>(null)

  useEffect(() => {
    if (!file) return
    const url = URL.createObjectURL(file)
    const element = new Image()
    element.onload = () => setImage(element)
    element.src = url
    return () => URL.revokeObjectURL(url)
  }, [file])

  function open(next: File) {
    setImage(null)
    setFile(next)
  }

  return { file, image, open }
}

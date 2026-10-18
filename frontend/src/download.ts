export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  setTimeout(() => URL.revokeObjectURL(url))
}

export function blurredFilename(original: string) {
  const dot = original.lastIndexOf('.')
  if (dot <= 0) return `${original}-blur`
  return `${original.slice(0, dot)}-blur${original.slice(dot)}`
}

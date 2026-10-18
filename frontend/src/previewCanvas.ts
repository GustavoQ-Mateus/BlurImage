import { clampToImage } from './regions'
import type { Box, Size } from './types'

const CONTEXT_FACTOR = 3

export interface Preview {
  canvas: HTMLCanvasElement
  box: Box
}

// O filtro blur() do canvas usa o raio como desvio padrão, igual ao GaussianBlur do Pillow.
export function renderPreview(image: HTMLImageElement, area: Box, radius: number, scale: number): Preview {
  const imageSize: Size = { width: image.naturalWidth, height: image.naturalHeight }
  const margin = radius * CONTEXT_FACTOR
  const box = clampToImage(
    {
      x: area.x - margin,
      y: area.y - margin,
      width: area.width + 2 * margin,
      height: area.height + 2 * margin,
    },
    imageSize,
  )
  const canvas = document.createElement('canvas')
  canvas.width = Math.max(Math.ceil(box.width * scale), 1)
  canvas.height = Math.max(Math.ceil(box.height * scale), 1)
  const context = canvas.getContext('2d')
  if (!context) return { canvas, box }
  context.filter = `blur(${radius * scale}px)`
  context.drawImage(image, box.x, box.y, box.width, box.height, 0, 0, canvas.width, canvas.height)
  return { canvas, box }
}

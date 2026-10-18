import { describe, expect, it } from 'vitest'
import { MAX_SCALE, fitView, zoomAt } from './viewport'

describe('fitView', () => {
  it('imagem maior que a tela é reduzida e centralizada', () => {
    const view = fitView({ width: 2000, height: 1000 }, { width: 1032, height: 800 })

    expect(view.scale).toBe(0.5)
    expect(view.x).toBe(16)
    expect(view.y).toBe(150)
  })

  it('imagem menor que a tela não é ampliada', () => {
    expect(fitView({ width: 100, height: 100 }, { width: 1000, height: 1000 }).scale).toBe(1)
  })
})

describe('zoomAt', () => {
  it('o ponto da imagem sob o cursor continua sob o cursor', () => {
    const view = { scale: 0.5, x: 10, y: 20 }
    const cursor = { x: 210, y: 120 }
    const imagePoint = { x: (cursor.x - view.x) / view.scale, y: (cursor.y - view.y) / view.scale }

    const zoomed = zoomAt(view, cursor, 2)

    expect(imagePoint.x * zoomed.scale + zoomed.x).toBeCloseTo(cursor.x)
    expect(imagePoint.y * zoomed.scale + zoomed.y).toBeCloseTo(cursor.y)
  })

  it('zoom não passa do limite máximo', () => {
    expect(zoomAt({ scale: 6, x: 0, y: 0 }, { x: 0, y: 0 }, 10).scale).toBe(MAX_SCALE)
  })
})

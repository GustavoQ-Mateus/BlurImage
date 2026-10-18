import { describe, expect, it } from 'vitest'
import { clampToImage, regionBounds, regionFromDrag, regionsReducer, toApiRegions } from './regions'
import type { Region } from './types'

const IMAGE = { width: 100, height: 80 }

function region(overrides: Partial<Region> = {}): Region {
  return { id: 'a', x: 10, y: 10, width: 20, height: 20, radius: 10, rotation: 0, ...overrides }
}

describe('regionFromDrag', () => {
  it('drag para cima e para a esquerda gera caixa com tamanho positivo', () => {
    const result = regionFromDrag({ x: 50, y: 40 }, { x: 20, y: 10 }, IMAGE, 15)

    expect(result).toMatchObject({ x: 20, y: 10, width: 30, height: 30, radius: 15, rotation: 0 })
  })

  it('drag que passa da imagem é cortado na borda', () => {
    const result = regionFromDrag({ x: 90, y: 70 }, { x: 130, y: 120 }, IMAGE, 15)

    expect(result).toMatchObject({ x: 90, y: 70, width: 10, height: 10 })
  })

  it('drag menor que o tamanho mínimo não cria região', () => {
    expect(regionFromDrag({ x: 10, y: 10 }, { x: 12, y: 30 }, IMAGE, 15)).toBeNull()
  })
})

describe('clampToImage', () => {
  it('caixa que passa da borda é cortada sem mover a origem', () => {
    expect(clampToImage({ x: 80, y: 5, width: 50, height: 10 }, IMAGE)).toEqual({ x: 80, y: 5, width: 20, height: 10 })
  })
})

describe('regionBounds', () => {
  it('giro de 90 graus troca largura e altura em torno do centro', () => {
    const bounds = regionBounds(region({ x: 0, y: 40, width: 100, height: 20, rotation: 90 }))

    expect(bounds.x).toBeCloseTo(40)
    expect(bounds.y).toBeCloseTo(0)
    expect(bounds.width).toBeCloseTo(20)
    expect(bounds.height).toBeCloseTo(100)
  })
})

describe('regionsReducer', () => {
  it('update altera só a região indicada', () => {
    const regions = [region(), region({ id: 'b' })]

    const result = regionsReducer(regions, { type: 'update', id: 'b', changes: { radius: 50 } })

    expect(result.map((item) => item.radius)).toEqual([10, 50])
  })

  it('remove tira só a região indicada', () => {
    const result = regionsReducer([region(), region({ id: 'b' })], { type: 'remove', id: 'a' })

    expect(result.map((item) => item.id)).toEqual(['b'])
  })
})

describe('toApiRegions', () => {
  it('arredonda as coordenadas para pixels inteiros e descarta o id', () => {
    const result = toApiRegions([region({ x: 10.4, y: 9.6, width: 0.3, height: 20.5, radius: 12.2, rotation: 30.04 })])

    expect(result).toEqual([{ x: 10, y: 10, width: 1, height: 21, radius: 12, rotation: 30 }])
  })

  it('normaliza giro negativo para o intervalo de 0 a 360', () => {
    expect(toApiRegions([region({ rotation: -45 })])[0].rotation).toBe(315)
  })
})

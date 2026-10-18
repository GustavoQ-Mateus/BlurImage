import { describe, expect, it } from 'vitest'
import { clampToImage, moveInside, regionFromDrag, regionsReducer, toApiRegions } from './regions'
import type { Region } from './types'

const IMAGE = { width: 100, height: 80 }

function region(overrides: Partial<Region> = {}): Region {
  return { id: 'a', x: 10, y: 10, width: 20, height: 20, radius: 10, ...overrides }
}

describe('regionFromDrag', () => {
  it('drag para cima e para a esquerda gera caixa com tamanho positivo', () => {
    const result = regionFromDrag({ x: 50, y: 40 }, { x: 20, y: 10 }, IMAGE, 15)

    expect(result).toMatchObject({ x: 20, y: 10, width: 30, height: 30, radius: 15 })
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
  it('redimensionar além da borda corta a caixa sem mover a origem', () => {
    expect(clampToImage({ x: 80, y: 5, width: 50, height: 10 }, IMAGE)).toEqual({ x: 80, y: 5, width: 20, height: 10 })
  })
})

describe('moveInside', () => {
  it('mover além da borda mantém o tamanho e encosta na borda', () => {
    expect(moveInside({ x: 90, y: -5, width: 20, height: 10 }, IMAGE)).toEqual({ x: 80, y: 0, width: 20, height: 10 })
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
    const result = toApiRegions([region({ x: 10.4, y: 9.6, width: 0.3, height: 20.5, radius: 12.2 })])

    expect(result).toEqual([{ x: 10, y: 10, width: 1, height: 21, radius: 12 }])
  })
})

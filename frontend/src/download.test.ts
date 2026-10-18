import { describe, expect, it } from 'vitest'
import { blurredFilename } from './download'

describe('blurredFilename', () => {
  it('acrescenta o sufixo antes da extensão original', () => {
    expect(blurredFilename('ferias.final.JPG')).toBe('ferias.final-blur.JPG')
  })

  it('arquivo sem extensão recebe o sufixo no fim', () => {
    expect(blurredFilename('foto')).toBe('foto-blur')
  })
})

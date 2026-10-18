import { describe, expect, it } from 'vitest'
import { isHeic } from './heic'

describe('isHeic', () => {
  it('reconhece HEIC pela extensão quando o navegador não informa o tipo', () => {
    expect(isHeic(new File([], 'IMG_0001.HEIC'))).toBe(true)
  })

  it('reconhece HEIF pelo tipo informado', () => {
    expect(isHeic(new File([], 'foto', { type: 'image/heif' }))).toBe(true)
  })

  it('não confunde JPEG com HEIC', () => {
    expect(isHeic(new File([], 'foto.jpg', { type: 'image/jpeg' }))).toBe(false)
  })
})

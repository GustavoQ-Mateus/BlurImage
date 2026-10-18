const HEIC_TYPES = ['image/heic', 'image/heif']
const HEIC_EXTENSION = /\.hei[cf]$/i

export function isHeic(file: File) {
  return HEIC_TYPES.includes(file.type) || HEIC_EXTENSION.test(file.name)
}

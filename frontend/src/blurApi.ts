import { toApiRegions } from './regions'
import type { Region } from './types'

export async function exportBlurred(file: File, regions: Region[]): Promise<Blob> {
  const body = new FormData()
  body.append('file', file)
  body.append('regions', JSON.stringify(toApiRegions(regions)))
  return post('/api/blur', body)
}

export async function fetchPreview(file: File): Promise<Blob> {
  const body = new FormData()
  body.append('file', file)
  return post('/api/preview', body)
}

async function post(url: string, body: FormData): Promise<Blob> {
  const response = await fetch(url, { method: 'POST', body })
  if (!response.ok) throw new Error(await errorMessage(response))
  return response.blob()
}

async function errorMessage(response: Response): Promise<string> {
  try {
    const { detail } = await response.json()
    return typeof detail === 'string' ? detail : `Erro ${response.status}`
  } catch {
    return `Erro ${response.status}`
  }
}

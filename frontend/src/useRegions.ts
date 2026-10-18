import { useReducer, useState } from 'react'
import { regionsReducer, type RegionChanges } from './regions'
import type { Region } from './types'

export function useRegions() {
  const [regions, dispatch] = useReducer(regionsReducer, [])
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const selected = regions.find((region) => region.id === selectedId) ?? null

  function add(region: Region) {
    dispatch({ type: 'add', region })
    setSelectedId(region.id)
  }

  function update(id: string, changes: RegionChanges) {
    dispatch({ type: 'update', id, changes })
  }

  function remove(id: string) {
    dispatch({ type: 'remove', id })
    if (id === selectedId) setSelectedId(null)
  }

  function clear() {
    dispatch({ type: 'clear' })
    setSelectedId(null)
  }

  return { regions, selected, select: setSelectedId, add, update, remove, clear }
}

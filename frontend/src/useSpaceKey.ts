import { useEffect, useState } from 'react'

export function useSpaceKey() {
  const [held, setHeld] = useState(false)

  useEffect(() => {
    function handle(event: KeyboardEvent) {
      if (event.code !== 'Space' || event.target instanceof HTMLInputElement) return
      event.preventDefault()
      setHeld(event.type === 'keydown')
    }
    window.addEventListener('keydown', handle)
    window.addEventListener('keyup', handle)
    return () => {
      window.removeEventListener('keydown', handle)
      window.removeEventListener('keyup', handle)
    }
  }, [])

  return held
}

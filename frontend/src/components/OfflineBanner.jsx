import React, { useState, useEffect } from 'react'

export default function OfflineBanner() {
  const [isOnline, setIsOnline]       = useState(
    typeof navigator !== 'undefined' ? navigator.onLine : true
  )
  const [justCameBack, setJustCameBack] = useState(false)

  useEffect(() => {
    function handleOnline() {
      setIsOnline(true)
      setJustCameBack(true)
      setTimeout(() => setJustCameBack(false), 3000)
    }
    function handleOffline() { setIsOnline(false) }
    window.addEventListener('online',  handleOnline)
    window.addEventListener('offline', handleOffline)
    return () => {
      window.removeEventListener('online',  handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  if (isOnline && !justCameBack) return null

  return (
    <div style={{
      position: 'fixed',
      top: 'var(--topnav-h)',
      left: 0, right: 0,
      zIndex: 10000,
      padding: '7px 16px',
      textAlign: 'center',
      fontSize: 12, fontWeight: 500,
      background: isOnline ? '#1D9E75' : '#BA7517',
      color: '#fff',
      transition: 'background 0.3s',
    }}>
      {isOnline
        ? 'Back online -- refreshing event data...'
        : 'You are offline -- showing last cached data. Real-time updates paused.'}
    </div>
  )
}

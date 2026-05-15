import React from 'react'
import useAppStore from '../store/useAppStore.js'
import { useCacheStatus } from '../api/queries.js'

export default function TopNav() {
  const { lightMode, toggleLight, toggleSidebar } = useAppStore()
  const { data: cacheInfo } = useCacheStatus()

  const evCount = cacheInfo && cacheInfo.event_count
  const mode    = cacheInfo && cacheInfo.mode

  return (
    <header style={{
      height: 'var(--topnav-h)',
      background: 'var(--bg-surface)',
      borderBottom: '1px solid var(--border-primary)',
      display: 'flex', alignItems: 'center',
      padding: '0 16px', gap: 10, flexShrink: 0, zIndex: 100,
    }}>
      {/* Sidebar toggle */}
      <button onClick={toggleSidebar} title="Toggle sidebar" style={btnStyle}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
          <rect x="1" y="3"    width="14" height="1.5" rx="0.75"/>
          <rect x="1" y="7.25" width="14" height="1.5" rx="0.75"/>
          <rect x="1" y="11.5" width="14" height="1.5" rx="0.75"/>
        </svg>
      </button>

      {/* Satellite icon */}
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
           stroke="#1D9E75" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M13 7L17 3M17 3L21 7M17 3V13"/>
        <circle cx="9" cy="15" r="4"/>
        <path d="M3 21L7 17"/>
        <path d="M9 11L13 7"/>
      </svg>

      {/* Title: full name + NET-EA short code */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
        <span style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-primary)',
                       letterSpacing: '-0.01em' }}>
          Natural Event Tracker for East Africa
        </span>
        <span style={{
          fontSize: 11, fontWeight: 700, padding: '1px 7px',
          borderRadius: 4, background: '#1D9E7522',
          border: '1px solid #1D9E7544', color: '#0F6E56',
          letterSpacing: '0.04em',
        }}>
          NET-EA
        </span>
      </div>

      <div style={{ flex: 1 }} />

      {/* Live data status */}
      {evCount != null && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 5,
                      fontSize: 11, color: 'var(--text-muted)' }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%',
                         background: mode === 'backend' ? '#1D9E75' : '#378ADD',
                         display: 'inline-block' }} />
          {evCount} events
          {cacheInfo.ttl_remaining_s != null
            ? ' -- refresh in ' + Math.ceil(cacheInfo.ttl_remaining_s / 60) + 'm'
            : ' -- live'}
        </div>
      )}

      {/* Theme toggle */}
      <button onClick={toggleLight} title="Toggle theme" style={btnStyle}>
        {lightMode ? (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="4"/>
            <line x1="12" y1="2"  x2="12" y2="4"/>
            <line x1="12" y1="20" x2="12" y2="22"/>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
            <line x1="2"  y1="12" x2="4"  y2="12"/>
            <line x1="20" y1="12" x2="22" y2="12"/>
          </svg>
        ) : (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" strokeWidth="2">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
          </svg>
        )}
      </button>
    </header>
  )
}

const btnStyle = {
  background: 'transparent', border: 'none',
  color: 'var(--text-secondary)', cursor: 'pointer',
  padding: '6px', borderRadius: 6,
  display: 'flex', alignItems: 'center', fontSize: 13,
}

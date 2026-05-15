import React from 'react'
import { isNetworkBlockedError } from '../api/queries.js'
import { useQueryClient } from '@tanstack/react-query'

export default function NetworkError({ error, compact }) {
  const qc      = useQueryClient()
  const blocked = isNetworkBlockedError(error)

  function handleRetry() {
    qc.invalidateQueries({ queryKey: ['events'] })
  }

  if (compact) {
    return (
      <div style={{
        padding: '10px 14px', fontSize: 12,
        color: 'var(--text-secondary)',
        display: 'flex', alignItems: 'center', gap: 10,
        flexWrap: 'wrap',
      }}>
        <span style={{ color: '#BA7517', fontWeight: 500 }}>
          {blocked ? 'Network blocked' : 'Fetch failed'}
        </span>
        <span style={{ color: 'var(--text-muted)' }}>
          {blocked
            ? 'Try a mobile hotspot -- office network blocks NASA servers'
            : (error && error.message) || 'Unknown error'}
        </span>
        <button onClick={handleRetry} style={{
          fontSize: 11, padding: '3px 10px', borderRadius: 5,
          border: '1px solid var(--border-primary)',
          background: 'transparent', color: 'var(--text-secondary)',
          cursor: 'pointer',
        }}>
          Retry
        </button>
      </div>
    )
  }

  return (
    <div style={{
      position: 'absolute', inset: 0, zIndex: 500,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'rgba(246,248,250,0.92)',
      padding: 24,
    }}>
      <div style={{
        maxWidth: 400, width: '100%',
        background: 'var(--bg-surface)',
        border: '1px solid #BA751744',
        borderLeft: '4px solid #BA7517',
        borderRadius: 'var(--radius-lg)',
        padding: '20px 22px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
            stroke="#BA7517" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
          <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
            {blocked ? 'Network is blocking NASA EONET' : 'Could not load events'}
          </span>
        </div>

        {blocked ? (
          <>
            <p style={{ fontSize: 12, color: 'var(--text-secondary)',
                        lineHeight: 1.65, marginBottom: 14 }}>
              Your network is blocking outbound HTTPS to
              <strong> eonet.gsfc.nasa.gov</strong> (port 443).
              This is common on institutional/corporate networks.
            </p>
            <div style={{ fontSize: 12, marginBottom: 14 }}>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)',
                            marginBottom: 6 }}>
                Quick fix options:
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                {[
                  ['1', 'Use a mobile hotspot', 'Fastest -- connect phone and switch laptop WiFi'],
                  ['2', 'Ask IT to whitelist', 'eonet.gsfc.nasa.gov port 443 (129.164.142.189)'],
                  ['3', 'Start the backend', 'uvicorn backend.main:app --port 8000 (may use system proxy)'],
                ].map(([n, title, sub]) => (
                  <div key={n} style={{
                    display: 'flex', gap: 10, padding: '6px 10px',
                    background: 'var(--bg-elevated)',
                    borderRadius: 6, alignItems: 'flex-start',
                  }}>
                    <span style={{ fontSize: 11, fontWeight: 700, color: '#BA7517',
                                   flexShrink: 0, minWidth: 14 }}>
                      {n}.
                    </span>
                    <div>
                      <div style={{ fontSize: 12, fontWeight: 500,
                                    color: 'var(--text-primary)' }}>{title}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{sub}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        ) : (
          <p style={{ fontSize: 12, color: 'var(--text-secondary)',
                      lineHeight: 1.65, marginBottom: 14 }}>
            {(error && error.message) || 'An unknown error occurred while fetching events.'}
          </p>
        )}

        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={handleRetry} style={{
            flex: 1, padding: '7px', borderRadius: 6, fontSize: 12,
            border: 'none', background: '#1D9E75', color: '#fff',
            cursor: 'pointer', fontWeight: 500,
          }}>
            Retry now
          </button>
          <button
            onClick={() => window.open('https://eonet.gsfc.nasa.gov/api/v3/categories', '_blank')}
            style={{
              flex: 1, padding: '7px', borderRadius: 6, fontSize: 12,
              border: '1px solid var(--border-primary)',
              background: 'transparent', color: 'var(--text-secondary)',
              cursor: 'pointer',
            }}>
            Test connection
          </button>
        </div>

        <p style={{ fontSize: 10, color: 'var(--text-faint)', marginTop: 10, lineHeight: 1.5 }}>
          Timed out after 9s. Once network access is available the
          dashboard will load real EONET data automatically.
        </p>
      </div>
    </div>
  )
}

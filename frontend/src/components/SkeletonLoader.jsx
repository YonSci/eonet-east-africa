import React from 'react'

export function SkeletonRect({ w, h, style }) {
  return (
    <div
      className="skeleton"
      style={{ width: w || '100%', height: h || 16, borderRadius: 4, ...style }}
    />
  )
}

export function SkeletonCard() {
  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border-primary)',
      borderRadius: 'var(--radius-md)',
      padding: '10px 14px',
    }}>
      <SkeletonRect h={28} w="40%" style={{ marginBottom: 6 }} />
      <SkeletonRect h={13} w="60%" />
    </div>
  )
}

export function SkeletonRow() {
  return (
    <div style={{ display: 'flex', gap: 8, padding: '7px 10px',
                  borderBottom: '1px solid var(--border-muted)' }}>
      <SkeletonRect w={82} h={12} />
      <SkeletonRect w={90} h={12} />
      <SkeletonRect w={52} h={12} />
      <SkeletonRect h={12} style={{ flex: 1 }} />
    </div>
  )
}

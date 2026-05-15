import React from 'react'
import { CATEGORIES } from '../store/useAppStore.js'
import { useEvents } from '../api/queries.js'
import useAppStore from '../store/useAppStore.js'

export default function CategoryBar() {
  const { activeCategories, activeStatus, setAllCategories, toggleCategory } = useAppStore()
  const { data: rawEvents = [], isLoading } = useEvents()

  // Count events per category (respecting status filter)
  const counts = {}
  rawEvents.forEach((ev) => {
    if (activeStatus === 'open'   && ev.status !== 'open')   return
    if (activeStatus === 'closed' && ev.status !== 'closed') return
    counts[ev.category] = (counts[ev.category] || 0) + 1
  })

  const total   = Object.values(counts).reduce((a, b) => a + b, 0)
  const entries = Object.entries(CATEGORIES)
    .map(([id, meta]) => ({ id, ...meta, count: counts[id] || 0 }))
    .filter((c) => c.count > 0)
    .sort((a, b) => b.count - a.count)

  if (isLoading || !entries.length) return null

  return (
    <div style={{
      flexShrink: 0,
      background: 'var(--bg-surface)',
      borderTop: '1px solid var(--border-primary)',
      padding: '8px 14px',
      display: 'flex',
      alignItems: 'center',
      gap: 0,
      overflow: 'hidden',
    }}>
      {/* Proportional colour bar */}
      <div style={{
        display: 'flex',
        height: 6,
        borderRadius: 3,
        overflow: 'hidden',
        width: 120,
        flexShrink: 0,
        marginRight: 12,
      }}>
        {entries.map((c) => (
          <div
            key={c.id}
            title={c.label + ': ' + c.count}
            style={{
              width: ((c.count / total) * 100) + '%',
              background: c.color,
              transition: 'width 0.4s',
            }}
          />
        ))}
      </div>

      {/* Category pills */}
      <div style={{
        display: 'flex',
        gap: 6,
        flexWrap: 'nowrap',
        overflowX: 'auto',
        flex: 1,
        scrollbarWidth: 'none',
        msOverflowStyle: 'none',
      }}>
        {entries.map((c) => {
          const active = activeCategories.includes(c.id)
          return (
            <button
              key={c.id}
              onClick={() => toggleCategory(c.id)}
              title={active ? 'Click to hide ' + c.label : 'Click to show ' + c.label}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 5,
                padding: '3px 8px',
                borderRadius: 100,
                border: '1px solid',
                borderColor: active ? c.color + '66' : 'var(--border-muted)',
                background:  active ? c.color + '15' : 'transparent',
                cursor: 'pointer',
                flexShrink: 0,
                transition: 'all 0.12s',
              }}
            >
              <span style={{
                width: 6, height: 6, borderRadius: '50%',
                background: active ? c.color : 'var(--text-faint)',
                flexShrink: 0,
              }} />
              <span style={{
                fontSize: 11, fontWeight: active ? 600 : 400,
                color: active ? 'var(--text-primary)' : 'var(--text-muted)',
                whiteSpace: 'nowrap',
              }}>
                {c.label}
              </span>
              <span style={{
                fontSize: 10,
                color: active ? c.color : 'var(--text-faint)',
                fontWeight: 600,
              }}>
                {c.count}
              </span>
            </button>
          )
        })}
      </div>

      {/* Total count */}
      <div style={{
        fontSize: 11,
        color: 'var(--text-muted)',
        flexShrink: 0,
        marginLeft: 10,
        paddingLeft: 10,
        borderLeft: '1px solid var(--border-primary)',
      }}>
        {total} shown
      </div>
    </div>
  )
}

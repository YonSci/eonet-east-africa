import React, { useState } from 'react'
import useAppStore, { CATEGORIES } from '../store/useAppStore.js'
import { useEvents } from '../api/queries.js'

// Columns shown in the narrow right panel
// Title gets all remaining space; magnitude shown only when present
const COLS = [
  { key: 'latest_date', label: 'Date',     width: 82  },
  { key: 'category',    label: 'Category', width: 104 },
  { key: 'status',      label: 'Status',   width: 60  },
  { key: 'title',       label: 'Title',    width: null },
]

function getCatColor(cat) {
  return (CATEGORIES[cat] || {}).color || '#484f58'
}

export default function EventList() {
  const {
    activeCategories, activeStatus,
    selectedEventId,  selectEvent,
  } = useAppStore()

  const { data: rawEvents = [], isLoading } = useEvents()

  const [sortKey, setSortKey] = useState('latest_date')
  const [sortAsc, setSortAsc] = useState(false)
  const [search,  setSearch]  = useState('')
  const [collapsed, setCollapsed] = useState(false)

  // Filter
  const filtered = rawEvents.filter((ev) => {
    if (!activeCategories.includes(ev.category)) return false
    if (activeStatus === 'open'   && ev.status !== 'open')   return false
    if (activeStatus === 'closed' && ev.status !== 'closed') return false
    if (search && !ev.title.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  // Sort
  const sorted = [...filtered].sort((a, b) => {
    const va = a[sortKey] ?? ''
    const vb = b[sortKey] ?? ''
    const cmp = typeof va === 'string' ? va.localeCompare(vb) : va - vb
    return sortAsc ? cmp : -cmp
  })

  function handleSort(key) {
    if (sortKey === key) setSortAsc(!sortAsc)
    else { setSortKey(key); setSortAsc(false) }
  }

  function exportCSV() {
    const header = ['ID','Title','Category','Status','Date','Lat','Lon']
    const rows   = sorted.map((ev) => [
      ev.id,
      '"' + (ev.title || '').replace(/"/g, '""') + '"',
      ev.category, ev.status,
      (ev.latest_date || '').slice(0,10),
      ev.coords ? ev.coords[1] : '',
      ev.coords ? ev.coords[0] : '',
    ])
    const csv  = [header, ...rows].map((r) => r.join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href = url; a.download = 'eonet_ea_events.csv'; a.click()
    URL.revokeObjectURL(url)
  }

  const panelWidth = collapsed ? 32 : 340

  return (
    <div style={{
      width:       panelWidth,
      flexShrink:  0,
      display:     'flex',
      flexDirection: 'column',
      background:  'var(--bg-surface)',
      borderLeft:  '1px solid var(--border-primary)',
      overflow:    'hidden',
      transition:  'width 0.2s ease',
    }}>

      {/* Collapse toggle strip */}
      <button
        onClick={() => setCollapsed((v) => !v)}
        title={collapsed ? 'Expand event list' : 'Collapse event list'}
        style={{
          width: '100%', flexShrink: 0,
          padding: collapsed ? '12px 0' : '6px 0',
          background: 'var(--bg-elevated)',
          border: 'none',
          borderBottom: '1px solid var(--border-primary)',
          cursor: 'pointer',
          color: 'var(--text-muted)',
          display: 'flex', alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'flex-start',
          paddingLeft: collapsed ? 0 : 10,
          gap: 6,
          fontSize: 12, fontWeight: 500,
          writingMode: collapsed ? 'vertical-rl' : 'horizontal-tb',
        }}
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none"
          style={{ transform: collapsed ? 'rotate(180deg)' : 'rotate(0deg)',
                   transition: 'transform 0.2s', flexShrink: 0 }}>
          <path d="M9 2L5 7L9 12" stroke="currentColor" strokeWidth="1.5"
            strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        {!collapsed && (
          <span style={{ color: 'var(--text-secondary)', letterSpacing: '0.05em',
                         textTransform: 'uppercase', fontSize: 10, fontWeight: 600 }}>
            Events
          </span>
        )}
        {!collapsed && (
          <span style={{ marginLeft: 'auto', marginRight: 8,
                         color: 'var(--text-muted)', fontSize: 11 }}>
            {sorted.length} / {rawEvents.length}
          </span>
        )}
      </button>

      {/* Panel content (hidden when collapsed) */}
      {!collapsed && (
        <>
          {/* Toolbar */}
          <div style={{
            padding: '8px 10px',
            borderBottom: '1px solid var(--border-primary)',
            display: 'flex', gap: 6, alignItems: 'center',
            flexShrink: 0,
          }}>
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search..."
              style={{
                flex: 1,
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border-primary)',
                borderRadius: 6, padding: '4px 8px',
                fontSize: 12, color: 'var(--text-primary)',
                outline: 'none',
              }}
            />
            <button
              onClick={exportCSV}
              title="Export to CSV"
              style={{
                padding: '4px 8px', borderRadius: 6, fontSize: 11,
                border: '1px solid var(--border-primary)',
                background: 'transparent', color: 'var(--text-secondary)',
                cursor: 'pointer', whiteSpace: 'nowrap',
              }}
            >
              CSV
            </button>
          </div>

          {/* Column headers */}
          <div style={{
            display: 'flex',
            borderBottom: '1px solid var(--border-primary)',
            background: 'var(--bg-elevated)',
            flexShrink: 0,
          }}>
            {COLS.map((col) => (
              <div
                key={col.key}
                onClick={() => handleSort(col.key)}
                style={{
                  padding: '5px 8px',
                  fontSize: 10, fontWeight: 600,
                  letterSpacing: '0.06em', textTransform: 'uppercase',
                  color: sortKey === col.key ? 'var(--text-primary)' : 'var(--text-muted)',
                  cursor: 'pointer', userSelect: 'none',
                  width:  col.width || 'auto',
                  flex:   col.width ? 'none' : 1,
                  minWidth: 0,
                  whiteSpace: 'nowrap',
                }}
              >
                {col.label}
                {sortKey === col.key ? (sortAsc ? ' ^' : ' v') : ''}
              </div>
            ))}
          </div>

          {/* Rows */}
          <div style={{ overflowY: 'auto', flex: 1 }}>
            {isLoading && (
              <div style={{ padding: 20, textAlign: 'center',
                            color: 'var(--text-muted)', fontSize: 12 }}>
                Loading...
              </div>
            )}
            {!isLoading && sorted.length === 0 && (
              <div style={{ padding: 20, textAlign: 'center',
                            color: 'var(--text-muted)', fontSize: 12 }}>
                No events match filters.
              </div>
            )}
            {sorted.map((ev) => {
              const isSel  = ev.id === selectedEventId
              const color  = getCatColor(ev.category)
              const isOpen = ev.status === 'open'
              const cat    = CATEGORIES[ev.category] || {}

              return (
                <div
                  key={ev.id}
                  onClick={() => selectEvent(ev.id)}
                  style={{
                    display: 'flex', alignItems: 'stretch',
                    borderBottom: '1px solid var(--border-muted)',
                    background: isSel ? 'var(--bg-hover)' : 'transparent',
                    cursor: 'pointer',
                    borderLeft: isSel ? '3px solid ' + color : '3px solid transparent',
                    transition: 'background 0.1s',
                  }}
                >
                  {/* Date */}
                  <div style={{ width: 82, flexShrink: 0, padding: '6px 8px',
                                fontSize: 11, color: 'var(--text-muted)',
                                lineHeight: 1.4 }}>
                    {(ev.latest_date || '--').slice(0,10)}
                  </div>

                  {/* Category pill */}
                  <div style={{ width: 104, flexShrink: 0, padding: '6px 4px',
                                display: 'flex', alignItems: 'center' }}>
                    <span style={{
                      fontSize: 10, padding: '1px 6px', borderRadius: 100,
                      background: color + '22', color: color,
                      border: '1px solid ' + color + '44',
                      whiteSpace: 'nowrap', overflow: 'hidden',
                      textOverflow: 'ellipsis', maxWidth: 92,
                      display: 'inline-block',
                    }}>
                      {cat.label || ev.category}
                    </span>
                  </div>

                  {/* Status dot */}
                  <div style={{ width: 60, flexShrink: 0, padding: '6px 4px',
                                display: 'flex', alignItems: 'center' }}>
                    <span style={{
                      fontSize: 10, fontWeight: 600,
                      color: isOpen ? 'var(--status-open)' : 'var(--text-muted)',
                    }}>
                      {isOpen ? 'open' : 'closed'}
                    </span>
                  </div>

                  {/* Title */}
                  <div style={{ flex: 1, minWidth: 0, padding: '6px 8px 6px 0',
                                fontSize: 11, color: 'var(--text-primary)',
                                overflow: 'hidden', textOverflow: 'ellipsis',
                                display: '-webkit-box', WebkitLineClamp: 2,
                                WebkitBoxOrient: 'vertical', lineHeight: 1.4 }}>
                    {ev.title}
                  </div>
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}

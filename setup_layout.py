"""
setup_layout.py
---------------
Two targeted changes:
  1. Light mode is now the default (was dark)
  2. Event list panel moves from bottom to right side of the map

Run from the eonet-east-africa project root:
    python setup_layout.py

Files updated:
    frontend/src/store/useAppStore.js     -- lightMode default true
    frontend/src/App.jsx                  -- right-panel layout for map tab
    frontend/src/components/EventList.jsx -- full-height right panel
"""

import sys, argparse
from pathlib import Path

try:
    from colorama import Fore, Style, init as _ci
    _ci(autoreset=True)
    def ok(m):  print(f"{Fore.GREEN}  [+]{Style.RESET_ALL} {m}")
    def ow(m):  print(f"{Fore.YELLOW}  [~]{Style.RESET_ALL} {m}")
    def hdr(m): print(f"\n{Fore.CYAN}{Style.BRIGHT}{m}{Style.RESET_ALL}")
except ImportError:
    def ok(m):  print(f"  [+] {m}")
    def ow(m):  print(f"  [~] {m}")
    def hdr(m): print(f"\n{m}")

FILES = {}

# =============================================================================
# useAppStore.js  --  light mode as default
# =============================================================================
FILES["src/store/useAppStore.js"] = """import { create } from 'zustand'

export const CATEGORIES = {
  wildfires:    { label: 'Wildfires',      color: '#E8593C' },
  severeStorms: { label: 'Severe Storms',  color: '#378ADD' },
  floods:       { label: 'Floods',         color: '#1D9E75' },
  drought:      { label: 'Drought',        color: '#BA7517' },
  volcanoes:    { label: 'Volcanoes',      color: '#E24B4A' },
  dustHaze:     { label: 'Dust and Haze', color: '#888780' },
  earthquakes:  { label: 'Earthquakes',   color: '#7F77DD' },
  landslides:   { label: 'Landslides',    color: '#639922' },
}

export const ALL_CATS = Object.keys(CATEGORIES)

const useAppStore = create((set) => ({
  activeCategories: ALL_CATS,
  activeStatus:     'all',
  lookbackDays:     90,
  selectedEventId:  null,
  lightMode:        true,       // light is the default
  sidebarOpen:      true,
  dataSource:       'auto',

  toggleCategory: (cat) => set((s) => ({
    activeCategories: s.activeCategories.includes(cat)
      ? s.activeCategories.filter((c) => c !== cat)
      : [...s.activeCategories, cat],
  })),
  setAllCategories: (cats) => set({ activeCategories: cats }),
  setStatus:        (v)    => set({ activeStatus: v }),
  setDays:          (v)    => set({ lookbackDays: v }),
  selectEvent:      (id)   => set({ selectedEventId: id }),
  toggleLight: () => set((s) => {
    const next = !s.lightMode
    document.documentElement.classList.toggle('light', next)
    return { lightMode: next }
  }),
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setDataSource:  (v)    => set({ dataSource: v }),
}))

// Apply light mode class on initial load
if (typeof document !== 'undefined') {
  document.documentElement.classList.add('light')
}

export default useAppStore
"""

# =============================================================================
# App.jsx  --  EventList on the RIGHT of the map, not below it
# =============================================================================
FILES["src/App.jsx"] = """import React, { useState } from 'react'
import TopNav         from './components/TopNav.jsx'
import FilterSidebar  from './components/FilterSidebar.jsx'
import StatCards      from './components/StatCards.jsx'
import MapPanel       from './components/MapPanel.jsx'
import EventList      from './components/EventList.jsx'
import AnalyticsPanel from './components/AnalyticsPanel.jsx'
import useAppStore    from './store/useAppStore.js'

const TABS = [
  { id: 'map',       label: 'Map view'  },
  { id: 'analytics', label: 'Analytics' },
]

export default function App() {
  const { sidebarOpen } = useAppStore()
  const [activeTab, setActiveTab] = useState('map')

  return (
    <div style={{ display: 'flex', flexDirection: 'column',
                  height: '100vh', overflow: 'hidden' }}>
      <TopNav />

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Left sidebar */}
        {sidebarOpen && <FilterSidebar />}

        {/* Main content */}
        <main style={{ flex: 1, display: 'flex', flexDirection: 'column',
                       overflow: 'hidden', minWidth: 0 }}>

          <StatCards />

          {/* Tab bar */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 2,
            padding: '8px 14px 0',
            borderBottom: '1px solid var(--border-primary)',
            background: 'var(--bg-base)',
            flexShrink: 0,
          }}>
            {TABS.map((tab) => {
              const active = activeTab === tab.id
              return (
                <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={{
                  padding: '6px 14px', fontSize: 13,
                  fontWeight: active ? 600 : 400,
                  color:  active ? 'var(--text-primary)' : 'var(--text-secondary)',
                  background: 'transparent', border: 'none',
                  borderBottom: '2px solid',
                  borderBottomColor: active ? 'var(--accent-green)' : 'transparent',
                  cursor: 'pointer', transition: 'all 0.15s', marginBottom: -1,
                }}>
                  {tab.label}
                </button>
              )
            })}
            <div style={{ flex: 1 }} />
            <span style={{ fontSize: 11, color: 'var(--text-muted)', paddingBottom: 6 }}>
              ICPAC GHA Region
            </span>
          </div>

          {/* Map tab  --  map LEFT, event list RIGHT */}
          {activeTab === 'map' && (
            <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
              {/* Map takes all remaining horizontal space */}
              <MapPanel />

              {/* Event list panel -- fixed width on the right */}
              <EventList />
            </div>
          )}

          {/* Analytics tab */}
          {activeTab === 'analytics' && <AnalyticsPanel />}

        </main>
      </div>
    </div>
  )
}
"""

# =============================================================================
# EventList.jsx  --  right-side panel (full height, vertical scroll)
# =============================================================================
FILES["src/components/EventList.jsx"] = """import React, { useState } from 'react'
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
    const csv  = [header, ...rows].map((r) => r.join(',')).join('\\n')
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
"""

# =============================================================================
# Builder
# =============================================================================
def build(root: Path):
    hdr(f"Applying layout patch in: {root}")
    created = updated = 0

    for rel, content in FILES.items():
        target = root / "frontend" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        existed = target.exists()
        target.write_text(content, encoding="utf-8")
        if existed:
            ow(f"update  frontend/{rel}")
            updated += 1
        else:
            ok(f"create  frontend/{rel}")
            created += 1

    hdr("Done")
    print(f"  Files created : {created}")
    print(f"  Files updated : {updated}")
    print()
    print("  Changes:")
    print("    - Default theme is now LIGHT (was dark)")
    print("    - Event list is now a RIGHT-SIDE panel (was bottom bar)")
    print("    - Panel is collapsible -- click the arrow strip to collapse/expand")
    print()
    print("  Restart Vite:")
    print("    cd frontend && npm run dev")
    print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Layout patch: light default + right event panel")
    parser.add_argument("--path", default=".", help="Project root (default: current dir)")
    args   = parser.parse_args()
    root   = Path(args.path).resolve()
    if not (root / "backend").exists():
        print(f"WARNING: {root} may not be project root. Continue? [y/N] ", end="")
        if input().strip().lower() != "y":
            sys.exit(0)
    build(root)

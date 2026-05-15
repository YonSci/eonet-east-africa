"""
setup_frontend.py
-----------------
Generates the complete Phase 2 frontend for the EONET East Africa dashboard.
Run from the eonet-east-africa project root.

Usage:
    python setup_frontend.py
"""

import os, sys, argparse
from pathlib import Path

try:
    from colorama import Fore, Style, init as _ci
    _ci(autoreset=True)
    def ok(m):   print(f"{Fore.GREEN}  [+]{Style.RESET_ALL} {m}")
    def skip(m): print(f"{Fore.YELLOW}  [-]{Style.RESET_ALL} {m}")
    def hdr(m):  print(f"\n{Fore.CYAN}{Style.BRIGHT}{m}{Style.RESET_ALL}")
except ImportError:
    def ok(m):   print(f"  [+] {m}")
    def skip(m): print(f"  [-] {m}")
    def hdr(m):  print(f"\n{m}")

FILES = {}

# =============================================================================
# package.json
# =============================================================================
FILES["package.json"] = """{
  "name": "eonet-east-africa",
  "private": true,
  "version": "2.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-leaflet": "^4.2.1",
    "leaflet": "^1.9.4",
    "@tanstack/react-query": "^5.56.2",
    "zustand": "^4.5.5",
    "recharts": "^2.12.7",
    "date-fns": "^3.6.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.1",
    "vite": "^5.4.8"
  }
}
"""

# =============================================================================
# vite.config.js
# =============================================================================
FILES["vite.config.js"] = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: import.meta.env?.VITE_BASE_PATH || '/',
  server: {
    port: 5173,
    proxy: {
      '/events': 'http://localhost:8000',
      '/summary': 'http://localhost:8000',
      '/status':  'http://localhost:8000',
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  }
})
"""

# =============================================================================
# index.html
# =============================================================================
FILES["index.html"] = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>EONET East Africa -- Natural Events Dashboard</title>
    <link rel="icon" type="image/svg+xml"
      href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🌍</text></svg>" />
    <link rel="stylesheet"
      href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
"""

# =============================================================================
# src/main.jsx
# =============================================================================
FILES["src/main.jsx"] = """import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App.jsx'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime:    10 * 60 * 1000,
      gcTime:       30 * 60 * 1000,
      refetchInterval: 15 * 60 * 1000,
      retry: 2,
    }
  }
})

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>
)
"""

# =============================================================================
# src/index.css
# =============================================================================
FILES["src/index.css"] = """/* ---- EONET East Africa Dashboard -- CSS Variables ---- */

:root {
  --bg-base:        #0d1117;
  --bg-surface:     #161b22;
  --bg-elevated:    #21262d;
  --bg-hover:       #2d333b;

  --text-primary:   #e6edf3;
  --text-secondary: #8b949e;
  --text-muted:     #6e7681;
  --text-faint:     #484f58;

  --border-primary: #30363d;
  --border-muted:   #21262d;

  --accent-blue:    #378ADD;
  --accent-green:   #1D9E75;

  /* Category colours */
  --cat-wildfires:    #E8593C;
  --cat-storms:       #378ADD;
  --cat-floods:       #1D9E75;
  --cat-drought:      #BA7517;
  --cat-volcanoes:    #E24B4A;
  --cat-dust:         #888780;
  --cat-earthquakes:  #7F77DD;
  --cat-landslides:   #639922;
  --cat-unknown:      #484f58;

  --status-open:   #1D9E75;
  --status-closed: #6e7681;

  --sidebar-w:     260px;
  --topnav-h:      52px;
  --radius-sm:     4px;
  --radius-md:     8px;
  --radius-lg:     12px;
}

html.light {
  --bg-base:        #f6f8fa;
  --bg-surface:     #ffffff;
  --bg-elevated:    #f0f3f6;
  --bg-hover:       #e8ecf0;
  --text-primary:   #1a1e23;
  --text-secondary: #4a5568;
  --text-muted:     #718096;
  --text-faint:     #a0aec0;
  --border-primary: #d1d9e0;
  --border-muted:   #eaecef;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: var(--bg-base);
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.5;
  overflow: hidden;
  height: 100vh;
}

#root { height: 100vh; display: flex; flex-direction: column; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-surface); }
::-webkit-scrollbar-thumb { background: var(--border-primary); border-radius: 3px; }

/* Leaflet overrides */
.leaflet-container { background: #1a2332 !important; }
.leaflet-popup-content-wrapper {
  background: var(--bg-elevated) !important;
  color: var(--text-primary) !important;
  border: 1px solid var(--border-primary) !important;
  border-radius: var(--radius-md) !important;
  box-shadow: 0 8px 24px rgba(0,0,0,0.4) !important;
}
.leaflet-popup-tip { background: var(--bg-elevated) !important; }
.leaflet-popup-close-button { color: var(--text-secondary) !important; }
.leaflet-control-zoom a {
  background: var(--bg-elevated) !important;
  color: var(--text-primary) !important;
  border-color: var(--border-primary) !important;
}
.leaflet-control-attribution {
  background: rgba(13,17,23,0.7) !important;
  color: var(--text-muted) !important;
}
.leaflet-control-attribution a { color: var(--accent-blue) !important; }

/* Animated pulse for open events */
@keyframes pulse-ring {
  0%   { transform: scale(0.8); opacity: 0.8; }
  100% { transform: scale(2.0); opacity: 0; }
}
.marker-pulse::after {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  border: 2px solid currentColor;
  animation: pulse-ring 2s ease-out infinite;
}
"""

# =============================================================================
# src/store/useAppStore.js
# =============================================================================
FILES["src/store/useAppStore.js"] = """import { create } from 'zustand'

// Category display metadata
export const CATEGORIES = {
  wildfires:    { label: 'Wildfires',      color: '#E8593C', emoji: 'F' },
  severeStorms: { label: 'Severe Storms',  color: '#378ADD', emoji: 'S' },
  floods:       { label: 'Floods',         color: '#1D9E75', emoji: 'W' },
  drought:      { label: 'Drought',        color: '#BA7517', emoji: 'D' },
  volcanoes:    { label: 'Volcanoes',      color: '#E24B4A', emoji: 'V' },
  dustHaze:     { label: 'Dust and Haze', color: '#888780', emoji: 'H' },
  earthquakes:  { label: 'Earthquakes',   color: '#7F77DD', emoji: 'E' },
  landslides:   { label: 'Landslides',    color: '#639922', emoji: 'L' },
}

export const ALL_CATS = Object.keys(CATEGORIES)

const useAppStore = create((set) => ({
  // Filters
  activeCategories: ALL_CATS,
  activeStatus: 'all',      // 'all' | 'open' | 'closed'
  lookbackDays: 90,

  // UI state
  selectedEventId: null,
  lightMode: false,
  sidebarOpen: true,
  dataSource: 'auto',        // 'auto' | 'mock'

  // Actions
  toggleCategory: (cat) => set((s) => ({
    activeCategories: s.activeCategories.includes(cat)
      ? s.activeCategories.filter((c) => c !== cat)
      : [...s.activeCategories, cat]
  })),
  setAllCategories: (cats) => set({ activeCategories: cats }),
  setStatus: (v) => set({ activeStatus: v }),
  setDays: (v) => set({ lookbackDays: v }),
  selectEvent: (id) => set({ selectedEventId: id }),
  toggleLight: () => set((s) => {
    const next = !s.lightMode
    document.documentElement.classList.toggle('light', next)
    return { lightMode: next }
  }),
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setDataSource: (v) => set({ dataSource: v }),
}))

export default useAppStore
"""

# =============================================================================
# src/api/queries.js
# =============================================================================
FILES["src/api/queries.js"] = """import { useQuery } from '@tanstack/react-query'
import useAppStore from '../store/useAppStore.js'

// ---------------------------------------------------------------------------
// Offline mock data -- 12 realistic East Africa events
// Used when backend is unreachable and dataSource === 'mock'
// ---------------------------------------------------------------------------
export const MOCK_EVENTS = [
  { id:'EONET_6001', title:'Wildfire - Marsabit County, Kenya',            category:'wildfires',    status:'open',   closed:null,              latest_date:'2025-03-15', coords:[37.97,2.34],   sources:[{id:'MODIS_C6_Terra',url:'https://earthdata.nasa.gov/firms'}], magnitude:null },
  { id:'EONET_6002', title:'Wildfire - Serengeti-Mara, Tanzania',          category:'wildfires',    status:'closed', closed:'2025-02-28',       latest_date:'2025-02-20', coords:[34.83,-2.31],  sources:[{id:'MODIS_C6_Aqua',url:'https://earthdata.nasa.gov/firms'}],  magnitude:null },
  { id:'EONET_6003', title:'Wildfire - Ogaden, Somali Region, Ethiopia',   category:'wildfires',    status:'open',   closed:null,              latest_date:'2025-03-22', coords:[43.52,7.86],   sources:[{id:'VIIRS_SNPP_NRT',url:'https://earthdata.nasa.gov/firms'}], magnitude:null },
  { id:'EONET_6004', title:'Flood - Tana River Basin, Kenya',              category:'floods',       status:'closed', closed:'2025-04-02',       latest_date:'2025-03-10', coords:[40.12,-0.52],  sources:[{id:'GDACS',url:'https://gdacs.org'}],                          magnitude:{value:3.5,unit:'m'} },
  { id:'EONET_6005', title:'Flood - Sobat River, South Sudan',             category:'floods',       status:'open',   closed:null,              latest_date:'2025-03-05', coords:[33.57,9.34],   sources:[{id:'GDACS',url:'https://gdacs.org'}],                          magnitude:{value:2.1,unit:'m'} },
  { id:'EONET_6006', title:'Dust and Haze - Horn of Africa',               category:'dustHaze',     status:'open',   closed:null,              latest_date:'2025-03-20', coords:[44.51,8.12],   sources:[{id:'MODIS_C6_Aqua',url:'https://worldview.earthdata.nasa.gov'}], magnitude:null },
  { id:'EONET_6007', title:'Dust and Haze - Lake Turkana Region',          category:'dustHaze',     status:'closed', closed:'2025-02-16',       latest_date:'2025-02-14', coords:[36.10,3.55],   sources:[{id:'MODIS_C6_Terra',url:'https://worldview.earthdata.nasa.gov'}], magnitude:null },
  { id:'EONET_6008', title:'Volcano - Ol Doinyo Lengai, Tanzania',         category:'volcanoes',    status:'open',   closed:null,              latest_date:'2025-01-10', coords:[35.90,-2.76],  sources:[{id:'Smithsonian_GVP',url:'https://volcano.si.edu'}],          magnitude:null },
  { id:'EONET_6009', title:'Earthquake - East African Rift, Tanzania',     category:'earthquakes',  status:'closed', closed:'2025-03-25',       latest_date:'2025-03-25', coords:[29.68,-7.12],  sources:[{id:'USGS_EHP',url:'https://earthquake.usgs.gov'}],            magnitude:{value:4.5,unit:'Richter'} },
  { id:'EONET_6010', title:'Severe Storm - Tropical Cyclone Jude',         category:'severeStorms', status:'closed', closed:'2025-03-18',       latest_date:'2025-03-12', coords:[40.30,-14.20], sources:[{id:'JTWC',url:'https://www.metoc.navy.mil/jtwc/jtwc.html'}],  magnitude:{value:95,unit:'kts'} },
  { id:'EONET_6011', title:'Drought - Horn of Africa',                     category:'drought',      status:'open',   closed:null,              latest_date:'2024-12-01', coords:[43.14,10.30],  sources:[{id:'FEWS_NET',url:'https://fews.net'}],                        magnitude:null },
  { id:'EONET_6012', title:'Landslide - Kericho County, Kenya Highlands',  category:'landslides',   status:'closed', closed:'2025-03-28',       latest_date:'2025-03-28', coords:[35.28,-0.37],  sources:[{id:'ReliefWeb',url:'https://reliefweb.int'}],                  magnitude:null },
]

const MOCK_SUMMARY = {
  total: 12,
  open: 6,
  closed: 6,
  by_category: { wildfires:3, floods:2, dustHaze:2, volcanoes:1, earthquakes:1, severeStorms:1, drought:1, landslides:1 }
}

// ---------------------------------------------------------------------------
// Fetch helpers
// ---------------------------------------------------------------------------
const API = import.meta.env.VITE_API_BASE_URL || ''

async function fetchEvents(days, status, category) {
  const params = new URLSearchParams({ days, status })
  if (category) params.set('category', category)
  const res = await fetch(`${API}/events?${params}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  const data = await res.json()
  return data.events || []
}

async function fetchSummary() {
  const res = await fetch(`${API}/summary`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

async function fetchStatus() {
  const res = await fetch(`${API}/status`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

// ---------------------------------------------------------------------------
// Hooks
// ---------------------------------------------------------------------------
export function useEvents() {
  const { activeStatus, lookbackDays, dataSource } = useAppStore()

  return useQuery({
    queryKey: ['events', activeStatus, lookbackDays, dataSource],
    queryFn: async () => {
      if (dataSource === 'mock') return MOCK_EVENTS
      try {
        return await fetchEvents(lookbackDays, activeStatus)
      } catch {
        console.warn('[useEvents] Backend unreachable -- using mock data')
        return MOCK_EVENTS
      }
    },
    staleTime: 10 * 60 * 1000,
  })
}

export function useSummary() {
  const { dataSource } = useAppStore()

  return useQuery({
    queryKey: ['summary', dataSource],
    queryFn: async () => {
      if (dataSource === 'mock') return MOCK_SUMMARY
      try {
        return await fetchSummary()
      } catch {
        return MOCK_SUMMARY
      }
    },
    staleTime: 10 * 60 * 1000,
  })
}

export function useCacheStatus() {
  const { dataSource } = useAppStore()

  return useQuery({
    queryKey: ['cache_status', dataSource],
    queryFn: async () => {
      if (dataSource === 'mock') return { cached: false, event_count: 12, note: 'offline mock' }
      try {
        return await fetchStatus()
      } catch {
        return null
      }
    },
    refetchInterval: 60 * 1000,
  })
}
"""

# =============================================================================
# src/components/TopNav.jsx
# =============================================================================
FILES["src/components/TopNav.jsx"] = """import React from 'react'
import useAppStore from '../store/useAppStore.js'
import { useCacheStatus } from '../api/queries.js'

export default function TopNav() {
  const { lightMode, toggleLight, toggleSidebar, dataSource, setDataSource } = useAppStore()
  const { data: cacheInfo } = useCacheStatus()

  const isMock = dataSource === 'mock'

  return (
    <header style={{
      height: 'var(--topnav-h)',
      background: 'var(--bg-surface)',
      borderBottom: '1px solid var(--border-primary)',
      display: 'flex',
      alignItems: 'center',
      padding: '0 16px',
      gap: 12,
      flexShrink: 0,
      zIndex: 100,
    }}>
      {/* Sidebar toggle */}
      <button
        onClick={toggleSidebar}
        title="Toggle sidebar"
        style={btnStyle}
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
          <rect x="1" y="3" width="14" height="1.5" rx="0.75"/>
          <rect x="1" y="7.25" width="14" height="1.5" rx="0.75"/>
          <rect x="1" y="11.5" width="14" height="1.5" rx="0.75"/>
        </svg>
      </button>

      {/* Logo + title */}
      <span style={{ fontSize: 16, lineHeight: 1 }}>globe</span>
      <span style={{ fontWeight: 600, fontSize: 15, color: 'var(--text-primary)', whiteSpace: 'nowrap' }}>
        EONET East Africa
      </span>
      <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>
        Natural Events Dashboard
      </span>

      {/* Spacer */}
      <div style={{ flex: 1 }} />

      {/* Data source badge */}
      {isMock && (
        <span style={{
          fontSize: 11, fontWeight: 500,
          padding: '2px 8px', borderRadius: 100,
          background: '#412402', color: '#FAC775',
          border: '1px solid #633806',
        }}>
          OFFLINE MOCK
        </span>
      )}

      {/* Cache info */}
      {cacheInfo && !isMock && (
        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
          {cacheInfo.event_count} events cached
          {cacheInfo.ttl_remaining_s != null
            ? ' -- refresh in ' + Math.ceil(cacheInfo.ttl_remaining_s / 60) + 'm'
            : ''}
        </span>
      )}

      {/* Mock toggle */}
      <button
        onClick={() => setDataSource(isMock ? 'auto' : 'mock')}
        title={isMock ? 'Switch to live API' : 'Switch to offline mock'}
        style={{ ...btnStyle, fontSize: 11, padding: '4px 10px', borderRadius: 6,
                 background: isMock ? 'var(--bg-elevated)' : 'transparent' }}
      >
        {isMock ? 'Use live API' : 'Use mock'}
      </button>

      {/* Light/dark toggle */}
      <button onClick={toggleLight} title="Toggle light mode" style={btnStyle}>
        {lightMode ? (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="4"/>
            <line x1="12" y1="2" x2="12" y2="4"/>
            <line x1="12" y1="20" x2="12" y2="22"/>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
            <line x1="2" y1="12" x2="4" y2="12"/>
            <line x1="20" y1="12" x2="22" y2="12"/>
          </svg>
        ) : (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
          </svg>
        )}
      </button>

      {/* ILRI badge */}
      <span style={{
        fontSize: 11, fontWeight: 600, padding: '3px 8px',
        border: '1px solid var(--border-primary)',
        borderRadius: 6, color: 'var(--text-secondary)',
      }}>
        ILRI
      </span>
    </header>
  )
}

const btnStyle = {
  background: 'transparent',
  border: 'none',
  color: 'var(--text-secondary)',
  cursor: 'pointer',
  padding: '6px',
  borderRadius: 6,
  display: 'flex',
  alignItems: 'center',
  fontSize: 13,
}
"""

# =============================================================================
# src/components/StatCards.jsx
# =============================================================================
FILES["src/components/StatCards.jsx"] = """import React from 'react'
import { useSummary } from '../api/queries.js'
import { CATEGORIES } from '../store/useAppStore.js'

export default function StatCards() {
  const { data: summary, isLoading } = useSummary()

  const cards = [
    { label: 'Total Events',   value: summary?.total  ?? '--', color: 'var(--accent-blue)',  sub: 'in bounding box' },
    { label: 'Open',           value: summary?.open   ?? '--', color: 'var(--status-open)',  sub: 'currently active' },
    { label: 'Closed',         value: summary?.closed ?? '--', color: 'var(--text-muted)',   sub: 'resolved events' },
    { label: 'Categories',     value: Object.keys(summary?.by_category || {}).length || '--', color: '#7F77DD', sub: 'event types' },
  ]

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(4, 1fr)',
      gap: 10,
      padding: '10px 14px 0',
      flexShrink: 0,
    }}>
      {cards.map((c) => (
        <div key={c.label} style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-primary)',
          borderRadius: 'var(--radius-md)',
          padding: '10px 14px',
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
        }}>
          <span style={{ fontSize: 22, fontWeight: 600, color: c.color }}>
            {isLoading ? '...' : c.value}
          </span>
          <span style={{ fontSize: 13, color: 'var(--text-primary)', fontWeight: 500 }}>
            {c.label}
          </span>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{c.sub}</span>
        </div>
      ))}
    </div>
  )
}
"""

# =============================================================================
# src/components/FilterSidebar.jsx
# =============================================================================
FILES["src/components/FilterSidebar.jsx"] = """import React from 'react'
import useAppStore, { CATEGORIES, ALL_CATS } from '../store/useAppStore.js'
import { useSummary } from '../api/queries.js'

const STATUS_OPTS = [
  { value: 'all',    label: 'All events' },
  { value: 'open',   label: 'Open only' },
  { value: 'closed', label: 'Closed only' },
]

const DAY_OPTS = [7, 14, 30, 60, 90, 180, 365]

export default function FilterSidebar() {
  const {
    activeCategories, toggleCategory, setAllCategories,
    activeStatus, setStatus,
    lookbackDays, setDays,
  } = useAppStore()

  const { data: summary } = useSummary()
  const byCat = summary?.by_category || {}

  const allOn  = activeCategories.length === ALL_CATS.length
  const noneOn = activeCategories.length === 0

  return (
    <aside style={{
      width: 'var(--sidebar-w)',
      background: 'var(--bg-surface)',
      borderRight: '1px solid var(--border-primary)',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
      flexShrink: 0,
    }}>
      <div style={{ overflowY: 'auto', flex: 1, padding: '14px 12px' }}>

        {/* -- Status -- */}
        <Section label="Status">
          {STATUS_OPTS.map((o) => (
            <Pill
              key={o.value}
              active={activeStatus === o.value}
              onClick={() => setStatus(o.value)}
            >
              {o.label}
            </Pill>
          ))}
        </Section>

        {/* -- Lookback -- */}
        <Section label="Lookback window">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {DAY_OPTS.map((d) => (
              <Pill
                key={d}
                active={lookbackDays === d}
                onClick={() => setDays(d)}
              >
                {d}d
              </Pill>
            ))}
          </div>
        </Section>

        {/* -- Categories -- */}
        <Section label="Event categories">
          <div style={{ display: 'flex', gap: 6, marginBottom: 10 }}>
            <button
              style={smallBtn(allOn)}
              onClick={() => setAllCategories(ALL_CATS)}
            >All</button>
            <button
              style={smallBtn(noneOn)}
              onClick={() => setAllCategories([])}
            >None</button>
          </div>

          {ALL_CATS.map((cat) => {
            const meta    = CATEGORIES[cat]
            const active  = activeCategories.includes(cat)
            const count   = byCat[cat] || 0

            return (
              <button
                key={cat}
                onClick={() => toggleCategory(cat)}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '6px 8px',
                  marginBottom: 3,
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid',
                  borderColor: active ? meta.color + '55' : 'var(--border-muted)',
                  background: active ? meta.color + '1A' : 'transparent',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.15s',
                }}
              >
                {/* Dot */}
                <span style={{
                  width: 10, height: 10, borderRadius: '50%', flexShrink: 0,
                  background: active ? meta.color : 'var(--text-faint)',
                  transition: 'background 0.15s',
                }} />
                {/* Label */}
                <span style={{
                  flex: 1, fontSize: 13,
                  color: active ? 'var(--text-primary)' : 'var(--text-secondary)',
                  fontWeight: active ? 500 : 400,
                }}>
                  {meta.label}
                </span>
                {/* Count badge */}
                {count > 0 && (
                  <span style={{
                    fontSize: 11, padding: '1px 5px', borderRadius: 100,
                    background: active ? meta.color + '33' : 'var(--bg-elevated)',
                    color: active ? meta.color : 'var(--text-muted)',
                  }}>
                    {count}
                  </span>
                )}
              </button>
            )
          })}
        </Section>

        {/* -- About -- */}
        <Section label="Data source">
          <p style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.6 }}>
            NASA EONET v3 API filtered to East Africa bbox
            (21.8-51.4 E, 11.7 S - 22.0 N). Auto-refreshed every 15 min.
          </p>
          <a
            href="https://eonet.gsfc.nasa.gov/docs/v3"
            target="_blank"
            rel="noreferrer"
            style={{ fontSize: 11, color: 'var(--accent-blue)', display: 'block', marginTop: 6 }}
          >
            EONET API docs
          </a>
        </Section>
      </div>
    </aside>
  )
}

// ---- Small components ----

function Section({ label, children }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <p style={{
        fontSize: 10, fontWeight: 600, letterSpacing: '0.08em',
        textTransform: 'uppercase', color: 'var(--text-muted)',
        marginBottom: 8,
      }}>
        {label}
      </p>
      {children}
    </div>
  )
}

function Pill({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '4px 10px', borderRadius: 100, fontSize: 12,
        border: '1px solid',
        borderColor: active ? 'var(--accent-blue)' : 'var(--border-primary)',
        background: active ? 'var(--accent-blue)' : 'transparent',
        color: active ? '#fff' : 'var(--text-secondary)',
        cursor: 'pointer', marginBottom: 4,
      }}
    >
      {children}
    </button>
  )
}

function smallBtn(active) {
  return {
    fontSize: 12, padding: '3px 10px', borderRadius: 6,
    border: '1px solid var(--border-primary)',
    background: active ? 'var(--bg-elevated)' : 'transparent',
    color: active ? 'var(--text-primary)' : 'var(--text-secondary)',
    cursor: 'pointer',
  }
}
"""

# =============================================================================
# src/components/MapPanel.jsx
# =============================================================================
FILES["src/components/MapPanel.jsx"] = """import React, { useEffect, useRef } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import useAppStore, { CATEGORIES } from '../store/useAppStore.js'
import { useEvents } from '../api/queries.js'

// East Africa bounds and center
const EA_CENTER  = [4.0, 36.5]
const EA_BOUNDS  = [[-11.7, 21.8], [22.0, 51.4]]

const TILE_DARK  = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
const TILE_LIGHT = 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'
const ATTR       = '(c) OpenStreetMap contributors, (c) CARTO'

function getCatColor(cat) {
  return (CATEGORIES[cat] || {}).color || '#484f58'
}

// Fly to selected event
function FlyTo({ events, selectedId }) {
  const map = useMap()
  useEffect(() => {
    if (!selectedId) return
    const ev = events.find((e) => e.id === selectedId)
    if (ev && ev.coords) {
      map.flyTo([ev.coords[1], ev.coords[0]], 7, { duration: 1.2 })
    }
  }, [selectedId, events, map])
  return null
}

export default function MapPanel({ height }) {
  const { activeCategories, activeStatus, selectedEventId, selectEvent, lightMode } = useAppStore()
  const { data: rawEvents = [], isLoading } = useEvents()

  // Apply local filters
  const events = rawEvents.filter((ev) => {
    if (!activeCategories.includes(ev.category)) return false
    if (activeStatus === 'open'   && ev.status !== 'open')   return false
    if (activeStatus === 'closed' && ev.status !== 'closed') return false
    return ev.coords != null
  })

  const tileUrl = lightMode ? TILE_LIGHT : TILE_DARK

  return (
    <div style={{
      flex: 1,
      position: 'relative',
      background: 'var(--bg-base)',
      minHeight: height || 340,
    }}>
      {/* Loading overlay */}
      {isLoading && (
        <div style={{
          position: 'absolute', inset: 0, zIndex: 500,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: 'rgba(13,17,23,0.6)', fontSize: 13,
          color: 'var(--text-secondary)',
        }}>
          Loading events...
        </div>
      )}

      {/* Event count badge */}
      <div style={{
        position: 'absolute', top: 10, right: 10, zIndex: 400,
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border-primary)',
        borderRadius: 6, padding: '4px 10px',
        fontSize: 12, color: 'var(--text-secondary)',
        pointerEvents: 'none',
      }}>
        {events.length} event{events.length !== 1 ? 's' : ''} shown
      </div>

      <MapContainer
        center={EA_CENTER}
        zoom={4}
        maxBounds={EA_BOUNDS}
        minZoom={3}
        maxZoom={12}
        style={{ width: '100%', height: '100%' }}
        zoomControl={true}
      >
        <TileLayer url={tileUrl} attribution={ATTR} />
        <FlyTo events={events} selectedId={selectedEventId} />

        {events.map((ev) => {
          const color   = getCatColor(ev.category)
          const isOpen  = ev.status === 'open'
          const isSel   = ev.id === selectedEventId
          const cat     = CATEGORIES[ev.category] || {}

          return (
            <CircleMarker
              key={ev.id}
              center={[ev.coords[1], ev.coords[0]]}
              radius={isSel ? 12 : isOpen ? 8 : 6}
              pathOptions={{
                color:       isSel ? '#fff'      : color,
                fillColor:   color,
                fillOpacity: isOpen ? 0.85 : 0.45,
                weight:      isSel ? 2.5 : isOpen ? 1.5 : 1,
                dashArray:   isOpen ? null : '4 3',
              }}
              eventHandlers={{ click: () => selectEvent(ev.id) }}
            >
              <Popup maxWidth={280}>
                <div style={{ fontFamily: 'inherit', minWidth: 220 }}>
                  {/* Category pill */}
                  <div style={{ marginBottom: 8 }}>
                    <span style={{
                      fontSize: 11, fontWeight: 500,
                      padding: '2px 8px', borderRadius: 100,
                      background: color + '33', color: color,
                      border: '1px solid ' + color + '55',
                    }}>
                      {cat.label || ev.category}
                    </span>
                    <span style={{
                      fontSize: 11, marginLeft: 6,
                      color: isOpen ? 'var(--status-open)' : 'var(--text-muted)',
                      fontWeight: 500,
                    }}>
                      {isOpen ? 'OPEN' : 'CLOSED'}
                    </span>
                  </div>

                  {/* Title */}
                  <p style={{ fontWeight: 600, fontSize: 13,
                              color: 'var(--text-primary)', lineHeight: 1.4,
                              marginBottom: 8 }}>
                    {ev.title}
                  </p>

                  {/* Details */}
                  <table style={{ fontSize: 12, color: 'var(--text-secondary)',
                                  borderCollapse: 'collapse', width: '100%' }}>
                    <tbody>
                      <Row label="Date"   value={ev.latest_date?.slice(0,10) || '--'} />
                      {ev.closed && (
                        <Row label="Closed" value={ev.closed.slice(0,10)} />
                      )}
                      {ev.magnitude && (
                        <Row
                          label="Magnitude"
                          value={ev.magnitude.value + ' ' + (ev.magnitude.unit || '')}
                        />
                      )}
                      <Row
                        label="Coords"
                        value={ev.coords[1].toFixed(2) + ', ' + ev.coords[0].toFixed(2)}
                      />
                    </tbody>
                  </table>

                  {/* Sources */}
                  {ev.sources && ev.sources.length > 0 && (
                    <div style={{ marginTop: 8 }}>
                      <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                        Source:{' '}
                      </span>
                      {ev.sources.map((s, i) => (
                        <a
                          key={i}
                          href={s.url}
                          target="_blank"
                          rel="noreferrer"
                          style={{ fontSize: 11, color: 'var(--accent-blue)',
                                   marginRight: 6 }}
                        >
                          {s.id}
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              </Popup>
            </CircleMarker>
          )
        })}
      </MapContainer>
    </div>
  )
}

function Row({ label, value }) {
  return (
    <tr>
      <td style={{ color: 'var(--text-muted)', paddingRight: 10,
                   paddingBottom: 3, whiteSpace: 'nowrap' }}>
        {label}
      </td>
      <td style={{ color: 'var(--text-secondary)', paddingBottom: 3 }}>
        {value}
      </td>
    </tr>
  )
}
"""

# =============================================================================
# src/components/EventList.jsx
# =============================================================================
FILES["src/components/EventList.jsx"] = """import React, { useState } from 'react'
import useAppStore, { CATEGORIES } from '../store/useAppStore.js'
import { useEvents } from '../api/queries.js'

const COLS = [
  { key: 'latest_date', label: 'Date',     width: 90  },
  { key: 'category',    label: 'Category', width: 130 },
  { key: 'status',      label: 'Status',   width: 72  },
  { key: 'title',       label: 'Title',    width: null },
  { key: 'magnitude',   label: 'Magnitude',width: 90  },
]

function getCatColor(cat) {
  return (CATEGORIES[cat] || {}).color || '#484f58'
}

export default function EventList() {
  const { activeCategories, activeStatus, selectedEventId, selectEvent } = useAppStore()
  const { data: rawEvents = [], isLoading } = useEvents()

  const [sortKey, setSortKey]   = useState('latest_date')
  const [sortAsc, setSortAsc]   = useState(false)
  const [search,  setSearch]    = useState('')

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
    let va = a[sortKey] ?? ''
    let vb = b[sortKey] ?? ''
    if (sortKey === 'magnitude') {
      va = a.magnitude?.value ?? -1
      vb = b.magnitude?.value ?? -1
    }
    const cmp = typeof va === 'string' ? va.localeCompare(vb) : va - vb
    return sortAsc ? cmp : -cmp
  })

  function handleSort(key) {
    if (sortKey === key) setSortAsc(!sortAsc)
    else { setSortKey(key); setSortAsc(false) }
  }

  function exportCSV() {
    const header = ['ID', 'Title', 'Category', 'Status', 'Date', 'Magnitude', 'Lat', 'Lon']
    const rows   = sorted.map((ev) => [
      ev.id, ev.title, ev.category, ev.status,
      ev.latest_date?.slice(0,10) || '',
      ev.magnitude ? ev.magnitude.value + ' ' + (ev.magnitude.unit || '') : '',
      ev.coords ? ev.coords[1] : '', ev.coords ? ev.coords[0] : '',
    ])
    const csv  = [header, ...rows].map((r) => r.join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href = url; a.download = 'eonet_ea_events.csv'; a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div style={{
      background: 'var(--bg-surface)',
      borderTop: '1px solid var(--border-primary)',
      display: 'flex',
      flexDirection: 'column',
      height: 220,
      flexShrink: 0,
    }}>
      {/* Toolbar */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '8px 14px',
        borderBottom: '1px solid var(--border-primary)',
        flexShrink: 0,
      }}>
        <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)',
                       textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          Events
        </span>
        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
          {sorted.length} of {rawEvents.length}
        </span>
        <div style={{ flex: 1 }} />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search events..."
          style={{
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border-primary)',
            borderRadius: 6, padding: '4px 10px',
            fontSize: 12, color: 'var(--text-primary)',
            width: 180, outline: 'none',
          }}
        />
        <button
          onClick={exportCSV}
          style={{
            fontSize: 12, padding: '4px 10px', borderRadius: 6,
            border: '1px solid var(--border-primary)',
            background: 'transparent', color: 'var(--text-secondary)',
            cursor: 'pointer',
          }}
        >
          Export CSV
        </button>
      </div>

      {/* Table */}
      <div style={{ overflowY: 'auto', flex: 1 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
          <thead style={{ position: 'sticky', top: 0, background: 'var(--bg-elevated)',
                          zIndex: 1 }}>
            <tr>
              {COLS.map((col) => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  style={{
                    padding: '6px 10px', textAlign: 'left',
                    color: sortKey === col.key ? 'var(--text-primary)' : 'var(--text-muted)',
                    fontWeight: 500, cursor: 'pointer', userSelect: 'none',
                    borderBottom: '1px solid var(--border-primary)',
                    width: col.width || 'auto',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {col.label}
                  {sortKey === col.key ? (sortAsc ? ' ^' : ' v') : ''}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td colSpan={5} style={{ padding: '20px', textAlign: 'center',
                                         color: 'var(--text-muted)' }}>
                  Loading...
                </td>
              </tr>
            )}
            {!isLoading && sorted.length === 0 && (
              <tr>
                <td colSpan={5} style={{ padding: '20px', textAlign: 'center',
                                         color: 'var(--text-muted)' }}>
                  No events match current filters.
                </td>
              </tr>
            )}
            {sorted.map((ev) => {
              const isSel  = ev.id === selectedEventId
              const color  = getCatColor(ev.category)
              const isOpen = ev.status === 'open'
              const cat    = CATEGORIES[ev.category] || {}

              return (
                <tr
                  key={ev.id}
                  onClick={() => selectEvent(ev.id)}
                  style={{
                    background: isSel ? 'var(--bg-hover)' : 'transparent',
                    borderBottom: '1px solid var(--border-muted)',
                    cursor: 'pointer',
                    transition: 'background 0.1s',
                  }}
                >
                  {/* Date */}
                  <td style={{ padding: '5px 10px', color: 'var(--text-muted)',
                               whiteSpace: 'nowrap' }}>
                    {ev.latest_date?.slice(0,10) || '--'}
                  </td>

                  {/* Category */}
                  <td style={{ padding: '5px 10px' }}>
                    <span style={{
                      fontSize: 11, padding: '1px 7px', borderRadius: 100,
                      background: color + '22', color: color,
                      border: '1px solid ' + color + '44',
                      whiteSpace: 'nowrap',
                    }}>
                      {cat.label || ev.category}
                    </span>
                  </td>

                  {/* Status */}
                  <td style={{ padding: '5px 10px' }}>
                    <span style={{
                      fontSize: 11, fontWeight: 500,
                      color: isOpen ? 'var(--status-open)' : 'var(--text-muted)',
                    }}>
                      {isOpen ? 'open' : 'closed'}
                    </span>
                  </td>

                  {/* Title */}
                  <td style={{ padding: '5px 10px', color: 'var(--text-primary)',
                               maxWidth: 0, overflow: 'hidden',
                               textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {ev.title}
                  </td>

                  {/* Magnitude */}
                  <td style={{ padding: '5px 10px', color: 'var(--text-secondary)',
                               whiteSpace: 'nowrap' }}>
                    {ev.magnitude
                      ? ev.magnitude.value + ' ' + (ev.magnitude.unit || '')
                      : '-'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
"""

# =============================================================================
# src/App.jsx
# =============================================================================
FILES["src/App.jsx"] = """import React from 'react'
import TopNav       from './components/TopNav.jsx'
import FilterSidebar from './components/FilterSidebar.jsx'
import StatCards    from './components/StatCards.jsx'
import MapPanel     from './components/MapPanel.jsx'
import EventList    from './components/EventList.jsx'
import useAppStore  from './store/useAppStore.js'

export default function App() {
  const { sidebarOpen } = useAppStore()

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      <TopNav />

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Sidebar */}
        {sidebarOpen && <FilterSidebar />}

        {/* Main content */}
        <main style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          minWidth: 0,
        }}>
          <StatCards />
          <MapPanel />
          <EventList />
        </main>
      </div>
    </div>
  )
}
"""

# =============================================================================
# Builder
# =============================================================================
def build(root: Path):
    hdr(f"Setting up Phase 2 frontend in: {root / 'frontend'}")
    created = skipped = 0

    for rel, content in FILES.items():
        target = root / "frontend" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            skip(f"exists  frontend/{rel}")
            skipped += 1
        else:
            target.write_text(content, encoding="utf-8")
            ok(f"create  frontend/{rel}")
            created += 1

    hdr("Done")
    print(f"  Files created : {created}")
    print(f"  Files skipped : {skipped}")
    print()
    print("  Next steps:")
    print("    cd frontend")
    print("    npm install")
    print("    npm run dev")
    print()
    print("  Then open http://localhost:5173")
    print()
    print("  Tip: if the backend is not running, click 'Use mock'")
    print("  in the top nav to load offline sample data.")
    print()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Setup Phase 2 frontend")
    parser.add_argument("--path", default=".", help="Project root (default: current dir)")
    args = parser.parse_args()
    root = Path(args.path).resolve()
    if not (root / "backend").exists():
        print(f"WARNING: {root} does not look like the eonet-east-africa root.")
        print("Run from the project root or pass --path to the correct folder.")
    build(root)

"""
setup_tier1.py
--------------
Adds all 7 Tier 1 professional features to NET-EA:

  1. Marker clustering (react-leaflet-cluster)
  2. Loading skeleton states (CSS pulse animation)
  3. NASA GIBS satellite imagery layers (WMTS toggle on map)
  4. Date range picker (custom start/end alongside lookback days)
  5. New event toast notifications (diff detection on each refresh)
  6. Shareable / bookmarkable URLs (filters encoded in query string)
  7. PDF bulletin export (print stylesheet + dedicated print view)

Run from the eonet-east-africa project root:
    python setup_tier1.py

Then:
    cd frontend
    npm install        <-- installs react-leaflet-cluster
    npm run dev
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
# package.json  --  add react-leaflet-cluster
# =============================================================================
FILES["frontend/package.json"] = """{
  "name": "eonet-east-africa",
  "private": true,
  "version": "3.0.0",
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
    "react-leaflet-cluster": "^2.1.0",
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
# index.html  --  add markercluster CSS from CDN
# =============================================================================
FILES["frontend/index.html"] = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>NET-EA -- Natural Event Tracker for East Africa</title>
    <meta name="description"
      content="Near real-time natural hazard monitoring for the Greater Horn of Africa, powered by NASA EONET v3." />
    <link rel="icon" type="image/svg+xml"
      href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>satellite</text></svg>" />
    <link rel="stylesheet"
      href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
    <link rel="stylesheet"
      href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
"""

# =============================================================================
# src/index.css  --  skeleton animation + toast styles + print CSS
# =============================================================================
FILES["frontend/src/index.css"] = """
:root {
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
  --accent-blue:    #378ADD;
  --accent-green:   #1D9E75;
  --cat-wildfires:    #E8593C;
  --cat-storms:       #378ADD;
  --cat-floods:       #1D9E75;
  --cat-drought:      #BA7517;
  --cat-volcanoes:    #E24B4A;
  --cat-dust:         #888780;
  --cat-earthquakes:  #7F77DD;
  --cat-landslides:   #639922;
  --status-open:   #1D9E75;
  --status-closed: #6e7681;
  --sidebar-w:     260px;
  --topnav-h:      52px;
  --radius-sm:     4px;
  --radius-md:     8px;
  --radius-lg:     12px;
}

html:not(.light) {
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

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-surface); }
::-webkit-scrollbar-thumb { background: var(--border-primary); border-radius: 3px; }

/* -- Leaflet overrides --------------------------------------------------- */
.leaflet-container { background: #e8f0e0 !important; }
html:not(.light) .leaflet-container { background: #1a2332 !important; }
.leaflet-popup-content-wrapper {
  background: var(--bg-elevated) !important;
  color: var(--text-primary) !important;
  border: 1px solid var(--border-primary) !important;
  border-radius: var(--radius-md) !important;
  box-shadow: 0 8px 24px rgba(0,0,0,0.15) !important;
}
.leaflet-popup-tip { background: var(--bg-elevated) !important; }
.leaflet-popup-close-button { color: var(--text-secondary) !important; }
.leaflet-control-zoom a {
  background: var(--bg-elevated) !important;
  color: var(--text-primary) !important;
  border-color: var(--border-primary) !important;
}
.leaflet-control-attribution {
  background: rgba(255,255,255,0.75) !important;
  color: var(--text-muted) !important;
}
html:not(.light) .leaflet-control-attribution {
  background: rgba(13,17,23,0.7) !important;
}
.leaflet-control-attribution a { color: var(--accent-blue) !important; }

/* -- Marker cluster overrides -------------------------------------------- */
.marker-cluster-small, .marker-cluster-medium, .marker-cluster-large {
  background: rgba(29, 158, 117, 0.18) !important;
}
.marker-cluster-small div, .marker-cluster-medium div, .marker-cluster-large div {
  background: rgba(29, 158, 117, 0.55) !important;
  color: #fff !important;
  font-weight: 600 !important;
  font-size: 12px !important;
}

/* -- Skeleton animation -------------------------------------------------- */
@keyframes skel-pulse {
  0%   { opacity: 1; }
  50%  { opacity: 0.4; }
  100% { opacity: 1; }
}
.skeleton {
  background: var(--border-muted);
  border-radius: var(--radius-sm);
  animation: skel-pulse 1.4s ease-in-out infinite;
}

/* -- Toast container ----------------------------------------------------- */
.toast-container {
  position: fixed;
  top: 62px;
  right: 14px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 8px;
  pointer-events: none;
}
.toast {
  pointer-events: auto;
  background: var(--bg-surface);
  border: 1px solid var(--border-primary);
  border-left: 3px solid #1D9E75;
  border-radius: var(--radius-md);
  padding: 10px 14px;
  min-width: 260px;
  max-width: 340px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  animation: toast-in 0.25s ease;
}
@keyframes toast-in {
  from { opacity: 0; transform: translateX(20px); }
  to   { opacity: 1; transform: translateX(0); }
}
.toast-warn { border-left-color: #BA7517; }
.toast-error { border-left-color: #E24B4A; }

/* -- Print styles -------------------------------------------------------- */
@media print {
  body { overflow: visible !important; height: auto !important; background: #fff !important; }
  #root { height: auto !important; overflow: visible !important; }
  .no-print { display: none !important; }
  .print-only { display: block !important; }
  .leaflet-container { height: 320px !important; }
  .leaflet-control-zoom, .leaflet-control-attribution { display: none !important; }

  header, aside, .tab-bar-row { display: none !important; }

  .print-header {
    display: flex !important;
    align-items: center;
    gap: 12px;
    padding: 12px 0 16px;
    border-bottom: 2px solid #1D9E75;
    margin-bottom: 16px;
  }
  .print-title { font-size: 18px; font-weight: 700; color: #1a1e23; }
  .print-subtitle { font-size: 12px; color: #718096; margin-top: 2px; }
  .print-meta { font-size: 11px; color: #718096; margin-left: auto; text-align: right; }

  main { display: block !important; }
  .stat-cards-row { display: flex !important; gap: 10px; margin-bottom: 14px; }
  .map-event-row { display: block !important; }
  .event-right-panel { width: 100% !important; height: auto !important; border: none !important; }
}

.print-only { display: none; }
"""

# =============================================================================
# useAppStore.js  --  add dateRange + toast state
# =============================================================================
FILES["frontend/src/store/useAppStore.js"] = """import { create } from 'zustand'

export const CATEGORIES = {
  wildfires:           { label: 'Wildfires',           color: '#E8593C' },
  severeStorms:        { label: 'Severe Storms',        color: '#378ADD' },
  floods:              { label: 'Floods',               color: '#1D9E75' },
  drought:             { label: 'Drought',              color: '#BA7517' },
  volcanoes:           { label: 'Volcanoes',            color: '#E24B4A' },
  dustHaze:            { label: 'Dust and Haze',        color: '#888780' },
  earthquakes:         { label: 'Earthquakes',          color: '#7F77DD' },
  landslides:          { label: 'Landslides',           color: '#639922' },
  temperatureExtremes: { label: 'Temperature Extremes', color: '#E85D24' },
  waterColor:          { label: 'Water Color',          color: '#1D6FA5' },
}

export const ALL_CATS = Object.keys(CATEGORIES)

// -- URL read / write helpers --
export function readURLFilters() {
  const p = new URLSearchParams(window.location.search)
  return {
    days:      p.has('days')   ? parseInt(p.get('days'), 10) || 90 : null,
    status:    p.has('status') ? p.get('status') : null,
    cats:      p.has('cats')   ? p.get('cats').split(',').filter((c) => ALL_CATS.includes(c)) : null,
    dateMode:  p.has('mode')   ? p.get('mode') : null,
    startDate: p.has('start')  ? p.get('start') : null,
    endDate:   p.has('end')    ? p.get('end') : null,
  }
}

export function writeURLFilters(state) {
  const p = new URLSearchParams()
  if (state.dateMode === 'range') {
    p.set('mode', 'range')
    if (state.startDate) p.set('start', state.startDate)
    if (state.endDate)   p.set('end',   state.endDate)
  } else {
    if (state.lookbackDays !== 90) p.set('days', String(state.lookbackDays))
  }
  if (state.activeStatus !== 'all') p.set('status', state.activeStatus)
  const catStr = state.activeCategories.join(',')
  if (catStr !== ALL_CATS.join(',')) p.set('cats', catStr)
  const str = p.toString()
  window.history.replaceState({}, '', str ? '?' + str : window.location.pathname)
}

let toastSeq = 0

const useAppStore = create((set) => ({
  activeCategories: ALL_CATS,
  activeStatus:     'all',
  lookbackDays:     90,
  dateMode:         'lookback',   // 'lookback' | 'range'
  startDate:        '',
  endDate:          '',
  selectedEventId:  null,
  lightMode:        true,
  sidebarOpen:      true,
  toasts:           [],

  toggleCategory:   (cat) => set((s) => ({
    activeCategories: s.activeCategories.includes(cat)
      ? s.activeCategories.filter((c) => c !== cat)
      : [...s.activeCategories, cat],
  })),
  setAllCategories: (cats) => set({ activeCategories: cats }),
  setStatus:        (v)    => set({ activeStatus: v }),
  setDays:          (v)    => set({ lookbackDays: v }),
  setDateMode:      (v)    => set({ dateMode: v }),
  setStartDate:     (v)    => set({ startDate: v }),
  setEndDate:       (v)    => set({ endDate: v }),
  selectEvent:      (id)   => set({ selectedEventId: id }),
  toggleLight: () => set((s) => {
    const next = !s.lightMode
    document.documentElement.classList.toggle('light', next)
    return { lightMode: next }
  }),
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),

  addToast: (msg, type) => set((s) => ({
    toasts: [
      ...s.toasts,
      { id: String(++toastSeq), msg, type: type || 'info', ts: Date.now() },
    ],
  })),
  removeToast: (id) => set((s) => ({
    toasts: s.toasts.filter((t) => t.id !== id),
  })),
}))

if (typeof document !== 'undefined') {
  document.documentElement.classList.add('light')
}

export default useAppStore
"""

# =============================================================================
# src/api/queries.js  --  date range support in queryKey + fetch
# =============================================================================
FILES["frontend/src/api/queries.js"] = """import { useQuery } from '@tanstack/react-query'
import useAppStore from '../store/useAppStore.js'

const EONET_BASE = 'https://eonet.gsfc.nasa.gov/api/v3'
const EA_BBOX    = '21.8,22.0,51.4,-11.7'
const USE_DIRECT = import.meta.env.VITE_EONET_DIRECT === 'true'
const API_BASE   = import.meta.env.VITE_API_BASE_URL || ''

function convertFeature(feat) {
  const props = feat.properties || {}
  const geom  = feat.geometry   || {}
  const cats  = props.categories || []
  const srcs  = props.sources    || []
  let coords  = null
  if (geom.type === 'Point') {
    coords = geom.coordinates
  } else if (geom.type === 'Polygon' && geom.coordinates?.[0]?.length) {
    const ring = geom.coordinates[0]
    const lons = ring.map((c) => c[0])
    const lats = ring.map((c) => c[1])
    coords = [
      (Math.min(...lons) + Math.max(...lons)) / 2,
      (Math.min(...lats) + Math.max(...lats)) / 2,
    ]
  }
  return {
    id:          props.id          || '',
    title:       props.title       || '',
    description: props.description || null,
    link:        props.link        || '',
    category:    cats[0]?.id       || 'unknown',
    categories:  cats,
    status:      props.closed ? 'closed' : 'open',
    closed:      props.closed || null,
    latest_date: props.date || (props.geometryDates || [])[0] || '',
    coords,
    sources: srcs,
    magnitude: props.magnitudeValue != null
      ? { value: props.magnitudeValue, unit: props.magnitudeUnit }
      : null,
  }
}

async function fetchDirect(opts) {
  const params = new URLSearchParams({ bbox: EA_BBOX, limit: 500, status: opts.status || 'all' })
  if (opts.startDate && opts.endDate) {
    params.set('start', opts.startDate)
    params.set('end',   opts.endDate)
  } else {
    params.set('days', String(opts.days || 90))
  }
  const res  = await fetch(EONET_BASE + '/events/geojson?' + params)
  if (!res.ok) throw new Error('EONET ' + res.status)
  const data = await res.json()
  return (data.features || []).map(convertFeature)
}

async function fetchViaBackend(opts) {
  const params = new URLSearchParams({ status: opts.status || 'all' })
  if (opts.startDate && opts.endDate) {
    params.set('start', opts.startDate)
    params.set('end',   opts.endDate)
  } else {
    params.set('days', String(opts.days || 90))
  }
  const res  = await fetch(API_BASE + '/events?' + params)
  if (!res.ok) throw new Error('Backend ' + res.status)
  const data = await res.json()
  return data.events || []
}

async function fetchEvents(opts) {
  if (USE_DIRECT) return fetchDirect(opts)
  try {
    return await fetchViaBackend(opts)
  } catch {
    console.info('[NET-EA] Backend offline -- fetching EONET directly')
    return fetchDirect(opts)
  }
}

export function useEvents() {
  const { activeStatus, lookbackDays, dateMode, startDate, endDate } = useAppStore()
  const opts = { status: activeStatus, days: lookbackDays }
  if (dateMode === 'range' && startDate && endDate) {
    opts.startDate = startDate
    opts.endDate   = endDate
  }
  return useQuery({
    queryKey:        ['events', activeStatus, lookbackDays, dateMode, startDate, endDate],
    queryFn:         () => fetchEvents(opts),
    staleTime:       10 * 60 * 1000,
    refetchInterval: 15 * 60 * 1000,
    retry:           2,
  })
}

export function useSummary() {
  const { data: events = [], isLoading } = useEvents()
  const open        = events.filter((e) => e.status === 'open').length
  const closed      = events.filter((e) => e.status === 'closed').length
  const by_category = {}
  events.forEach((e) => { by_category[e.category] = (by_category[e.category] || 0) + 1 })
  return { data: { total: events.length, open, closed, by_category }, isLoading }
}

export function useCacheStatus() {
  return useQuery({
    queryKey:        ['cache_status'],
    queryFn: async () => {
      if (USE_DIRECT) return { mode: 'direct', note: 'NASA EONET direct fetch' }
      try {
        const res = await fetch(API_BASE + '/status')
        if (!res.ok) return { mode: 'direct', note: 'Backend offline' }
        return { ...(await res.json()), mode: 'backend' }
      } catch { return { mode: 'direct', note: 'Backend offline' } }
    },
    refetchInterval: 60 * 1000,
    staleTime:       30 * 1000,
  })
}
"""

# =============================================================================
# SkeletonLoader.jsx  --  NEW  reusable pulsing placeholder
# =============================================================================
FILES["frontend/src/components/SkeletonLoader.jsx"] = """import React from 'react'

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
"""

# =============================================================================
# ToastContainer.jsx  --  NEW  toast notification system
# =============================================================================
FILES["frontend/src/components/ToastContainer.jsx"] = """import React, { useEffect } from 'react'
import useAppStore from '../store/useAppStore.js'

function Toast({ toast }) {
  const removeToast = useAppStore((s) => s.removeToast)
  useEffect(() => {
    const t = setTimeout(() => removeToast(toast.id), 5000)
    return () => clearTimeout(t)
  }, [toast.id, removeToast])

  const cls = toast.type === 'warn' ? 'toast toast-warn'
            : toast.type === 'error' ? 'toast toast-error'
            : 'toast'

  return (
    <div className={cls}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)',
                        marginBottom: 2 }}>
            {toast.type === 'warn' ? 'Warning' : 'New events detected'}
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            {toast.msg}
          </div>
        </div>
        <button
          onClick={() => removeToast(toast.id)}
          style={{ background: 'none', border: 'none', cursor: 'pointer',
                   color: 'var(--text-muted)', fontSize: 16, lineHeight: 1,
                   padding: '0 2px', flexShrink: 0 }}
        >
          x
        </button>
      </div>
    </div>
  )
}

export default function ToastContainer() {
  const toasts = useAppStore((s) => s.toasts)
  if (!toasts.length) return null
  return (
    <div className="toast-container no-print">
      {toasts.map((t) => <Toast key={t.id} toast={t} />)}
    </div>
  )
}
"""

# =============================================================================
# PrintButton.jsx  --  NEW  PDF / print export
# =============================================================================
FILES["frontend/src/components/PrintButton.jsx"] = """import React from 'react'
import useAppStore from '../store/useAppStore.js'
import { useEvents } from '../api/queries.js'

export default function PrintButton() {
  const { activeStatus, lookbackDays, dateMode, startDate, endDate, activeCategories } = useAppStore()
  const { data: events = [] } = useEvents()

  function handlePrint() {
    const el = document.getElementById('print-header-inject')
    if (el) {
      const dateStr  = dateMode === 'range'
        ? startDate + ' to ' + endDate
        : 'Last ' + lookbackDays + ' days'
      const cats     = activeCategories.length === 10
        ? 'All categories'
        : activeCategories.join(', ')
      el.innerHTML =
        '<div class="print-title">NET-EA -- Natural Event Tracker for East Africa</div>' +
        '<div class="print-subtitle">Yonas M. | Y.Mersha@cgiar.org | Climate Modelling and AI Expert</div>' +
        '<div class="print-meta">' +
          'Generated: ' + new Date().toLocaleString() + '<br/>' +
          'Period: ' + dateStr + '<br/>' +
          'Status: ' + activeStatus + '<br/>' +
          'Events: ' + events.length + '<br/>' +
          'Categories: ' + cats +
        '</div>'
    }
    window.print()
  }

  return (
    <button
      onClick={handlePrint}
      title="Print / Export PDF"
      className="no-print"
      style={{
        display: 'flex', alignItems: 'center', gap: 5,
        fontSize: 12, padding: '4px 10px', borderRadius: 6,
        border: '1px solid var(--border-primary)',
        background: 'transparent', color: 'var(--text-secondary)',
        cursor: 'pointer',
      }}
    >
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
           stroke="currentColor" strokeWidth="2" strokeLinecap="round"
           strokeLinejoin="round">
        <polyline points="6 9 6 2 18 2 18 9"/>
        <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/>
        <rect x="6" y="14" width="12" height="8"/>
      </svg>
      Export PDF
    </button>
  )
}
"""

# =============================================================================
# MapPanel.jsx  --  clustering + GIBS satellite + shareable popup link
# =============================================================================
FILES["frontend/src/components/MapPanel.jsx"] = """import React, { useEffect, useState, useCallback } from 'react'
import {
  MapContainer, TileLayer, WMSTileLayer, CircleMarker,
  Popup, GeoJSON, Rectangle, useMap,
} from 'react-leaflet'
import MarkerClusterGroup from 'react-leaflet-cluster'
import 'leaflet/dist/leaflet.css'
import useAppStore, { CATEGORIES } from '../store/useAppStore.js'
import { useEvents } from '../api/queries.js'

const ICPAC_CENTER   = [6.5, 38.0]
const MAX_BOUNDS     = [[-16.0, 18.0], [26.0, 56.0]]
const REGION_BOUNDS  = [[-12.0, 22.0], [23.0, 52.0]]
const ICPAC_ISO2     = ['DJ','ER','ET','KE','RW','SO','SS','SD','TZ','UG','BI']
const GEO_BASE       = 'https://raw.githubusercontent.com/johan/world.geo.json/master/countries'

const TILE_LIGHT  = 'https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png'
const TILE_DARK   = 'https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png'
const TILE_LABELS = 'https://{s}.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}{r}.png'
const TILE_LABELS_LIGHT = 'https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}{r}.png'
const ATTR        = '(c) OpenStreetMap contributors, (c) CARTO | NASA EONET v3'
const GIBS_URL    = 'https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi'

const GIBS_LAYERS = [
  { id: 'MODIS_Terra_CorrectedReflectance_TrueColor', label: 'True colour (Terra)' },
  { id: 'VIIRS_SNPP_CorrectedReflectance_TrueColor',  label: 'True colour (VIIRS)' },
  { id: 'FIRMS_VIIRS_375m_FireAndThermalAnomalies',   label: 'Fire detections' },
  { id: 'MODIS_Terra_Chlorophyll_A',                  label: 'Chlorophyll' },
]

function todayStr() {
  return new Date().toISOString().slice(0, 10)
}

function getCatColor(cat) {
  return (CATEGORIES[cat] || {}).color || '#484f58'
}

function worldviewURL(ev) {
  if (!ev.coords) return null
  const lon  = ev.coords[0]
  const lat  = ev.coords[1]
  const pad  = 3
  const date = (ev.latest_date || todayStr()).slice(0, 10)
  const bbox = (lon - pad) + ',' + (lat - pad) + ',' + (lon + pad) + ',' + (lat + pad)
  return 'https://worldview.earthdata.nasa.gov/?v=' + bbox + '&t=' + date
}

function FitRegion() {
  const map = useMap()
  useEffect(() => { map.fitBounds(REGION_BOUNDS, { padding: [10, 10] }) }, [map])
  return null
}

function FlyTo({ events, selectedId }) {
  const map = useMap()
  useEffect(() => {
    if (!selectedId) return
    const ev = events.find((e) => e.id === selectedId)
    if (ev && ev.coords) map.flyTo([ev.coords[1], ev.coords[0]], 7, { duration: 1.2 })
  }, [selectedId, events, map])
  return null
}

function OutsideMask() {
  const strips = [
    [[-90, -180], [90, 22.0]],
    [[-90, 52.0], [90, 180]],
    [[23.0, 22.0], [90, 52.0]],
    [[-90, 22.0], [-12.0, 52.0]],
  ]
  return strips.map((b, i) => (
    <Rectangle key={i} bounds={b}
      pathOptions={{ color: 'transparent', fillColor: '#000', fillOpacity: 0.4, weight: 0 }} />
  ))
}

function CountriesLayer({ geo, lightMode }) {
  const style = useCallback(() => ({
    color:       lightMode ? '#94a3b8' : '#4a5568',
    weight:      1.2,
    fillColor:   lightMode ? '#e2e8f0' : '#1e293b',
    fillOpacity: 0.12,
  }), [lightMode])

  if (!geo) return null
  return <GeoJSON key={'c-' + (lightMode ? 'l' : 'd')} data={geo} style={style} />
}

function LegendRow({ color, label, dash }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
      <svg width="16" height="12" viewBox="0 0 16 12">
        <circle cx="8" cy="6" r="5" fill={color} fillOpacity={dash ? 0.4 : 0.85}
          stroke={color} strokeWidth={1.5} strokeDasharray={dash ? '3 2' : null} />
      </svg>
      <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{label}</span>
    </div>
  )
}

function PopupRow({ label, value }) {
  return (
    <tr>
      <td style={{ color: 'var(--text-muted)', paddingRight: 10, paddingBottom: 3,
                   whiteSpace: 'nowrap', fontSize: 12 }}>{label}</td>
      <td style={{ color: 'var(--text-secondary)', paddingBottom: 3, fontSize: 12 }}>{value}</td>
    </tr>
  )
}

export default function MapPanel({ height }) {
  const { activeCategories, activeStatus, selectedEventId, selectEvent, lightMode } = useAppStore()
  const { data: rawEvents = [], isLoading } = useEvents()

  const [geo,         setGeo]       = useState(null)
  const [satOn,       setSatOn]     = useState(false)
  const [satLayer,    setSatLayer]  = useState(GIBS_LAYERS[0].id)
  const [satDate,     setSatDate]   = useState(todayStr)
  const [satOpen,     setSatOpen]   = useState(false)

  useEffect(() => {
    Promise.allSettled(
      ICPAC_ISO2.map((iso) =>
        fetch(GEO_BASE + '/' + iso + '.geo.json', { signal: AbortSignal.timeout(7000) })
          .then((r) => (r.ok ? r.json() : null))
          .catch(() => null)
      )
    ).then((results) => {
      const features = results
        .flatMap((r, i) => {
          if (r.status !== 'fulfilled' || !r.value) return []
          const d   = r.value
          const raw = d.type === 'FeatureCollection' ? d.features : [d]
          return raw.map((f) => ({ ...f, properties: { ...(f.properties || {}), iso2: ICPAC_ISO2[i] } }))
        })
      if (features.length) setGeo({ type: 'FeatureCollection', features })
    })
  }, [])

  const events = rawEvents.filter((ev) => {
    if (!activeCategories.includes(ev.category)) return false
    if (activeStatus === 'open'   && ev.status !== 'open')   return false
    if (activeStatus === 'closed' && ev.status !== 'closed') return false
    return ev.coords != null
  })

  return (
    <div style={{ flex: 1, position: 'relative', background: '#e8f0e0',
                  minHeight: height || 340 }}>
      {isLoading && (
        <div style={{ position: 'absolute', inset: 0, zIndex: 500,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      background: 'rgba(246,248,250,0.7)', fontSize: 13,
                      color: 'var(--text-secondary)' }}>
          Loading events...
        </div>
      )}

      {/* Top-left badge */}
      <div style={{ position: 'absolute', top: 10, left: 10, zIndex: 400,
                    background: 'rgba(255,255,255,0.88)',
                    border: '1px solid var(--border-primary)', borderRadius: 6,
                    padding: '4px 10px', fontSize: 11, fontWeight: 600,
                    color: '#1D9E75', letterSpacing: '0.05em',
                    pointerEvents: 'none' }}>
        Greater Horn of Africa
      </div>

      {/* Top-right toolbar */}
      <div style={{ position: 'absolute', top: 10, right: 10, zIndex: 400,
                    display: 'flex', gap: 6, alignItems: 'flex-start' }}>

        {/* Satellite toggle */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setSatOpen((v) => !v)}
            style={{
              fontSize: 11, padding: '4px 10px', borderRadius: 6,
              border: '1px solid',
              borderColor: satOn ? '#378ADD' : 'var(--border-primary)',
              background:  satOn ? '#378ADD22' : 'rgba(255,255,255,0.88)',
              color:        satOn ? '#185FA5'   : 'var(--text-secondary)',
              cursor: 'pointer', fontWeight: satOn ? 600 : 400,
            }}
          >
            Satellite
          </button>

          {satOpen && (
            <div style={{
              position: 'absolute', top: 32, right: 0, zIndex: 600,
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-primary)',
              borderRadius: 8, padding: '10px 12px',
              minWidth: 240, boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
            }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)',
                            textTransform: 'uppercase', letterSpacing: '0.06em',
                            marginBottom: 8 }}>
                NASA GIBS layer
              </div>
              {GIBS_LAYERS.map((gl) => (
                <label key={gl.id} style={{ display: 'flex', alignItems: 'center',
                                            gap: 7, marginBottom: 6, cursor: 'pointer' }}>
                  <input
                    type="radio"
                    name="gibs"
                    checked={satLayer === gl.id}
                    onChange={() => { setSatLayer(gl.id); setSatOn(true) }}
                  />
                  <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                    {gl.label}
                  </span>
                </label>
              ))}
              <div style={{ marginTop: 10, borderTop: '1px solid var(--border-muted)',
                            paddingTop: 8 }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>
                  Date
                </div>
                <input
                  type="date"
                  value={satDate}
                  max={todayStr()}
                  onChange={(e) => setSatDate(e.target.value)}
                  style={{ width: '100%', fontSize: 12, padding: '4px 6px',
                           border: '1px solid var(--border-primary)',
                           borderRadius: 4, background: 'var(--bg-elevated)',
                           color: 'var(--text-primary)' }}
                />
              </div>
              <div style={{ marginTop: 10, display: 'flex', gap: 6 }}>
                <button
                  onClick={() => { setSatOn(true); setSatOpen(false) }}
                  style={{ flex: 1, padding: '5px', borderRadius: 5, fontSize: 11,
                           border: 'none', background: '#378ADD', color: '#fff',
                           cursor: 'pointer', fontWeight: 500 }}
                >
                  Apply
                </button>
                <button
                  onClick={() => { setSatOn(false); setSatOpen(false) }}
                  style={{ flex: 1, padding: '5px', borderRadius: 5, fontSize: 11,
                           border: '1px solid var(--border-primary)',
                           background: 'transparent', color: 'var(--text-secondary)',
                           cursor: 'pointer' }}
                >
                  Off
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Event count */}
        <div style={{ background: 'rgba(255,255,255,0.88)',
                      border: '1px solid var(--border-primary)', borderRadius: 6,
                      padding: '4px 10px', fontSize: 12, color: 'var(--text-secondary)',
                      pointerEvents: 'none' }}>
          {events.length} event{events.length !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Legend */}
      <div style={{ position: 'absolute', bottom: 30, left: 10, zIndex: 400,
                    background: 'rgba(255,255,255,0.88)',
                    border: '1px solid var(--border-primary)',
                    borderRadius: 6, padding: '8px 10px', pointerEvents: 'none' }}>
        <div style={{ fontSize: 10, color: 'var(--text-muted)',
                      textTransform: 'uppercase', letterSpacing: '0.06em',
                      marginBottom: 4, fontWeight: 600 }}>Legend</div>
        <LegendRow color="#1D9E75" label="Open"   dash={false} />
        <LegendRow color="#6e7681" label="Closed" dash={true}  />
      </div>

      <MapContainer
        center={ICPAC_CENTER} zoom={5} minZoom={4} maxZoom={10}
        maxBounds={MAX_BOUNDS} maxBoundsViscosity={0.85}
        style={{ width: '100%', height: '100%' }}
      >
        {lightMode ? (
          <>
            <TileLayer url={TILE_LIGHT}       attribution={ATTR} />
            <TileLayer url={TILE_LABELS_LIGHT} />
          </>
        ) : (
          <>
            <TileLayer url={TILE_DARK}   attribution={ATTR} />
            <TileLayer url={TILE_LABELS} />
          </>
        )}

        {satOn && (
          <WMSTileLayer
            url={GIBS_URL}
            layers={satLayer}
            format="image/jpeg"
            version="1.1.1"
            time={satDate}
            opacity={0.7}
            transparent={false}
          />
        )}

        <OutsideMask />
        <CountriesLayer geo={geo} lightMode={lightMode} />
        <FitRegion />
        <FlyTo events={events} selectedId={selectedEventId} />

        <MarkerClusterGroup
          chunkedLoading
          maxClusterRadius={60}
          showCoverageOnHover={false}
        >
          {events.map((ev) => {
            const color  = getCatColor(ev.category)
            const isOpen = ev.status === 'open'
            const isSel  = ev.id === selectedEventId
            const cat    = CATEGORIES[ev.category] || {}
            const wvLink = worldviewURL(ev)

            return (
              <CircleMarker
                key={ev.id}
                center={[ev.coords[1], ev.coords[0]]}
                radius={isSel ? 13 : isOpen ? 9 : 7}
                pathOptions={{
                  color:       isSel ? '#1a1e23' : color,
                  fillColor:   color,
                  fillOpacity: isOpen ? 0.88 : 0.42,
                  weight:      isSel ? 2.5 : isOpen ? 1.5 : 1,
                  dashArray:   isOpen ? null : '4 3',
                }}
                eventHandlers={{ click: () => selectEvent(ev.id) }}
              >
                <Popup maxWidth={290}>
                  <div style={{ fontFamily: 'inherit', minWidth: 230 }}>
                    <div style={{ marginBottom: 8, display: 'flex', gap: 6, flexWrap: 'wrap',
                                  alignItems: 'center' }}>
                      <span style={{ fontSize: 11, fontWeight: 500, padding: '2px 8px',
                                     borderRadius: 100, background: color + '33', color: color,
                                     border: '1px solid ' + color + '55' }}>
                        {cat.label || ev.category}
                      </span>
                      <span style={{ fontSize: 11, fontWeight: 600,
                                     color: isOpen ? '#1D9E75' : '#6e7681' }}>
                        {isOpen ? 'OPEN' : 'CLOSED'}
                      </span>
                    </div>
                    <p style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-primary)',
                                lineHeight: 1.4, marginBottom: 8 }}>
                      {ev.title}
                    </p>
                    <table style={{ borderCollapse: 'collapse', width: '100%' }}>
                      <tbody>
                        <PopupRow label="Date"   value={(ev.latest_date || '--').slice(0, 10)} />
                        {ev.closed && (
                          <PopupRow label="Closed" value={ev.closed.slice(0, 10)} />
                        )}
                        {ev.magnitude && (
                          <PopupRow label="Magnitude"
                            value={ev.magnitude.value + ' ' + (ev.magnitude.unit || '')} />
                        )}
                        <PopupRow label="Coords"
                          value={ev.coords[1].toFixed(2) + ', ' + ev.coords[0].toFixed(2)} />
                      </tbody>
                    </table>
                    <div style={{ marginTop: 10, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                      {ev.sources && ev.sources[0] && (
                        <a href={ev.sources[0].url} target="_blank" rel="noreferrer"
                           style={{ fontSize: 11, color: '#378ADD' }}>
                          {ev.sources[0].id}
                        </a>
                      )}
                      {wvLink && (
                        <a href={wvLink} target="_blank" rel="noreferrer"
                           style={{ fontSize: 11, color: '#1D9E75', fontWeight: 500 }}>
                          View satellite image
                        </a>
                      )}
                      {ev.link && (
                        <a href={ev.link} target="_blank" rel="noreferrer"
                           style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                          EONET page
                        </a>
                      )}
                    </div>
                  </div>
                </Popup>
              </CircleMarker>
            )
          })}
        </MarkerClusterGroup>
      </MapContainer>
    </div>
  )
}
"""

# =============================================================================
# FilterSidebar.jsx  --  add date range picker mode
# =============================================================================
FILES["frontend/src/components/FilterSidebar.jsx"] = """import React from 'react'
import useAppStore, { CATEGORIES, ALL_CATS } from '../store/useAppStore.js'
import { useSummary } from '../api/queries.js'

const STATUS_OPTS = [
  { value: 'all',    label: 'All events' },
  { value: 'open',   label: 'Open only'  },
  { value: 'closed', label: 'Closed only' },
]

const DAY_OPTS = [7, 14, 30, 60, 90, 180, 365]

function Section({ label, children }) {
  return (
    <div style={{ marginBottom: 18 }}>
      <p style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.08em',
                  textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 8 }}>
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
        padding: '4px 10px', borderRadius: 100, fontSize: 12, marginBottom: 4,
        border: '1px solid',
        borderColor: active ? '#378ADD' : 'var(--border-primary)',
        background:  active ? '#378ADD' : 'transparent',
        color:       active ? '#fff'    : 'var(--text-secondary)',
        cursor: 'pointer',
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

export default function FilterSidebar() {
  const {
    activeCategories, toggleCategory, setAllCategories,
    activeStatus,     setStatus,
    lookbackDays,     setDays,
    dateMode,         setDateMode,
    startDate,        setStartDate,
    endDate,          setEndDate,
  } = useAppStore()

  const { data: summary } = useSummary()
  const byCat = summary?.by_category || {}

  const allOn  = activeCategories.length === ALL_CATS.length
  const noneOn = activeCategories.length === 0

  return (
    <aside className="no-print" style={{
      width: 'var(--sidebar-w)',
      background: 'var(--bg-surface)',
      borderRight: '1px solid var(--border-primary)',
      display: 'flex', flexDirection: 'column',
      overflow: 'hidden', flexShrink: 0,
    }}>
      <div style={{ overflowY: 'auto', flex: 1, padding: '14px 12px' }}>

        {/* -- Status -- */}
        <Section label="Status">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {STATUS_OPTS.map((o) => (
              <Pill key={o.value} active={activeStatus === o.value}
                    onClick={() => setStatus(o.value)}>
                {o.label}
              </Pill>
            ))}
          </div>
        </Section>

        {/* -- Time period -- */}
        <Section label="Time period">
          <div style={{ display: 'flex', gap: 6, marginBottom: 10 }}>
            <button style={smallBtn(dateMode === 'lookback')} onClick={() => setDateMode('lookback')}>
              Lookback
            </button>
            <button style={smallBtn(dateMode === 'range')} onClick={() => setDateMode('range')}>
              Date range
            </button>
          </div>

          {dateMode === 'lookback' && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
              {DAY_OPTS.map((d) => (
                <Pill key={d} active={lookbackDays === d} onClick={() => setDays(d)}>
                  {d + 'd'}
                </Pill>
              ))}
            </div>
          )}

          {dateMode === 'range' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 3 }}>
                  Start date
                </div>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  style={{ width: '100%', fontSize: 12, padding: '5px 8px',
                           border: '1px solid var(--border-primary)', borderRadius: 5,
                           background: 'var(--bg-elevated)', color: 'var(--text-primary)' }}
                />
              </div>
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 3 }}>
                  End date
                </div>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  style={{ width: '100%', fontSize: 12, padding: '5px 8px',
                           border: '1px solid var(--border-primary)', borderRadius: 5,
                           background: 'var(--bg-elevated)', color: 'var(--text-primary)' }}
                />
              </div>
            </div>
          )}
        </Section>

        {/* -- Categories -- */}
        <Section label="Event categories">
          <div style={{ display: 'flex', gap: 6, marginBottom: 10 }}>
            <button style={smallBtn(allOn)}  onClick={() => setAllCategories(ALL_CATS)}>All</button>
            <button style={smallBtn(noneOn)} onClick={() => setAllCategories([])}>None</button>
          </div>

          {ALL_CATS.map((cat) => {
            const meta   = CATEGORIES[cat]
            const active = activeCategories.includes(cat)
            const count  = byCat[cat] || 0
            return (
              <button
                key={cat}
                onClick={() => toggleCategory(cat)}
                style={{
                  width: '100%', display: 'flex', alignItems: 'center', gap: 8,
                  padding: '6px 8px', marginBottom: 3,
                  borderRadius: 'var(--radius-sm)', cursor: 'pointer',
                  border: '1px solid',
                  borderColor: active ? meta.color + '55' : 'var(--border-muted)',
                  background:  active ? meta.color + '18' : 'transparent',
                  transition: 'all 0.12s', textAlign: 'left',
                }}
              >
                <span style={{
                  width: 10, height: 10, borderRadius: '50%', flexShrink: 0,
                  background: active ? meta.color : 'var(--text-faint)',
                }} />
                <span style={{ flex: 1, fontSize: 13,
                               color: active ? 'var(--text-primary)' : 'var(--text-secondary)',
                               fontWeight: active ? 500 : 400 }}>
                  {meta.label}
                </span>
                {count > 0 && (
                  <span style={{ fontSize: 11, padding: '1px 5px', borderRadius: 100,
                                 background: active ? meta.color + '33' : 'var(--bg-elevated)',
                                 color: active ? meta.color : 'var(--text-muted)' }}>
                    {count}
                  </span>
                )}
              </button>
            )
          })}
        </Section>

        <Section label="Data source">
          <p style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.6 }}>
            NASA EONET v3 -- Greater Horn of Africa (21.8-51.4 E, 11.7 S - 22.0 N).
            Auto-refreshed every 15 min.
          </p>
          <a href="https://eonet.gsfc.nasa.gov/docs/v3" target="_blank" rel="noreferrer"
             style={{ fontSize: 11, color: 'var(--accent-blue)', display: 'block', marginTop: 6 }}>
            EONET API docs
          </a>
        </Section>
      </div>
    </aside>
  )
}
"""

# =============================================================================
# StatCards.jsx  --  skeleton during loading
# =============================================================================
FILES["frontend/src/components/StatCards.jsx"] = """import React from 'react'
import { useSummary } from '../api/queries.js'
import { CATEGORIES } from '../store/useAppStore.js'
import { SkeletonRect } from './SkeletonLoader.jsx'

function getCatColor(cat) { return (CATEGORIES[cat] || {}).color || '#484f58' }

export default function StatCards() {
  const { data: s, isLoading } = useSummary()

  const total    = s?.total  ?? 0
  const open     = s?.open   ?? 0
  const closed   = s?.closed ?? 0
  const byCat    = s?.by_category || {}
  const openRate = total > 0 ? Math.round((open / total) * 100) : 0
  const topEntry = Object.entries(byCat).sort(([,a],[,b]) => b - a)[0]
  const topCatId = topEntry ? topEntry[0] : null
  const topCatN  = topEntry ? topEntry[1] : 0
  const topLabel = topCatId ? ((CATEGORIES[topCatId] || {}).label || topCatId) : '--'
  const topColor = topCatId ? getCatColor(topCatId) : 'var(--text-muted)'

  const cards = [
    { value: total,  label: 'Total events', sub: 'Greater Horn of Africa', color: '#378ADD' },
    { value: open,   label: 'Open',         sub: openRate + '% of total',  color: '#1D9E75', bar: openRate, barColor: '#1D9E75' },
    { value: closed, label: 'Closed',       sub: (100 - openRate) + '% resolved', color: 'var(--text-muted)' },
    { value: topCatN, label: 'Top category', sub: topLabel, color: topColor },
  ]

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)',
                  gap: 10, padding: '10px 14px 0', flexShrink: 0 }}>
      {isLoading ? (
        Array.from({ length: 4 }).map((_, i) => (
          <div key={i} style={{ background: 'var(--bg-surface)',
                                border: '1px solid var(--border-primary)',
                                borderRadius: 'var(--radius-md)', padding: '10px 14px' }}>
            <SkeletonRect h={26} w="50%" style={{ marginBottom: 6 }} />
            <SkeletonRect h={13} w="65%" />
          </div>
        ))
      ) : (
        cards.map((c, i) => (
          <div key={i} style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-primary)',
            borderTop: '2px solid ' + c.color,
            borderRadius: 'var(--radius-md)', padding: '10px 14px',
          }}>
            <div style={{ fontSize: 24, fontWeight: 600, color: c.color, lineHeight: 1,
                          marginBottom: 4 }}>
              {c.value}
            </div>
            <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)',
                          marginBottom: 2 }}>
              {c.label}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{c.sub}</div>
            {c.bar != null && (
              <div style={{ marginTop: 8, height: 3, background: 'var(--bg-elevated)',
                            borderRadius: 2 }}>
                <div style={{ height: '100%', borderRadius: 2, width: c.bar + '%',
                              background: c.barColor, transition: 'width 0.5s' }} />
              </div>
            )}
          </div>
        ))
      )}
    </div>
  )
}
"""

# =============================================================================
# App.jsx  --  URL sync + toast wiring + ToastContainer + PrintButton
# =============================================================================
FILES["frontend/src/App.jsx"] = """import React, { useState, useEffect, useRef } from 'react'
import TopNav         from './components/TopNav.jsx'
import FilterSidebar  from './components/FilterSidebar.jsx'
import StatCards      from './components/StatCards.jsx'
import MapPanel       from './components/MapPanel.jsx'
import EventList      from './components/EventList.jsx'
import AnalyticsPanel from './components/AnalyticsPanel.jsx'
import AboutPanel     from './components/AboutPanel.jsx'
import ToastContainer from './components/ToastContainer.jsx'
import PrintButton    from './components/PrintButton.jsx'
import useAppStore, { ALL_CATS, readURLFilters, writeURLFilters } from './store/useAppStore.js'
import { useEvents }  from './api/queries.js'

const TABS = [
  { id: 'map',       label: 'Map view'  },
  { id: 'analytics', label: 'Analytics' },
  { id: 'about',     label: 'About'     },
]

function EventWatcher() {
  const { data: events } = useEvents()
  const addToast = useAppStore((s) => s.addToast)
  const prevIdsRef = useRef(null)

  useEffect(() => {
    if (!events || events.length === 0) return
    const currentIds = new Set(events.map((e) => e.id))
    if (prevIdsRef.current !== null && prevIdsRef.current.size > 0) {
      const newEvs = events.filter((e) => !prevIdsRef.current.has(e.id))
      if (newEvs.length > 0) {
        const names = newEvs.slice(0, 2).map((e) => e.title).join('; ')
        addToast(
          newEvs.length + ' new event' + (newEvs.length > 1 ? 's' : '') + ': ' + names,
          'info'
        )
      }
    }
    prevIdsRef.current = currentIds
  }, [events, addToast])

  return null
}

export default function App() {
  const {
    sidebarOpen, activeCategories, activeStatus,
    lookbackDays, dateMode, startDate, endDate,
    setStatus, setDays, setAllCategories, setDateMode, setStartDate, setEndDate,
  } = useAppStore()

  const [activeTab, setActiveTab] = useState('map')

  // -- Read URL filters on mount --
  useEffect(() => {
    const f = readURLFilters()
    if (f.status)    setStatus(f.status)
    if (f.days)      setDays(f.days)
    if (f.cats && f.cats.length > 0) setAllCategories(f.cats)
    if (f.dateMode)  setDateMode(f.dateMode)
    if (f.startDate) setStartDate(f.startDate)
    if (f.endDate)   setEndDate(f.endDate)
  }, [])

  // -- Write URL whenever filters change --
  useEffect(() => {
    writeURLFilters({
      activeCategories, activeStatus, lookbackDays,
      dateMode, startDate, endDate,
    })
  }, [activeCategories, activeStatus, lookbackDays, dateMode, startDate, endDate])

  const showSidebar   = sidebarOpen && activeTab !== 'about'
  const showStatCards = activeTab !== 'about'

  return (
    <div style={{ display: 'flex', flexDirection: 'column',
                  height: '100vh', overflow: 'hidden' }}>
      <ToastContainer />
      <EventWatcher />

      {/* Print header -- hidden on screen, visible on print */}
      <div id="print-header-inject" className="print-only print-header" />

      <TopNav />

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {showSidebar && <FilterSidebar />}

        <main style={{ flex: 1, display: 'flex', flexDirection: 'column',
                       overflow: 'hidden', minWidth: 0 }}>

          {showStatCards && <StatCards />}

          {/* Tab bar */}
          <div className="tab-bar-row no-print" style={{
            display: 'flex', alignItems: 'center', gap: 2,
            padding: '8px 14px 0',
            borderBottom: '1px solid var(--border-primary)',
            background: 'var(--bg-base)', flexShrink: 0,
          }}>
            {TABS.map((tab) => {
              const active = activeTab === tab.id
              return (
                <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={{
                  padding: '6px 14px', fontSize: 13, fontWeight: active ? 600 : 400,
                  color:  active ? 'var(--text-primary)' : 'var(--text-secondary)',
                  background: 'transparent', border: 'none',
                  borderBottom: '2px solid',
                  borderBottomColor: active ? '#1D9E75' : 'transparent',
                  cursor: 'pointer', marginBottom: -1,
                }}>
                  {tab.label}
                </button>
              )
            })}
            <div style={{ flex: 1 }} />

            {/* Share URL button */}
            <button
              onClick={() => {
                navigator.clipboard.writeText(window.location.href)
                  .then(() => useAppStore.getState().addToast('Link copied to clipboard', 'info'))
                  .catch(() => {})
              }}
              className="no-print"
              title="Copy shareable link"
              style={{
                fontSize: 12, padding: '4px 10px', borderRadius: 6,
                border: '1px solid var(--border-primary)',
                background: 'transparent', color: 'var(--text-secondary)',
                cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 5,
              }}
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" strokeWidth="2" strokeLinecap="round"
                   strokeLinejoin="round">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
              </svg>
              Share
            </button>

            <PrintButton />
          </div>

          {activeTab === 'map' && (
            <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
              <MapPanel />
              <EventList />
            </div>
          )}

          {activeTab === 'analytics' && <AnalyticsPanel />}
          {activeTab === 'about'     && <AboutPanel />}
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
    hdr(f"Adding all Tier 1 features to NET-EA in: {root}")
    fe = root / "frontend"
    created = updated = 0

    for rel, content in FILES.items():
        if rel.startswith("frontend/"):
            target = root / rel
        else:
            target = fe / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        existed = target.exists()
        target.write_text(content, encoding="utf-8")
        (ow if existed else ok)(("update  " if existed else "create  ") + rel)
        if existed: updated += 1
        else: created += 1

    hdr("Done")
    print(f"  Files created : {created}")
    print(f"  Files updated : {updated}")
    print()
    print("  7 Tier 1 features added:")
    print("  [1] Marker clustering  -- react-leaflet-cluster groups nearby events")
    print("  [2] Skeleton loaders   -- pulsing placeholders while data fetches")
    print("  [3] NASA satellite     -- GIBS WMTS layers (true colour, fire, chlorophyll)")
    print("  [4] Date range picker  -- custom start/end dates in sidebar")
    print("  [5] Toast alerts       -- popup when refresh finds new events")
    print("  [6] Shareable URLs     -- filters encoded in URL, Share button copies link")
    print("  [7] PDF export         -- Export PDF button, print-optimised layout")
    print()
    print("  IMPORTANT -- run npm install to pull in react-leaflet-cluster:")
    print("    cd frontend")
    print("    npm install")
    print("    npm run dev")
    print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Add all 7 Tier 1 professional features")
    parser.add_argument("--path", default=".", help="Project root (default: current dir)")
    args = parser.parse_args()
    root = Path(args.path).resolve()
    if not (root / "backend").exists():
        print(f"WARNING: {root} may not be project root. Continue? [y/N] ", end="")
        if input().strip().lower() != "y":
            sys.exit(0)
    build(root)

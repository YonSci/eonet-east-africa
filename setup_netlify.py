"""
setup_netlify.py
----------------
Four changes in one script:
  1. Fix lookback days filter -- direct EONET fetch works without backend
  2. Remove demo mode toggle from UI -- always fetch real data
  3. Remove remaining ICPAC text, add NET-EA branding next to full title
  4. Add Netlify deployment config (netlify.toml + .env.production)

Run from the eonet-east-africa project root:
    python setup_netlify.py

Files created / updated:
    netlify.toml                              NEW -- Netlify build + redirect config
    frontend/.env.production                  NEW -- VITE_EONET_DIRECT=true for prod builds
    frontend/src/api/queries.js               -- direct EONET, days filter, no mock
    frontend/src/store/useAppStore.js         -- remove dataSource field
    frontend/src/components/TopNav.jsx        -- clean title, no demo toggle
    frontend/src/components/AboutPanel.jsx    -- patch remaining ICPAC text
    frontend/src/components/FilterSidebar.jsx -- patch remaining ICPAC text
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
# netlify.toml  --  root of repo
# =============================================================================
FILES["_root/netlify.toml"] = """[build]
  base    = "frontend"
  command = "npm run build"
  publish = "dist"

[build.environment]
  NODE_VERSION       = "20"
  VITE_EONET_DIRECT  = "true"

# SPA fallback: all routes serve index.html
[[redirects]]
  from   = "/*"
  to     = "/index.html"
  status = 200
"""

# =============================================================================
# .env.production  --  auto-loaded by Vite during `npm run build`
# =============================================================================
FILES["frontend/.env.production"] = """# Vite loads this file automatically during `npm run build`
# Do NOT commit secrets here -- this file is safe (only public env vars)

# Fetch EONET directly from the browser (no backend proxy needed)
# Required for Netlify, GitHub Pages, and any static deployment
VITE_EONET_DIRECT=true
"""

# =============================================================================
# queries.js
#   - Direct EONET GeoJSON fetch (for Netlify + when backend is offline)
#   - Backend proxy fetch (for local dev with FastAPI running)
#   - Auto-selects based on VITE_EONET_DIRECT env var
#   - Days filter always respected (queryKey includes lookbackDays)
#   - Summary computed from events data (no extra /summary round-trip)
#   - No mock data in production UI
# =============================================================================
FILES["frontend/src/api/queries.js"] = """import { useQuery } from '@tanstack/react-query'
import useAppStore from '../store/useAppStore.js'

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------
const EONET_BASE  = 'https://eonet.gsfc.nasa.gov/api/v3'
const EA_BBOX     = '21.8,22.0,51.4,-11.7'   // min_lon,max_lat,max_lon,min_lat
const USE_DIRECT  = import.meta.env.VITE_EONET_DIRECT === 'true'
const API_BASE    = import.meta.env.VITE_API_BASE_URL || ''

// ---------------------------------------------------------------------------
// Convert EONET GeoJSON feature -> our flat event object
// ---------------------------------------------------------------------------
function convertFeature(feat) {
  const props = feat.properties || {}
  const geom  = feat.geometry   || {}
  const cats  = props.categories || []
  const srcs  = props.sources    || []

  let coords = null
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
    latest_date: props.date   || (props.geometryDates || [])[0] || '',
    coords,
    sources: srcs,
    magnitude: props.magnitudeValue != null
      ? { value: props.magnitudeValue, unit: props.magnitudeUnit }
      : null,
  }
}

// ---------------------------------------------------------------------------
// Fetch strategies
// ---------------------------------------------------------------------------

// Direct from NASA EONET -- used on Netlify / static deployments
async function fetchDirect(days, status) {
  const params = new URLSearchParams({ bbox: EA_BBOX, days, status, limit: 500 })
  const url    = EONET_BASE + '/events/geojson?' + params
  const res    = await fetch(url)
  if (!res.ok) throw new Error('EONET ' + res.status)
  const data   = await res.json()
  return (data.features || []).map(convertFeature)
}

// Via FastAPI backend -- used in local dev
async function fetchViaBackend(days, status) {
  const params = new URLSearchParams({ days, status })
  const res    = await fetch(API_BASE + '/events?' + params)
  if (!res.ok) throw new Error('Backend ' + res.status)
  const data   = await res.json()
  return data.events || []
}

// Unified: tries backend first (local dev), falls back to direct EONET
async function fetchEvents(days, status) {
  if (USE_DIRECT) return fetchDirect(days, status)
  try {
    return await fetchViaBackend(days, status)
  } catch {
    console.info('[NET-EA] Backend offline -- fetching EONET directly')
    return fetchDirect(days, status)
  }
}

// ---------------------------------------------------------------------------
// Hooks
// ---------------------------------------------------------------------------

export function useEvents() {
  const { activeStatus, lookbackDays } = useAppStore()

  return useQuery({
    // queryKey includes lookbackDays -- TanStack refetches when days slider changes
    queryKey:        ['events', activeStatus, lookbackDays],
    queryFn:         () => fetchEvents(lookbackDays, activeStatus),
    staleTime:       10 * 60 * 1000,   // treat data fresh for 10 min
    refetchInterval: 15 * 60 * 1000,   // poll every 15 min for live updates
    retry:           2,
  })
}

// Summary is derived client-side from the events -- no extra network call
export function useSummary() {
  const { data: events = [], isLoading } = useEvents()

  const open   = events.filter((e) => e.status === 'open').length
  const closed = events.filter((e) => e.status === 'closed').length
  const by_category = {}
  events.forEach((e) => {
    by_category[e.category] = (by_category[e.category] || 0) + 1
  })

  return {
    data: { total: events.length, open, closed, by_category },
    isLoading,
  }
}

// Cache status: shows API mode and last update time
export function useCacheStatus() {
  return useQuery({
    queryKey:        ['cache_status'],
    queryFn:         async () => {
      if (USE_DIRECT) {
        return { mode: 'direct', note: 'Fetching from NASA EONET directly' }
      }
      try {
        const res = await fetch(API_BASE + '/status')
        if (!res.ok) return { mode: 'direct', note: 'Backend offline' }
        const d = await res.json()
        return { ...d, mode: 'backend' }
      } catch {
        return { mode: 'direct', note: 'Backend offline -- using direct EONET' }
      }
    },
    refetchInterval: 60 * 1000,
    staleTime:       30 * 1000,
  })
}
"""

# =============================================================================
# useAppStore.js  -- remove dataSource field entirely
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

const useAppStore = create((set) => ({
  activeCategories: ALL_CATS,
  activeStatus:     'all',
  lookbackDays:     90,
  selectedEventId:  null,
  lightMode:        true,
  sidebarOpen:      true,

  toggleCategory:   (cat)  => set((s) => ({
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
  toggleSidebar:  () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
}))

if (typeof document !== 'undefined') {
  document.documentElement.classList.add('light')
}

export default useAppStore
"""

# =============================================================================
# TopNav.jsx  --  clean title + no demo toggle
# =============================================================================
FILES["frontend/src/components/TopNav.jsx"] = """import React from 'react'
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
"""

# =============================================================================
# Text patches applied to existing files (find-and-replace)
# =============================================================================
TEXT_PATCHES = {
  "frontend/src/components/AboutPanel.jsx": {
    'ICPAC Greater Horn of Africa region': 'Greater Horn of Africa region',
    'ICPAC Greater Horn of Africa (GHA) region': 'Greater Horn of Africa region',
    'ICPAC GHA region': 'Greater Horn of Africa region',
    'ICPAC GHA': 'Greater Horn of Africa',
    'ICPAC': 'NET-EA',
    'on-premise NET-EA server deployment': 'on-premise server deployment',
  },
  "frontend/src/components/FilterSidebar.jsx": {
    'Greater Horn of Africa\n          (21.8-51.4': 'Greater Horn of Africa (21.8-51.4',
    'ICPAC': '',
  },
  "frontend/src/App.jsx": {
    'Greater Horn of Africa\n            </span>': 'East Africa\n            </span>',
    "{ id: 'about',     label: 'About'     },":
    "{ id: 'about',     label: 'About'     },",
  },
  "frontend/src/components/MapPanel.jsx": {
    'ICPAC Greater Horn of Africa': 'Greater Horn of Africa',
    'ICPAC': '',
  },
}

# =============================================================================
# Builder
# =============================================================================
def build(root: Path):
    hdr(f"Applying Netlify + cleanup in: {root}")
    created = updated = patched = 0

    # 1. Full file writes
    for rel, content in FILES.items():
        if rel.startswith("_root/"):
            target = root / rel[6:]   # strip the _root/ prefix -> repo root
        else:
            target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        existed = target.exists()
        target.write_text(content, encoding="utf-8")
        if existed:
            ow(f"update  {rel.replace('_root/', '')}")
            updated += 1
        else:
            ok(f"create  {rel.replace('_root/', '')}")
            created += 1

    # 2. Text patches
    for rel, patches in TEXT_PATCHES.items():
        target = root / rel
        if not target.exists():
            print(f"  SKIP  {rel} (not found)")
            continue
        txt = target.read_text(encoding="utf-8")
        n = 0
        for old, new in patches.items():
            if old in txt:
                txt = txt.replace(old, new)
                n += 1
        if n:
            target.write_text(txt, encoding="utf-8")
            ow(f"patch   {rel}  ({n} sub{'s' if n > 1 else ''})")
            patched += 1

    hdr("Done")
    print(f"  Files created : {created}")
    print(f"  Files updated : {updated}")
    print(f"  Files patched : {patched}")
    print()
    print("  Changes summary:")
    print("    [1] Days filter: clicking 7d/14d/30d/60d/90d/180d/365d now refetches")
    print("        real EONET data immediately via direct API or backend proxy")
    print("    [2] Demo mode removed: no toggle, no badge -- always real data")
    print("    [3] ICPAC text cleaned from all files")
    print("    [4] Title: 'Natural Event Tracker for East Africa' + NET-EA badge")
    print("    [5] Netlify: netlify.toml + .env.production created")
    print()
    print("  Local dev (no errors):")
    print("    cd frontend && npm run dev")
    print()
    print("  Netlify deploy steps:")
    print("    1. Push repo to GitHub")
    print("    2. Log in to netlify.com -> Add new site -> Import from GitHub")
    print("    3. Select your repo -- Netlify auto-reads netlify.toml")
    print("    4. Click Deploy site -- done")
    print("    5. Live URL: https://your-site-name.netlify.app")
    print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Netlify + days filter + cleanup")
    parser.add_argument("--path", default=".", help="Project root (default: current dir)")
    args = parser.parse_args()
    root = Path(args.path).resolve()
    if not (root / "backend").exists():
        print(f"WARNING: {root} may not be project root. Continue? [y/N] ", end="")
        if input().strip().lower() != "y":
            sys.exit(0)
    build(root)

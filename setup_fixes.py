"""
setup_fixes.py
--------------
Two fixes:
  1. Suppress Vite proxy ECONNREFUSED errors (backend not running = silent fallback to mock)
  2. Remove ICPAC / ILRI institutional text from all UI components

Run from the eonet-east-africa project root:
    python setup_fixes.py
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
# vite.config.js  -- silence proxy errors when backend is offline
# =============================================================================
FILES["vite.config.js"] = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

function silentProxy(target) {
  return {
    target,
    changeOrigin: true,
    configure: (proxy) => {
      proxy.on('error', () => {})
    },
  }
}

export default defineConfig({
  plugins: [react()],
  base: '/',
  server: {
    port: 5173,
    proxy: {
      '/events':  silentProxy('http://localhost:8000'),
      '/summary': silentProxy('http://localhost:8000'),
      '/status':  silentProxy('http://localhost:8000'),
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
})
"""

# =============================================================================
# useAppStore.js  -- mock as default so app never tries the backend on startup
# =============================================================================
FILES["src/store/useAppStore.js"] = """import { create } from 'zustand'

export const CATEGORIES = {
  wildfires:           { label: 'Wildfires',            color: '#E8593C' },
  severeStorms:        { label: 'Severe Storms',         color: '#378ADD' },
  floods:              { label: 'Floods',                color: '#1D9E75' },
  drought:             { label: 'Drought',               color: '#BA7517' },
  volcanoes:           { label: 'Volcanoes',             color: '#E24B4A' },
  dustHaze:            { label: 'Dust and Haze',         color: '#888780' },
  earthquakes:         { label: 'Earthquakes',           color: '#7F77DD' },
  landslides:          { label: 'Landslides',            color: '#639922' },
  temperatureExtremes: { label: 'Temperature Extremes',  color: '#E85D24' },
  waterColor:          { label: 'Water Color',           color: '#1D6FA5' },
}

export const ALL_CATS = Object.keys(CATEGORIES)

const useAppStore = create((set) => ({
  activeCategories: ALL_CATS,
  activeStatus:     'all',
  lookbackDays:     90,
  selectedEventId:  null,
  lightMode:        true,
  sidebarOpen:      true,
  dataSource:       'mock',

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
  setDataSource:  (v) => set({ dataSource: v }),
}))

if (typeof document !== 'undefined') {
  document.documentElement.classList.add('light')
}

export default useAppStore
"""

# =============================================================================
# TopNav.jsx  -- remove ILRI badge and region label
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

      {/* Title */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        <span style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-primary)',
                       lineHeight: 1, letterSpacing: '-0.01em' }}>
          Natural Event Tracker
        </span>
        <span style={{ fontSize: 10, color: '#1D9E75', fontWeight: 500,
                       letterSpacing: '0.04em', textTransform: 'uppercase' }}>
          East Africa
        </span>
      </div>

      <div style={{ flex: 1 }} />

      {/* Mock badge */}
      {isMock && (
        <span style={{ fontSize: 11, fontWeight: 500, padding: '2px 8px',
                       borderRadius: 100, background: '#EAF3DE', color: '#27500A',
                       border: '1px solid #97C45944' }}>
          Demo data
        </span>
      )}

      {/* Cache info when live */}
      {cacheInfo && !isMock && (
        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
          {cacheInfo.event_count} events
          {cacheInfo.ttl_remaining_s != null
            ? ' -- refresh in ' + Math.ceil(cacheInfo.ttl_remaining_s / 60) + 'm'
            : ''}
        </span>
      )}

      {/* Data source toggle */}
      <button
        onClick={() => setDataSource(isMock ? 'auto' : 'mock')}
        title={isMock ? 'Switch to live API' : 'Switch to demo data'}
        style={{
          ...btnStyle, fontSize: 11, padding: '4px 10px', borderRadius: 6,
          border: '1px solid var(--border-primary)',
          background: 'transparent',
        }}
      >
        {isMock ? 'Connect API' : 'Demo mode'}
      </button>

      {/* Light/dark toggle */}
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
# MapPanel.jsx  -- replace "ICPAC Greater Horn of Africa" with neutral label
# This is a targeted patch on just the label string inside the existing file.
# We read, replace, write rather than rewriting the full 300+ line component.
# =============================================================================
MAP_PATCH = {
  'ICPAC Greater Horn of Africa': 'Greater Horn of Africa',
}

# =============================================================================
# App.jsx  -- remove "ICPAC GHA Region" from tab bar
# =============================================================================
APP_PATCH = {
  'ICPAC GHA Region': 'Greater Horn of Africa',
}

# =============================================================================
# FilterSidebar.jsx  -- update data source blurb
# =============================================================================
SIDEBAR_OLD = """          <p style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.6 }}>
            NASA EONET v3 API filtered to East Africa bbox
            (21.8-51.4 E, 11.7 S - 22.0 N). Auto-refreshed every 15 min.
          </p>"""

SIDEBAR_NEW = """          <p style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.6 }}>
            NASA EONET v3 API filtered to the Greater Horn of Africa
            (21.8-51.4 E, 11.7 S - 22.0 N). Auto-refreshed every 15 min.
          </p>"""

# =============================================================================
# AboutPanel.jsx  -- neutral header, remove institutional branding
# =============================================================================
ABOUT_PATCHES = {
  'Natural Event Tracker for East Africa (NET-EA) was developed at\n          the International Livestock Research Institute (ILRI) Climate Services\n          unit to provide a unified, accessible view of natural hazard events\n          across the 11-country ICPAC Greater Horn of Africa (GHA) region.\n          It bridges the gap between raw NASA satellite-derived event metadata\n          and actionable situational awareness for climate, agriculture, and\n          humanitarian professionals working in the region.':
  'Natural Event Tracker for East Africa (NET-EA) provides a unified,\n          accessible view of natural hazard events across the 11-country\n          Greater Horn of Africa region. It bridges the gap between raw\n          NASA satellite-derived event metadata and actionable situational\n          awareness for climate, agriculture, and humanitarian professionals.',

  'The dashboard is geographically scoped to the 11-country ICPAC GHA\n          region using the bounding box':
  'The dashboard is geographically scoped to the 11-country Greater Horn\n          of Africa region using the bounding box',

  '<Section title="ICPAC Greater Horn of Africa region">':
  '<Section title="Greater Horn of Africa region">',

  "'Docker Compose packaging for on-premise ILRI/ICPAC server deployment',":
  "'Docker Compose packaging for on-premise server deployment',",

  'NET-EA v2.0 -- ILRI Climate Services 2025':
  'NET-EA v2.0 -- Natural Event Tracker for East Africa 2025',

  '"Built at"       value="ILRI Climate Services, Addis Ababa, Ethiopia"\n          link="https://www.ilri.org"':
  '"Built at"       value="East Africa Climate Services"',

  '"In collaboration with" value="ICPAC (IGAD Climate Prediction and Applications Centre)"\n          link="https://www.icpac.net"':
  '"Data region" value="Greater Horn of Africa (11 countries)"',

  '        <a href="https://www.icpac.net" target="_blank" rel="noreferrer"\n           style={{ fontSize: 11, color: \'#378ADD\' }}>ICPAC</a>\n        <a href="https://www.ilri.org" target="_blank" rel="noreferrer"\n           style={{ fontSize: 11, color: \'#378ADD\' }}>ILRI</a>':
  '',
}

# =============================================================================
# Builder
# =============================================================================
def apply_patches(content: str, patches: dict) -> tuple[str, int]:
    count = 0
    for old, new in patches.items():
        if old in content:
            content = content.replace(old, new)
            count += 1
    return content, count


def build(root: Path):
    hdr(f"Applying fixes in: {root}")
    fe = root / "frontend"

    # 1. Full rewrites
    for rel, content in FILES.items():
        target = fe / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        existed = target.exists()
        target.write_text(content, encoding="utf-8")
        ow(f"update  frontend/{rel}") if existed else ok(f"create  frontend/{rel}")

    # 2. Targeted text patches on existing files
    patch_targets = [
        ("src/components/MapPanel.jsx",    MAP_PATCH),
        ("src/App.jsx",                    APP_PATCH),
    ]
    for rel, patches in patch_targets:
        target = fe / rel
        if not target.exists():
            print(f"  SKIP  {rel} (not found)")
            continue
        content, n = apply_patches(target.read_text(encoding="utf-8"), patches)
        target.write_text(content, encoding="utf-8")
        ow(f"patch   frontend/{rel}  ({n} substitution{'s' if n != 1 else ''})")

    # 3. FilterSidebar targeted patch
    sb = fe / "src/components/FilterSidebar.jsx"
    if sb.exists():
        txt = sb.read_text(encoding="utf-8")
        if SIDEBAR_OLD in txt:
            txt = txt.replace(SIDEBAR_OLD, SIDEBAR_NEW)
            sb.write_text(txt, encoding="utf-8")
            ow("patch   frontend/src/components/FilterSidebar.jsx  (1 substitution)")

    # 4. AboutPanel targeted patches
    ap = fe / "src/components/AboutPanel.jsx"
    if ap.exists():
        txt, n = apply_patches(ap.read_text(encoding="utf-8"), ABOUT_PATCHES)
        ap.write_text(txt, encoding="utf-8")
        ow(f"patch   frontend/src/components/AboutPanel.jsx  ({n} substitutions)")

    hdr("Done")
    print()
    print("  Fix 1 -- Proxy errors:")
    print("    vite.config.js now silences ECONNREFUSED -- no more console spam")
    print("    dataSource defaults to 'mock' -- app loads instantly without backend")
    print("    Click 'Connect API' in the top nav when the FastAPI backend is running")
    print()
    print("  Fix 2 -- Text cleanup:")
    print("    Removed: ICPAC, ILRI institutional labels from all UI components")
    print("    'ICPAC Greater Horn of Africa' -> 'Greater Horn of Africa'")
    print("    'ICPAC GHA Region' -> 'Greater Horn of Africa'")
    print("    TopNav: no more ILRI badge; 'Use mock' -> 'Demo mode'")
    print("    Mock badge: changed from amber warning to green 'Demo data'")
    print()
    print("  Restart Vite (no more proxy errors):")
    print("    cd frontend && npm run dev")
    print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Fix proxy errors + remove institutional text")
    parser.add_argument("--path", default=".", help="Project root (default: current dir)")
    args = parser.parse_args()
    root = Path(args.path).resolve()
    if not (root / "backend").exists():
        print(f"WARNING: {root} may not be project root. Continue? [y/N] ", end="")
        if input().strip().lower() != "y":
            sys.exit(0)
    build(root)

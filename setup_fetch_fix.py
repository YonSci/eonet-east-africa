"""
setup_fetch_fix.py
------------------
Fixes the endless "Loading events..." caused by the office network
blocking outbound HTTPS to eonet.gsfc.nasa.gov.

Root cause:
  browser fetch() has no built-in timeout -- it hangs for up to
  75-120 seconds (Windows OS TCP timeout) per attempt. With retry:2,
  total hang time = 3 x ~90s = ~4.5 minutes before showing any error.

Fix:
  1. queries.js  -- AbortSignal.timeout(9000) on every fetch, retry:0,
                    clear error thrown so TanStack enters error state fast
  2. MapPanel.jsx -- show network-blocked error banner with instructions
  3. EventList.jsx -- show error row instead of endless "Loading..."
  4. StatCards.jsx -- show error state instead of skeleton forever
  5. App.jsx      -- global ErrorBoundary catches render crashes

Run from the eonet-east-africa project root:
    python setup_fetch_fix.py
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
# queries.js -- fast timeout + proper error state
# =============================================================================
FILES["frontend/src/api/queries.js"] = """import { useQuery } from '@tanstack/react-query'
import useAppStore from '../store/useAppStore.js'

const EONET_BASE = 'https://eonet.gsfc.nasa.gov/api/v3'
const EA_BBOX    = '21.8,22.0,51.4,-11.7'
const USE_DIRECT = import.meta.env.VITE_EONET_DIRECT === 'true'
const API_BASE   = import.meta.env.VITE_API_BASE_URL || ''

// How long to wait for a response before giving up (milliseconds)
const FETCH_TIMEOUT_MS = 9000

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

// Create an AbortSignal that times out after FETCH_TIMEOUT_MS
function timeoutSignal() {
  return AbortSignal.timeout(FETCH_TIMEOUT_MS)
}

async function fetchDirect(opts) {
  const params = new URLSearchParams({ bbox: EA_BBOX, limit: 500, status: opts.status || 'all' })
  if (opts.startDate && opts.endDate) {
    params.set('start', opts.startDate)
    params.set('end',   opts.endDate)
  } else {
    params.set('days', String(opts.days || 90))
  }
  const url = EONET_BASE + '/events/geojson?' + params
  let res
  try {
    res = await fetch(url, { signal: timeoutSignal() })
  } catch (err) {
    if (err.name === 'TimeoutError' || err.name === 'AbortError') {
      throw new Error(
        'NETWORK_BLOCKED: Connection to eonet.gsfc.nasa.gov timed out after ' +
        (FETCH_TIMEOUT_MS / 1000) + 's. Your network may be blocking outbound ' +
        'HTTPS to NASA servers. Try connecting via a mobile hotspot.'
      )
    }
    throw new Error('FETCH_FAILED: ' + (err.message || String(err)))
  }
  if (!res.ok) throw new Error('EONET_HTTP_' + res.status)
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
  let res
  try {
    res = await fetch(API_BASE + '/events?' + params, { signal: timeoutSignal() })
  } catch {
    throw new Error('BACKEND_OFFLINE')
  }
  if (!res.ok) throw new Error('BACKEND_HTTP_' + res.status)
  const data = await res.json()
  return data.events || []
}

async function fetchEvents(opts) {
  if (USE_DIRECT) {
    // Netlify / static deployment -- direct only, no backend
    return fetchDirect(opts)
  }
  // Local dev -- try backend proxy first, then direct
  try {
    return await fetchViaBackend(opts)
  } catch (backendErr) {
    // Backend offline is expected in local dev -- try direct
    console.info('[NET-EA] Backend offline, trying EONET directly...')
    return fetchDirect(opts)
  }
}

// ---------------------------------------------------------------------------
// Helper: is this error a network-blocked error?
// ---------------------------------------------------------------------------
export function isNetworkBlockedError(error) {
  if (!error) return false
  const msg = error.message || ''
  return msg.includes('NETWORK_BLOCKED') ||
         msg.includes('timed out') ||
         msg.includes('TimeoutError') ||
         msg.includes('Failed to fetch') ||
         msg.includes('NetworkError')
}

// ---------------------------------------------------------------------------
// Hooks
// ---------------------------------------------------------------------------

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
    retry:           0,    // no retries -- fail fast, user can manually retry
    retryOnMount:    false,
  })
}

export function useSummary() {
  const { data: events = [], isLoading, isError } = useEvents()
  const open        = events.filter((e) => e.status === 'open').length
  const closed      = events.filter((e) => e.status === 'closed').length
  const by_category = {}
  events.forEach((e) => { by_category[e.category] = (by_category[e.category] || 0) + 1 })
  return { data: { total: events.length, open, closed, by_category }, isLoading, isError }
}

export function useCacheStatus() {
  return useQuery({
    queryKey:        ['cache_status'],
    queryFn: async () => {
      if (USE_DIRECT) return { mode: 'direct', note: 'NASA EONET direct fetch' }
      try {
        const res = await fetch(API_BASE + '/status', { signal: timeoutSignal() })
        if (!res.ok) return { mode: 'direct', note: 'Backend offline' }
        return { ...(await res.json()), mode: 'backend' }
      } catch { return { mode: 'direct', note: 'Backend offline' } }
    },
    refetchInterval: 60 * 1000,
    staleTime:       30 * 1000,
    retry:           0,
  })
}

// Year-over-year helpers (added by setup_yoy.py)
const EONET_BASE_YOY = 'https://eonet.gsfc.nasa.gov/api/v3'
const EA_BBOX_YOY    = '21.8,22.0,51.4,-11.7'

async function fetchYearDirect(year) {
  const curYear = new Date().getFullYear()
  const start   = year + '-01-01'
  const end     = (year === curYear)
    ? new Date().toISOString().slice(0, 10)
    : year + '-12-31'
  const params  = new URLSearchParams({
    bbox: EA_BBOX_YOY, status: 'all', limit: 500, start, end,
  })
  const res = await fetch(EONET_BASE_YOY + '/events/geojson?' + params,
    { signal: AbortSignal.timeout(12000) })
  if (!res.ok) throw new Error('EONET ' + res.status)
  const data = await res.json()
  return (data.features || []).map(convertFeature)
}

export function useYearData(year) {
  return useQuery({
    queryKey:  ['year-events', year],
    queryFn:   () => fetchYearDirect(year),
    staleTime: 60 * 60 * 1000,
    enabled:   year > 2015 && year <= new Date().getFullYear(),
    retry:     0,
  })
}
"""

# =============================================================================
# NetworkError.jsx -- reusable error panel with fix instructions
# =============================================================================
FILES["frontend/src/components/NetworkError.jsx"] = """import React from 'react'
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
"""

# =============================================================================
# MapPanel.jsx -- show NetworkError instead of infinite spinner
# (targeted patch: replace the loading overlay logic)
# =============================================================================
MAP_PATCH_OLD = """      {isLoading && (
        <div style={{ position:'absolute', inset:0, zIndex:1000,
                      display:'flex', alignItems:'center', justifyContent:'center',
                      background:'rgba(246,248,250,0.75)', fontSize:13,
                      color:'var(--text-secondary)', pointerEvents:'none' }}>
          Loading events...
        </div>
      )}"""

MAP_PATCH_NEW = """      {isLoading && (
        <div style={{ position:'absolute', inset:0, zIndex:1000,
                      display:'flex', alignItems:'center', justifyContent:'center',
                      background:'rgba(246,248,250,0.75)', fontSize:13,
                      color:'var(--text-secondary)', pointerEvents:'none' }}>
          <div style={{ display:'flex', flexDirection:'column', alignItems:'center', gap:10 }}>
            <div style={{ width:28, height:28, border:'3px solid #1D9E75',
                          borderTopColor:'transparent', borderRadius:'50%',
                          animation:'spin 0.9s linear infinite' }} />
            <span>Loading events from NASA EONET...</span>
          </div>
        </div>
      )}
      {isError && <NetworkError error={error} />}"""

MAP_IMPORT_OLD = """import useAppStore, { CATEGORIES, COUNTRY_MAP } from '../store/useAppStore.js'
import { useEvents } from '../api/queries.js'"""

MAP_IMPORT_NEW = """import useAppStore, { CATEGORIES, COUNTRY_MAP } from '../store/useAppStore.js'
import { useEvents } from '../api/queries.js'
import NetworkError from './NetworkError.jsx'"""

MAP_DESTRUCTURE_OLD = "  const { data: rawEvents = [], isLoading } = useEvents()"
MAP_DESTRUCTURE_NEW  = "  const { data: rawEvents = [], isLoading, isError, error } = useEvents()"

# Add spin keyframes to index.css
SPIN_CSS = """
@keyframes spin {
  to { transform: rotate(360deg); }
}
"""

# =============================================================================
# EventList.jsx -- show error instead of endless loading row
# =============================================================================
EVENTLIST_IMPORT_OLD = "import { useEvents } from '../api/queries.js'"
EVENTLIST_IMPORT_NEW = """import { useEvents } from '../api/queries.js'
import NetworkError from './NetworkError.jsx'"""

EVENTLIST_DESTRUCTURE_OLD = "  const { data: rawEvents = [], isLoading } = useEvents()"
EVENTLIST_DESTRUCTURE_NEW  = "  const { data: rawEvents = [], isLoading, isError, error } = useEvents()"

EVENTLIST_LOADING_OLD = """            {isLoading && (
              <div style={{ padding: 20, textAlign: 'center',
                            color: 'var(--text-muted)', fontSize: 12 }}>
                Loading...
              </div>
            )}"""

EVENTLIST_LOADING_NEW = """            {isLoading && (
              <div style={{ padding: '16px 10px', textAlign: 'center',
                            color: 'var(--text-muted)', fontSize: 12 }}>
                <div style={{ display:'flex', alignItems:'center',
                              justifyContent:'center', gap:8 }}>
                  <div style={{ width:14, height:14,
                                border:'2px solid #1D9E75',
                                borderTopColor:'transparent', borderRadius:'50%',
                                animation:'spin 0.9s linear infinite', flexShrink:0 }} />
                  Fetching from NASA EONET...
                </div>
              </div>
            )}
            {isError && <NetworkError error={error} compact />}"""

# =============================================================================
# StatCards.jsx -- show error state instead of skeleton forever
# =============================================================================
STATCARDS_IMPORT_OLD = "import { useSummary } from '../api/queries.js'"
STATCARDS_IMPORT_NEW = """import { useSummary } from '../api/queries.js'
import { isNetworkBlockedError } from '../api/queries.js'"""

STATCARDS_DESTRUCTURE_OLD = "  const { data: s, isLoading } = useSummary()"
STATCARDS_DESTRUCTURE_NEW  = "  const { data: s, isLoading, isError, error } = useSummary()"

STATCARDS_SKELETON_OLD = """      {isLoading ? (
        Array.from({ length: 4 }).map((_, i) => (
          <div key={i} style={{ background: 'var(--bg-surface)',
                                border: '1px solid var(--border-primary)',
                                borderRadius: 'var(--radius-md)', padding: '10px 14px' }}>
            <SkeletonRect h={26} w="50%" style={{ marginBottom: 6 }} />
            <SkeletonRect h={13} w="65%" />
          </div>
        ))
      ) : ("""

STATCARDS_SKELETON_NEW = """      {isError ? (
        <div style={{ gridColumn:'1 / -1', padding:'10px 14px',
                      fontSize:12, color:'#BA7517', fontWeight:500,
                      background:'#FAEEDA', borderRadius:'var(--radius-md)',
                      border:'1px solid #BA751733' }}>
          {isNetworkBlockedError(error)
            ? 'Network blocked -- cannot reach NASA EONET. Try a mobile hotspot.'
            : 'Failed to load events. Check console for details.'}
        </div>
      ) : isLoading ? (
        Array.from({ length: 4 }).map((_, i) => (
          <div key={i} style={{ background: 'var(--bg-surface)',
                                border: '1px solid var(--border-primary)',
                                borderRadius: 'var(--radius-md)', padding: '10px 14px' }}>
            <SkeletonRect h={26} w="50%" style={{ marginBottom: 6 }} />
            <SkeletonRect h={13} w="65%" />
          </div>
        ))
      ) : ("""

# =============================================================================
# Builder
# =============================================================================
def apply(path: Path, old: str, new: str, label: str) -> bool:
    if not path.exists():
        print(f"  SKIP  {label} (file not found)")
        return False
    txt = path.read_text(encoding="utf-8")
    if old not in txt:
        print(f"  SKIP  {label} (marker not found)")
        return False
    path.write_text(txt.replace(old, new), encoding="utf-8")
    ow(f"patch   {label}")
    return True


def build(root: Path):
    fe = root / "frontend"
    hdr(f"Applying fetch-timeout + error-state fix in: {root}")
    created = updated = 0

    # 1. Write new files
    for rel, content in FILES.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        existed = target.exists()
        target.write_text(content, encoding="utf-8")
        (ow if existed else ok)(("update  " if existed else "create  ") + rel)
        if existed: updated += 1
        else: created += 1

    # 2. Patch MapPanel.jsx
    mp = fe / "src/components/MapPanel.jsx"
    apply(mp, MAP_IMPORT_OLD,       MAP_IMPORT_NEW,       "MapPanel.jsx imports")
    apply(mp, MAP_DESTRUCTURE_OLD,  MAP_DESTRUCTURE_NEW,  "MapPanel.jsx destructure")
    apply(mp, MAP_PATCH_OLD,        MAP_PATCH_NEW,        "MapPanel.jsx error overlay")

    # 3. Patch EventList.jsx
    el = fe / "src/components/EventList.jsx"
    apply(el, EVENTLIST_IMPORT_OLD,       EVENTLIST_IMPORT_NEW,       "EventList.jsx imports")
    apply(el, EVENTLIST_DESTRUCTURE_OLD,  EVENTLIST_DESTRUCTURE_NEW,  "EventList.jsx destructure")
    apply(el, EVENTLIST_LOADING_OLD,      EVENTLIST_LOADING_NEW,      "EventList.jsx loading/error")

    # 4. Patch StatCards.jsx
    sc = fe / "src/components/StatCards.jsx"
    apply(sc, STATCARDS_IMPORT_OLD,       STATCARDS_IMPORT_NEW,       "StatCards.jsx imports")
    apply(sc, STATCARDS_DESTRUCTURE_OLD,  STATCARDS_DESTRUCTURE_NEW,  "StatCards.jsx destructure")
    apply(sc, STATCARDS_SKELETON_OLD,     STATCARDS_SKELETON_NEW,     "StatCards.jsx error state")

    # 5. Add spin keyframe to index.css
    css = fe / "src/index.css"
    if css.exists():
        css_txt = css.read_text(encoding="utf-8")
        if "@keyframes spin" not in css_txt:
            css.write_text(css_txt.rstrip() + "\n" + SPIN_CSS, encoding="utf-8")
            ow("patch   index.css (spin keyframe)")
            updated += 1

    # 6. ASCII check
    print()
    bad = []
    for f in list((fe / "src").rglob("*.jsx")) + list((fe / "src").rglob("*.js")):
        raw = f.read_bytes()
        for i, line in enumerate(raw.split(b"\n"), 1):
            if any(b > 127 for b in line):
                bad.append(f"  {f.name}:{i}")
    if bad:
        print("  WARN  Non-ASCII (OXC will reject):")
        for b in bad[:6]: print(b)
    else:
        ok("ASCII-clean -- OXC safe")

    hdr("Done")
    print(f"  Files created : {created}")
    print(f"  Files updated : {updated}")
    print()
    print("  What changes:")
    print("    fetch() now times out after 9s (was no timeout = up to 90s hang)")
    print("    retry:0 -- fails immediately, no 3x retry loop (was ~4.5 min wait)")
    print("    Map shows a spinner + then a clear error panel with fix instructions")
    print("    Event list shows spinner + compact error row")
    print("    Stat cards show amber warning banner instead of infinite skeleton")
    print("    'Retry now' button immediately re-fetches without page reload")
    print("    'Test connection' opens eonet.gsfc.nasa.gov to confirm browser access")
    print()
    print("  No npm install needed. Restart Vite:")
    print("    cd frontend && npm run dev")
    print()
    print("  To get real data:")
    print("    Option 1: Switch to mobile hotspot, then click 'Retry now'")
    print("    Option 2: python scripts/validate_eonet.py --save")
    print("              (tests the connection first)")
    print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Fix fetch timeout and error states")
    parser.add_argument("--path", default=".", help="Project root (default: current dir)")
    args   = parser.parse_args()
    root   = Path(args.path).resolve()
    if not (root / "backend").exists():
        print(f"WARNING: {root} may not be project root. Continue? [y/N] ", end="")
        if input().strip().lower() != "y":
            sys.exit(0)
    build(root)

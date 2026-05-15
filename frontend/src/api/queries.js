import { useQuery } from '@tanstack/react-query'
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

import { useQuery } from '@tanstack/react-query'
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

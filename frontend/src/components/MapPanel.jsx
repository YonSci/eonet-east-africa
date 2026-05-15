import React, { useEffect, useState, useCallback } from 'react'
import {
  MapContainer, TileLayer, CircleMarker, Popup,
  GeoJSON, Rectangle, useMap,
} from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import useAppStore, { CATEGORIES } from '../store/useAppStore.js'
import { useEvents } from '../api/queries.js'

// --  region --------------------------------------------------------------
const _CENTER   = [6.5, 38.0]
const _ZOOM     = 5
const _MIN_ZOOM = 4
const _MAX_ZOOM = 10
const MAX_BOUNDS     = [[-16.0, 18.0], [26.0, 56.0]]
const REGION_BOUNDS  = [[-12.0, 22.0], [23.0, 52.0]]

// -- Country data --------------------------------------------------------------
const _ISO2 = ['DJ','ER','ET','KE','RW','SO','SS','SD','TZ','UG','BI']

const COUNTRY_BBOX = {
  SD: { minLat:  9, maxLat: 22, minLon: 21, maxLon: 38, name: 'Sudan'       },
  SS: { minLat:  3, maxLat: 12, minLon: 24, maxLon: 36, name: 'South Sudan' },
  ET: { minLat:  3, maxLat: 15, minLon: 33, maxLon: 48, name: 'Ethiopia'    },
  ER: { minLat: 12, maxLat: 18, minLon: 36, maxLon: 44, name: 'Eritrea'     },
  DJ: { minLat: 10, maxLat: 13, minLon: 41, maxLon: 44, name: 'Djibouti'    },
  SO: { minLat: -2, maxLat: 12, minLon: 40, maxLon: 52, name: 'Somalia'     },
  KE: { minLat: -5, maxLat:  5, minLon: 33, maxLon: 42, name: 'Kenya'       },
  UG: { minLat: -2, maxLat:  4, minLon: 29, maxLon: 35, name: 'Uganda'      },
  TZ: { minLat:-12, maxLat:  0, minLon: 29, maxLon: 41, name: 'Tanzania'    },
  RW: { minLat: -3, maxLat:  0, minLon: 28, maxLon: 31, name: 'Rwanda'      },
  BI: { minLat: -5, maxLat: -2, minLon: 28, maxLon: 31, name: 'Burundi'     },
}

function assignCountry(coords) {
  if (!coords) return null
  const lon = coords[0]
  const lat = coords[1]
  for (const [iso2, b] of Object.entries(COUNTRY_BBOX)) {
    if (lon >= b.minLon && lon <= b.maxLon && lat >= b.minLat && lat <= b.maxLat) {
      return iso2
    }
  }
  return null
}

// -- Choropleth colour scale: transparent -> teal -> amber -> coral ----------
function choroplethFill(count, maxCount) {
  if (count === 0 || maxCount === 0) return 'transparent'
  const t = Math.min(count / maxCount, 1)
  let r, g, b
  if (t < 0.5) {
    const s = t * 2
    r = Math.round(29  + (186 - 29)  * s)
    g = Math.round(158 + (117 - 158) * s)
    b = Math.round(117 + (23  - 117) * s)
  } else {
    const s = (t - 0.5) * 2
    r = Math.round(186 + (232 - 186) * s)
    g = Math.round(117 + (89  - 117) * s)
    b = Math.round(23  + (60  - 23)  * s)
  }
  return 'rgb(' + r + ',' + g + ',' + b + ')'
}

function getCatColor(cat) {
  return (CATEGORIES[cat] || {}).color || '#484f58'
}

const GEO_BASE = 'https://raw.githubusercontent.com/johan/world.geo.json/master/countries'
const TILE_DARK   = 'https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png'
const TILE_LABELS = 'https://{s}.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}{r}.png'
const TILE_LIGHT  = 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'
const ATTR        = '(c) OpenStreetMap contributors, (c) CARTO | NASA EONET v3'

// -- FitRegion on mount --------------------------------------------------------
function FitRegion() {
  const map = useMap()
  useEffect(() => { map.fitBounds(REGION_BOUNDS, { padding: [10, 10] }) }, [map])
  return null
}

// -- FlyTo selected event ------------------------------------------------------
function FlyTo({ events, selectedId }) {
  const map = useMap()
  useEffect(() => {
    if (!selectedId) return
    const ev = events.find((e) => e.id === selectedId)
    if (ev && ev.coords) map.flyTo([ev.coords[1], ev.coords[0]], 7, { duration: 1.2 })
  }, [selectedId, events, map])
  return null
}

// -- Outside mask --------------------------------------------------------------
function OutsideMask() {
  const strips = [
    [[-90, -180], [ 90,  22.0]],
    [[-90,  52.0], [ 90,  180]],
    [[ 23.0, 22.0], [ 90,  52.0]],
    [[-90,  22.0], [-12.0, 52.0]],
  ]
  return strips.map((b, i) => (
    <Rectangle key={i} bounds={b}
      pathOptions={{ color: 'transparent', fillColor: '#000', fillOpacity: 0.45, weight: 0 }} />
  ))
}

// -- Country layer (borders + optional choropleth fill) ------------------------
function CountriesLayer({ geo, choropleth, countryCounts }) {
  const maxCount = Math.max(...Object.values(countryCounts), 1)

  const styleFunc = useCallback((feature) => {
    const iso2  = feature.properties && feature.properties.iso2
    const count = (iso2 && countryCounts[iso2]) || 0
    if (choropleth) {
      return {
        color:       '#6b7280',
        weight:      1,
        fillColor:   choroplethFill(count, maxCount),
        fillOpacity: count > 0 ? 0.42 : 0.08,
      }
    }
    return {
      color:       '#4a5568',
      weight:      1.2,
      fillColor:   '#1e293b',
      fillOpacity: 0.10,
    }
  }, [choropleth, countryCounts, maxCount])

  if (!geo) return null

  // key forces GeoJSON remount when style data changes
  const key = 'countries-' + (choropleth ? 1 : 0) + '-' + Object.values(countryCounts).join('_')

  return <GeoJSON key={key} data={geo} style={styleFunc} />
}

// -- Choropleth legend ---------------------------------------------------------
function ChoroplethLegend({ maxCount }) {
  const stops = [0, 0.25, 0.5, 0.75, 1.0]
  return (
    <div style={{
      position: 'absolute', bottom: 30, right: 10, zIndex: 400,
      background: 'rgba(13,17,23,0.82)',
      border: '1px solid var(--border-primary)',
      borderRadius: 6, padding: '8px 12px',
      pointerEvents: 'none', minWidth: 140,
    }}>
      <div style={{ fontSize: 10, color: 'var(--text-muted)',
                    textTransform: 'uppercase', letterSpacing: '0.06em',
                    fontWeight: 600, marginBottom: 6 }}>
        Events / country
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 2, marginBottom: 4 }}>
        {stops.map((t, i) => (
          <div key={i} style={{
            flex: 1, height: 8, borderRadius: i === 0 ? '3px 0 0 3px' : i === stops.length - 1 ? '0 3px 3px 0' : 0,
            background: t === 0 ? '#1e293b' : choroplethFill(t * maxCount, maxCount),
          }} />
        ))}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between',
                    fontSize: 10, color: 'var(--text-muted)' }}>
        <span>0</span>
        <span>{Math.ceil(maxCount / 2)}</span>
        <span>{maxCount}+</span>
      </div>
    </div>
  )
}

// -- Main MapPanel -------------------------------------------------------------
export default function MapPanel({ height }) {
  const { activeCategories, activeStatus, selectedEventId, selectEvent, lightMode } = useAppStore()
  const { data: rawEvents = [], isLoading } = useEvents()

  const [geo,        setGeo]       = useState(null)
  const [choropleth, setChoropleth] = useState(false)

  // Fetch  country boundaries once on mount
  useEffect(() => {
    Promise.allSettled(
      _ISO2.map((iso) =>
        fetch(GEO_BASE + '/' + iso + '.geo.json', { signal: AbortSignal.timeout(7000) })
          .then((r) => (r.ok ? r.json() : null))
          .catch(() => null)
      )
    ).then((results) => {
      const features = results
        .filter((r, i) => r.status === 'fulfilled' && r.value)
        .flatMap((r, i) => {
          const iso = _ISO2[
            results.slice(0, results.indexOf(r)).filter(x => x.status === 'fulfilled').length +
            (r.status === 'fulfilled' ? results.filter((x,j) => j <= results.indexOf(r) && x.status === 'fulfilled').length - 1 : 0)
          ] || ''
          const d = r.value
          const raw = d && d.type === 'FeatureCollection' ? d.features : (d ? [d] : [])
          return raw.map((f) => ({ ...f, properties: { ...(f.properties || {}), iso2: _ISO2[results.indexOf(r)] } }))
        })
      if (features.length > 0) setGeo({ type: 'FeatureCollection', features })
    })
  }, [])

  // Apply filters
  const events = rawEvents.filter((ev) => {
    if (!activeCategories.includes(ev.category)) return false
    if (activeStatus === 'open'   && ev.status !== 'open')   return false
    if (activeStatus === 'closed' && ev.status !== 'closed') return false
    return ev.coords != null
  })

  // Count events per country for choropleth
  const countryCounts = {}
  events.forEach((ev) => {
    const iso = assignCountry(ev.coords)
    if (iso) countryCounts[iso] = (countryCounts[iso] || 0) + 1
  })
  const maxCount = Math.max(...Object.values(countryCounts), 1)

  return (
    <div style={{ flex: 1, position: 'relative', background: '#0d1117', minHeight: height || 340 }}>
      {/* Loading */}
      {isLoading && (
        <div style={{ position: 'absolute', inset: 0, zIndex: 500,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      background: 'rgba(13,17,23,0.6)', fontSize: 13,
                      color: 'var(--text-secondary)' }}>
          Loading events...
        </div>
      )}

      {/* Region badge */}
      <div style={{ position: 'absolute', top: 10, left: 10, zIndex: 400,
                    background: 'rgba(13,17,23,0.75)',
                    border: '1px solid var(--border-primary)', borderRadius: 6,
                    padding: '4px 10px', fontSize: 11, fontWeight: 600,
                    color: 'var(--accent-green)', letterSpacing: '0.05em',
                    pointerEvents: 'none' }}>
        Greater Horn of Africa
      </div>

      {/* Toolbar (top right) */}
      <div style={{ position: 'absolute', top: 10, right: 10, zIndex: 400,
                    display: 'flex', gap: 6, alignItems: 'center' }}>
        {/* Choropleth toggle */}
        <button
          onClick={() => setChoropleth((v) => !v)}
          title="Toggle country heatmap"
          style={{
            fontSize: 11, padding: '4px 10px', borderRadius: 6,
            border: '1px solid',
            borderColor: choropleth ? '#1D9E75' : 'var(--border-primary)',
            background:  choropleth ? '#1D9E7522' : 'rgba(13,17,23,0.75)',
            color:       choropleth ? '#1D9E75'   : 'var(--text-secondary)',
            cursor: 'pointer', fontWeight: choropleth ? 600 : 400,
          }}
        >
          Heatmap
        </button>
        {/* Event count */}
        <div style={{ background: 'rgba(13,17,23,0.75)',
                      border: '1px solid var(--border-primary)', borderRadius: 6,
                      padding: '4px 10px', fontSize: 12, color: 'var(--text-secondary)',
                      pointerEvents: 'none' }}>
          {events.length} event{events.length !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Choropleth legend */}
      {choropleth && <ChoroplethLegend maxCount={maxCount} />}

      {/* Marker legend (when NOT choropleth) */}
      {!choropleth && (
        <div style={{ position: 'absolute', bottom: 30, left: 10, zIndex: 400,
                      background: 'rgba(13,17,23,0.80)',
                      border: '1px solid var(--border-primary)',
                      borderRadius: 6, padding: '8px 10px', pointerEvents: 'none' }}>
          <div style={{ fontSize: 10, color: 'var(--text-muted)',
                        textTransform: 'uppercase', letterSpacing: '0.06em',
                        marginBottom: 6, fontWeight: 600 }}>Legend</div>
          <LegendRow color="#1D9E75" label="Open event"   dash={false} />
          <LegendRow color="#6e7681" label="Closed event" dash={true}  />
        </div>
      )}

      <MapContainer
        center={_CENTER} zoom={_ZOOM}
        minZoom={_MIN_ZOOM} maxZoom={_MAX_ZOOM}
        maxBounds={MAX_BOUNDS} maxBoundsViscosity={0.85}
        style={{ width: '100%', height: '100%' }}
      >
        {lightMode ? (
          <TileLayer url={TILE_LIGHT} attribution={ATTR} />
        ) : (
          <>
            <TileLayer url={TILE_DARK}   attribution={ATTR} />
            <TileLayer url={TILE_LABELS} />
          </>
        )}

        <OutsideMask />
        <CountriesLayer geo={geo} choropleth={choropleth} countryCounts={countryCounts} />
        <FitRegion />
        <FlyTo events={events} selectedId={selectedEventId} />

        {events.map((ev) => {
          const color  = getCatColor(ev.category)
          const isOpen = ev.status === 'open'
          const isSel  = ev.id === selectedEventId
          const cat    = CATEGORIES[ev.category] || {}
          return (
            <CircleMarker
              key={ev.id}
              center={[ev.coords[1], ev.coords[0]]}
              radius={isSel ? 13 : isOpen ? 9 : 7}
              pathOptions={{
                color:       isSel ? '#fff' : color,
                fillColor:   color,
                fillOpacity: isOpen ? 0.88 : 0.42,
                weight:      isSel ? 2.5 : isOpen ? 1.5 : 1,
                dashArray:   isOpen ? null : '4 3',
              }}
              eventHandlers={{ click: () => selectEvent(ev.id) }}
            >
              <Popup maxWidth={280}>
                <div style={{ fontFamily: 'inherit', minWidth: 220 }}>
                  <div style={{ marginBottom: 8, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
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
                  <table style={{ fontSize: 12, color: 'var(--text-secondary)',
                                  borderCollapse: 'collapse', width: '100%' }}>
                    <tbody>
                      <PopupRow label="Date"   value={(ev.latest_date || '--').slice(0,10)} />
                      {ev.closed && <PopupRow label="Closed" value={ev.closed.slice(0,10)} />}
                      {ev.magnitude && (
                        <PopupRow label="Magnitude"
                          value={ev.magnitude.value + ' ' + (ev.magnitude.unit || '')} />
                      )}
                      <PopupRow label="Country"
                        value={(COUNTRY_BBOX[assignCountry(ev.coords) || ''] || {}).name || '--'} />
                      <PopupRow label="Coords"
                        value={ev.coords[1].toFixed(2) + ', ' + ev.coords[0].toFixed(2)} />
                    </tbody>
                  </table>
                  {ev.sources && ev.sources.length > 0 && (
                    <div style={{ marginTop: 8 }}>
                      <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Source: </span>
                      {ev.sources.map((s, i) => (
                        <a key={i} href={s.url} target="_blank" rel="noreferrer"
                           style={{ fontSize: 11, color: '#378ADD', marginRight: 6 }}>
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
      <td style={{ color: 'var(--text-muted)', paddingRight: 10,
                   paddingBottom: 3, whiteSpace: 'nowrap' }}>{label}</td>
      <td style={{ color: 'var(--text-secondary)', paddingBottom: 3 }}>{value}</td>
    </tr>
  )
}

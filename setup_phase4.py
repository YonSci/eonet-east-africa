"""
setup_phase4.py
---------------
Phase 4: Country choropleth, duration histogram, category click-to-filter,
GeoJSON export, enhanced stat cards.

Run from the eonet-east-africa project root:
    python setup_phase4.py

Files updated:
    frontend/src/components/MapPanel.jsx       -- choropleth toggle + country heatmap
    frontend/src/components/AnalyticsPanel.jsx -- duration chart, click-to-filter, GeoJSON export
    frontend/src/components/StatCards.jsx      -- most active category, open rate
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
# MapPanel.jsx -- choropleth support
# =============================================================================
FILES["src/components/MapPanel.jsx"] = r"""import React, { useEffect, useState, useCallback } from 'react'
import {
  MapContainer, TileLayer, CircleMarker, Popup,
  GeoJSON, Rectangle, useMap,
} from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import useAppStore, { CATEGORIES } from '../store/useAppStore.js'
import { useEvents } from '../api/queries.js'

// -- ICPAC region --------------------------------------------------------------
const ICPAC_CENTER   = [6.5, 38.0]
const ICPAC_ZOOM     = 5
const ICPAC_MIN_ZOOM = 4
const ICPAC_MAX_ZOOM = 10
const MAX_BOUNDS     = [[-16.0, 18.0], [26.0, 56.0]]
const REGION_BOUNDS  = [[-12.0, 22.0], [23.0, 52.0]]

// -- Country data --------------------------------------------------------------
const ICPAC_ISO2 = ['DJ','ER','ET','KE','RW','SO','SS','SD','TZ','UG','BI']

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

  // Fetch ICPAC country boundaries once on mount
  useEffect(() => {
    Promise.allSettled(
      ICPAC_ISO2.map((iso) =>
        fetch(GEO_BASE + '/' + iso + '.geo.json', { signal: AbortSignal.timeout(7000) })
          .then((r) => (r.ok ? r.json() : null))
          .catch(() => null)
      )
    ).then((results) => {
      const features = results
        .filter((r, i) => r.status === 'fulfilled' && r.value)
        .flatMap((r, i) => {
          const iso = ICPAC_ISO2[
            results.slice(0, results.indexOf(r)).filter(x => x.status === 'fulfilled').length +
            (r.status === 'fulfilled' ? results.filter((x,j) => j <= results.indexOf(r) && x.status === 'fulfilled').length - 1 : 0)
          ] || ''
          const d = r.value
          const raw = d && d.type === 'FeatureCollection' ? d.features : (d ? [d] : [])
          return raw.map((f) => ({ ...f, properties: { ...(f.properties || {}), iso2: ICPAC_ISO2[results.indexOf(r)] } }))
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
        ICPAC Greater Horn of Africa
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
        center={ICPAC_CENTER} zoom={ICPAC_ZOOM}
        minZoom={ICPAC_MIN_ZOOM} maxZoom={ICPAC_MAX_ZOOM}
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
"""

# =============================================================================
# AnalyticsPanel.jsx -- Phase 4: duration chart, click-to-filter, GeoJSON export
# =============================================================================
FILES["src/components/AnalyticsPanel.jsx"] = r"""import React, { useMemo } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  AreaChart, Area, CartesianGrid, Cell,
  PieChart, Pie,
} from 'recharts'
import useAppStore, { CATEGORIES } from '../store/useAppStore.js'
import { useEvents, useSummary } from '../api/queries.js'

// -- Country bbox (same as MapPanel) ------------------------------------------
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
  const lon = coords[0]; const lat = coords[1]
  for (const [iso, b] of Object.entries(COUNTRY_BBOX)) {
    if (lon >= b.minLon && lon <= b.maxLon && lat >= b.minLat && lat <= b.maxLat) return iso
  }
  return null
}

function getCatColor(cat) { return (CATEGORIES[cat] || {}).color || '#484f58' }

function shortMonth(ym) {
  if (!ym) return ''
  const p = ym.split('-')
  if (p.length < 2) return ym
  const M = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
  return M[parseInt(p[1], 10) - 1] + ' ' + p[0].slice(2)
}

function binByMonth(events) {
  const bins = {}
  events.forEach((ev) => {
    const m = (ev.latest_date || '').slice(0, 7)
    if (m) bins[m] = (bins[m] || 0) + 1
  })
  return Object.entries(bins).sort(([a],[b]) => a.localeCompare(b))
    .map(([month, count]) => ({ month, count }))
}

function durationDays(ev) {
  if (!ev.closed || !ev.latest_date) return null
  const start = new Date(ev.latest_date)
  const end   = new Date(ev.closed)
  return Math.max(0, Math.round((end - start) / 86400000))
}

// -- Tooltip style -------------------------------------------------------------
const TT_STYLE = {
  background: 'var(--bg-elevated)',
  border: '1px solid var(--border-primary)',
  borderRadius: 6, fontSize: 12,
  color: 'var(--text-primary)',
}

// -- GeoJSON export ------------------------------------------------------------
function exportGeoJSON(events) {
  const fc = {
    type: 'FeatureCollection',
    name: 'EONET East Africa Events',
    crs: { type: 'name', properties: { name: 'urn:ogc:def:crs:OGC:1.3:CRS84' } },
    features: events
      .filter((ev) => ev.coords)
      .map((ev) => ({
        type: 'Feature',
        geometry: { type: 'Point', coordinates: ev.coords },
        properties: {
          id:              ev.id,
          title:           ev.title,
          category:        ev.category,
          status:          ev.status,
          date:            (ev.latest_date || '').slice(0, 10),
          closed:          ev.closed ? ev.closed.slice(0, 10) : null,
          magnitude_value: ev.magnitude ? ev.magnitude.value : null,
          magnitude_unit:  ev.magnitude ? ev.magnitude.unit  : null,
          country:         (COUNTRY_BBOX[assignCountry(ev.coords) || ''] || {}).name || null,
          source:          (ev.sources && ev.sources[0]) ? ev.sources[0].id : null,
        },
      })),
  }
  const blob = new Blob([JSON.stringify(fc, null, 2)], { type: 'application/json' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href = url; a.download = 'eonet_ea_events.geojson'; a.click()
  URL.revokeObjectURL(url)
}

function exportCSV(events) {
  const header = ['ID','Title','Category','Status','Date','Closed','Magnitude','Unit','Country','Lat','Lon']
  const rows   = events.map((ev) => [
    ev.id, '"' + (ev.title || '').replace(/"/g, '""') + '"',
    ev.category, ev.status,
    (ev.latest_date || '').slice(0,10),
    ev.closed ? ev.closed.slice(0,10) : '',
    ev.magnitude ? ev.magnitude.value : '',
    ev.magnitude ? (ev.magnitude.unit || '') : '',
    (COUNTRY_BBOX[assignCountry(ev.coords) || ''] || {}).name || '',
    ev.coords ? ev.coords[1] : '', ev.coords ? ev.coords[0] : '',
  ])
  const csv  = [header, ...rows].map((r) => r.join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href = url; a.download = 'eonet_ea_events.csv'; a.click()
  URL.revokeObjectURL(url)
}

// -- Sub-components ------------------------------------------------------------

function SectionTitle({ children }) {
  return (
    <p style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.07em',
                textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 12 }}>
      {children}
    </p>
  )
}

function Empty() {
  return <p style={{ fontSize: 12, color: 'var(--text-muted)', textAlign: 'center', padding: '20px 0' }}>No data</p>
}

// Category bar chart -- bars are clickable to toggle filter
function CategoryChart({ events }) {
  const { toggleCategory, activeCategories } = useAppStore()

  const data = useMemo(() => {
    const counts = {}
    events.forEach((ev) => { counts[ev.category] = (counts[ev.category] || 0) + 1 })
    return Object.entries(counts)
      .sort(([,a],[,b]) => b - a)
      .map(([cat, count]) => ({
        cat, label: (CATEGORIES[cat] || {}).label || cat,
        count, color: getCatColor(cat),
        active: activeCategories.includes(cat),
      }))
  }, [events, activeCategories])

  if (!data.length) return <Empty />

  return (
    <div>
      <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 8 }}>
        Click a bar to toggle that category on the map
      </p>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} layout="vertical"
          margin={{ top: 0, right: 20, bottom: 0, left: 100 }}>
          <XAxis type="number" allowDecimals={false}
            tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
            axisLine={{ stroke: 'var(--border-primary)' }} tickLine={false} />
          <YAxis type="category" dataKey="label" width={95}
            tick={{ fontSize: 12, fill: 'var(--text-secondary)' }}
            axisLine={false} tickLine={false} />
          <Tooltip contentStyle={TT_STYLE}
            labelStyle={{ color: 'var(--text-primary)', fontWeight: 500 }}
            formatter={(value) => [value, 'Events']} />
          <Bar dataKey="count" radius={[0,3,3,0]} maxBarSize={18}
            onClick={(d) => toggleCategory(d.cat)}
            style={{ cursor: 'pointer' }}>
            {data.map((entry) => (
              <Cell key={entry.cat}
                fill={entry.color}
                fillOpacity={entry.active ? 1 : 0.3}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

// Monthly timeline
function TimelineChart({ events }) {
  const data = useMemo(() => binByMonth(events), [events])
  if (!data.length) return <Empty />
  return (
    <ResponsiveContainer width="100%" height={150}>
      <AreaChart data={data} margin={{ top: 4, right: 10, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="ag" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%"   stopColor="#1D9E75" stopOpacity={0.35} />
            <stop offset="100%" stopColor="#1D9E75" stopOpacity={0.0}  />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="var(--border-primary)" strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="month" tickFormatter={shortMonth}
          tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
          axisLine={{ stroke: 'var(--border-primary)' }} tickLine={false} />
        <YAxis allowDecimals={false}
          tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
          axisLine={false} tickLine={false} width={24} />
        <Tooltip contentStyle={TT_STYLE} labelFormatter={shortMonth}
          formatter={(value) => [value, 'Events']} />
        <Area type="monotone" dataKey="count" stroke="#1D9E75"
          strokeWidth={2} fill="url(#ag)" />
      </AreaChart>
    </ResponsiveContainer>
  )
}

// Duration histogram for closed events
function DurationChart({ events }) {
  const data = useMemo(() => {
    const bins = [
      { label: '< 1 day',   min: 0,  max: 1,   count: 0, color: '#378ADD' },
      { label: '1-7 days',  min: 1,  max: 8,   count: 0, color: '#1D9E75' },
      { label: '8-30 days', min: 8,  max: 31,  count: 0, color: '#BA7517' },
      { label: '> 30 days', min: 31, max: 9999, count: 0, color: '#E8593C' },
    ]
    events
      .filter((ev) => ev.status === 'closed')
      .forEach((ev) => {
        const d = durationDays(ev)
        if (d === null) return
        const bin = bins.find((b) => d >= b.min && d < b.max)
        if (bin) bin.count += 1
      })
    return bins
  }, [events])

  const closedCount = events.filter((ev) => ev.status === 'closed').length

  if (closedCount === 0) return (
    <p style={{ fontSize: 12, color: 'var(--text-muted)', textAlign: 'center', padding: '20px 0' }}>
      No closed events in current filter
    </p>
  )

  return (
    <div>
      <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 10 }}>
        How long closed events lasted ({closedCount} events)
      </p>
      <ResponsiveContainer width="100%" height={130}>
        <BarChart data={data} margin={{ top: 4, right: 10, bottom: 0, left: 0 }}>
          <XAxis dataKey="label" tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
            axisLine={{ stroke: 'var(--border-primary)' }} tickLine={false} />
          <YAxis allowDecimals={false}
            tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
            axisLine={false} tickLine={false} width={24} />
          <Tooltip contentStyle={TT_STYLE}
            formatter={(value) => [value, 'Closed events']} />
          <Bar dataKey="count" radius={[3,3,0,0]} maxBarSize={40}>
            {data.map((entry, i) => <Cell key={i} fill={entry.color} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

// Open vs closed donut
function StatusDonut({ summary }) {
  const open   = summary?.open   || 0
  const closed = summary?.closed || 0
  const total  = open + closed || 1
  const data   = [
    { name: 'Open',   value: open,   color: '#1D9E75' },
    { name: 'Closed', value: closed, color: '#484f58' },
  ]
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
      <PieChart width={90} height={90}>
        <Pie data={data} cx={40} cy={40} innerRadius={24} outerRadius={40}
          dataKey="value" paddingAngle={2} startAngle={90} endAngle={-270}>
          {data.map((entry, i) => <Cell key={i} fill={entry.color} />)}
        </Pie>
        <Tooltip contentStyle={TT_STYLE} formatter={(v, n) => [v, n]} />
      </PieChart>
      <div>
        {data.map((d) => (
          <div key={d.name} style={{ display: 'flex', alignItems: 'center',
                                     gap: 8, marginBottom: 8 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%',
                           background: d.color, flexShrink: 0 }} />
            <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{d.name}</span>
            <span style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>
              {d.value}
            </span>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
              ({Math.round((d.value / total) * 100)}%)
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

// Country event table
function CountryTable({ events }) {
  const rows = useMemo(() => {
    const counts = {}
    events.forEach((ev) => {
      const iso = assignCountry(ev.coords)
      if (!iso) return
      const name = (COUNTRY_BBOX[iso] || {}).name || iso
      if (!counts[iso]) counts[iso] = { name, open: 0, closed: 0, total: 0 }
      counts[iso].total += 1
      if (ev.status === 'open') counts[iso].open   += 1
      else                      counts[iso].closed += 1
    })
    return Object.values(counts).sort((a, b) => b.total - a.total)
  }, [events])

  if (!rows.length) return <Empty />

  const maxTotal = rows[0]?.total || 1

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {rows.map((r) => (
        <div key={r.name}>
          <div style={{ display: 'flex', justifyContent: 'space-between',
                        fontSize: 12, marginBottom: 3 }}>
            <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>{r.name}</span>
            <div style={{ display: 'flex', gap: 10 }}>
              <span style={{ color: '#1D9E75', fontSize: 11 }}>{r.open} open</span>
              <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>{r.closed} closed</span>
              <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{r.total}</span>
            </div>
          </div>
          <div style={{ height: 5, background: 'var(--bg-elevated)', borderRadius: 3 }}>
            <div style={{
              height: '100%', borderRadius: 3,
              width: Math.round((r.total / maxTotal) * 100) + '%',
              background: 'linear-gradient(90deg, #1D9E75, #BA7517)',
              transition: 'width 0.4s',
            }} />
          </div>
        </div>
      ))}
    </div>
  )
}

// Source breakdown
function SourceList({ events }) {
  const sources = useMemo(() => {
    const c = {}
    events.forEach((ev) => {
      (ev.sources || []).forEach((s) => {
        if (!c[s.id]) c[s.id] = { id: s.id, url: s.url, count: 0 }
        c[s.id].count += 1
      })
    })
    return Object.values(c).sort((a, b) => b.count - a.count).slice(0, 5)
  }, [events])

  if (!sources.length) return <Empty />
  const max = sources[0]?.count || 1

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {sources.map((s) => (
        <div key={s.id}>
          <div style={{ display: 'flex', justifyContent: 'space-between',
                        marginBottom: 3, fontSize: 12 }}>
            <a href={s.url} target="_blank" rel="noreferrer"
               style={{ color: '#378ADD', textDecoration: 'none' }}>{s.id}</a>
            <span style={{ color: 'var(--text-muted)' }}>{s.count}</span>
          </div>
          <div style={{ height: 4, background: 'var(--bg-elevated)', borderRadius: 2 }}>
            <div style={{
              height: '100%', width: Math.round((s.count / max) * 100) + '%',
              background: '#378ADD', borderRadius: 2, transition: 'width 0.4s',
            }} />
          </div>
        </div>
      ))}
    </div>
  )
}

// -- Main AnalyticsPanel -------------------------------------------------------
export default function AnalyticsPanel() {
  const { activeCategories, activeStatus } = useAppStore()
  const { data: rawEvents = [] } = useEvents()
  const { data: summary }        = useSummary()

  const events = rawEvents.filter((ev) => {
    if (!activeCategories.includes(ev.category)) return false
    if (activeStatus === 'open'   && ev.status !== 'open')   return false
    if (activeStatus === 'closed' && ev.status !== 'closed') return false
    return true
  })

  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: 14,
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: 14, alignContent: 'start' }}>

      {/* Category bar chart -- click-to-filter */}
      <Card title="Events by category (click to filter map)" style={{ gridColumn: '1 / 2' }}>
        <CategoryChart events={events} />
      </Card>

      {/* Status donut + source list */}
      <Card title="Status breakdown" style={{ gridColumn: '2 / 3' }}>
        <StatusDonut summary={summary} />
        <div style={{ marginTop: 16 }}>
          <SectionTitle>Data sources</SectionTitle>
          <SourceList events={events} />
        </div>
      </Card>

      {/* Monthly timeline */}
      <Card title="Events over time (monthly)" style={{ gridColumn: '1 / -1' }}>
        <TimelineChart events={events} />
      </Card>

      {/* Duration histogram */}
      <Card title="Closed event duration" style={{ gridColumn: '1 / 2' }}>
        <DurationChart events={events} />
      </Card>

      {/* Country table */}
      <Card title="Events by country" style={{ gridColumn: '2 / 3' }}>
        <CountryTable events={events} />
      </Card>

      {/* Export */}
      <Card title="Export data" style={{ gridColumn: '1 / -1' }}>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <ExportBtn
            label="Download GeoJSON"
            sub={events.length + ' features'}
            color="#1D9E75"
            onClick={() => exportGeoJSON(events)}
          />
          <ExportBtn
            label="Download CSV"
            sub={events.length + ' rows'}
            color="#378ADD"
            onClick={() => exportCSV(events)}
          />
        </div>
        <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 10 }}>
          Exports apply your current filters (category, status, lookback window).
          GeoJSON is compatible with QGIS, ArcGIS, and Python geopandas.
        </p>
      </Card>

    </div>
  )
}

function Card({ title, children, style }) {
  return (
    <div style={{ background: 'var(--bg-surface)',
                  border: '1px solid var(--border-primary)',
                  borderRadius: 'var(--radius-lg)',
                  padding: '14px 16px', ...style }}>
      <SectionTitle>{title}</SectionTitle>
      {children}
    </div>
  )
}

function ExportBtn({ label, sub, color, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '10px 18px', borderRadius: 8, cursor: 'pointer',
        border: '1px solid ' + color + '55',
        background: color + '18',
        display: 'flex', flexDirection: 'column', gap: 2,
        textAlign: 'left',
      }}
    >
      <span style={{ fontSize: 13, fontWeight: 600, color: color }}>{label}</span>
      <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{sub}</span>
    </button>
  )
}
"""

# =============================================================================
# StatCards.jsx -- enhanced with most-active category + open rate
# =============================================================================
FILES["src/components/StatCards.jsx"] = r"""import React from 'react'
import { useSummary } from '../api/queries.js'
import { CATEGORIES } from '../store/useAppStore.js'

function getCatColor(cat) { return (CATEGORIES[cat] || {}).color || '#484f58' }

export default function StatCards() {
  const { data: s, isLoading } = useSummary()

  const total      = s?.total  ?? 0
  const open       = s?.open   ?? 0
  const closed     = s?.closed ?? 0
  const byCat      = s?.by_category || {}
  const openRate   = total > 0 ? Math.round((open / total) * 100) : 0

  const topCat     = Object.entries(byCat).sort(([,a],[,b]) => b - a)[0]
  const topCatId   = topCat ? topCat[0] : null
  const topCatN    = topCat ? topCat[1] : 0
  const topCatLabel= topCatId ? ((CATEGORIES[topCatId] || {}).label || topCatId) : '--'
  const topCatColor= topCatId ? getCatColor(topCatId) : 'var(--text-muted)'

  const cards = [
    {
      value:  isLoading ? '...' : total,
      label:  'Total events',
      sub:    'in ICPAC GHA region',
      color:  'var(--accent-blue)',
      icon:   'globe',
    },
    {
      value:  isLoading ? '...' : open,
      label:  'Open',
      sub:    openRate + '% of total',
      color:  '#1D9E75',
      icon:   'circle',
      bar:    openRate,
      barColor: '#1D9E75',
    },
    {
      value:  isLoading ? '...' : closed,
      label:  'Closed',
      sub:    (100 - openRate) + '% resolved',
      color:  'var(--text-muted)',
      icon:   'check',
    },
    {
      value:  isLoading ? '...' : (topCatId ? topCatN : '--'),
      label:  'Top category',
      sub:    topCatLabel,
      color:  topCatColor,
      icon:   'fire',
      accent: topCatColor,
    },
  ]

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)',
                  gap: 10, padding: '10px 14px 0', flexShrink: 0 }}>
      {cards.map((c, i) => (
        <div key={i} style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-primary)',
          borderTop: '2px solid ' + c.color,
          borderRadius: 'var(--radius-md)',
          padding: '10px 14px',
          position: 'relative',
          overflow: 'hidden',
        }}>
          {/* Background accent strip */}
          <div style={{
            position: 'absolute', top: 0, right: 0, bottom: 0, width: 3,
            background: c.color, opacity: 0.2,
          }} />

          <div style={{ fontSize: 24, fontWeight: 600, color: c.color,
                        lineHeight: 1, marginBottom: 4 }}>
            {c.value}
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-primary)', fontWeight: 500,
                        marginBottom: 2 }}>
            {c.label}
          </div>
          <div style={{ fontSize: 11, color: c.accent || 'var(--text-muted)' }}>
            {c.sub}
          </div>

          {/* Progress bar for open rate */}
          {c.bar != null && (
            <div style={{ marginTop: 8, height: 3,
                          background: 'var(--bg-elevated)', borderRadius: 2 }}>
              <div style={{
                height: '100%', borderRadius: 2,
                width: c.bar + '%', background: c.barColor,
                transition: 'width 0.5s',
              }} />
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
"""

# =============================================================================
# Builder
# =============================================================================
def build(root: Path):
    hdr(f"Setting up Phase 4 in: {root}")
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
    print("  Restart Vite:")
    print("    cd frontend && npm run dev")
    print()
    print("  New in Phase 4:")
    print("    - Choropleth country heatmap (toggle 'Heatmap' button on map)")
    print("    - Click any bar in Analytics -> category chart to filter map")
    print("    - Duration histogram for closed events")
    print("    - Country event counts table with open/closed split")
    print("    - GeoJSON + CSV export from Analytics tab")
    print("    - Enhanced stat cards with top category + open rate bar")
    print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phase 4 -- choropleth + analytics")
    parser.add_argument("--path", default=".", help="Project root (default: current dir)")
    args = parser.parse_args()
    root = Path(args.path).resolve()
    if not (root / "backend").exists():
        print(f"WARNING: {root} may not be the project root. Continue? [y/N] ", end="")
        if input().strip().lower() != "y":
            sys.exit(0)
    build(root)

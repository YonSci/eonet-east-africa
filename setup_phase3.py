"""
setup_phase3.py
---------------
Updates Phase 2 map to ICPAC East Africa region focus and
adds Phase 3 analytics panel with Recharts charts.

Run from the eonet-east-africa project root:
    python setup_phase3.py

Files created / overwritten:
    frontend/src/components/MapPanel.jsx      -- ICPAC bounds + country borders
    frontend/src/components/AnalyticsPanel.jsx -- Phase 3 charts
    frontend/src/App.jsx                      -- Map / Analytics tabs
    frontend/index.html                       -- clean up duplicate CSS import
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
# index.html  --  remove duplicate leaflet CSS (npm import handles it)
# =============================================================================
FILES["index.html"] = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>EONET East Africa -- Natural Events Dashboard</title>
    <link rel="icon" type="image/svg+xml"
      href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>earth</text></svg>" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
"""

# =============================================================================
# MapPanel.jsx  --  ICPAC GHA focus + country boundary layer
# =============================================================================
FILES["src/components/MapPanel.jsx"] = """import React, { useEffect, useState } from 'react'
import {
  MapContainer, TileLayer, CircleMarker, Popup,
  GeoJSON, Rectangle, useMap,
} from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import useAppStore, { CATEGORIES } from '../store/useAppStore.js'
import { useEvents } from '../api/queries.js'

// ------------------------------------------------------------------
// ICPAC Greater Horn of Africa region
// Countries: Sudan, South Sudan, Ethiopia, Eritrea, Djibouti,
//            Somalia, Kenya, Uganda, Tanzania, Rwanda, Burundi
// ------------------------------------------------------------------
const ICPAC_CENTER  = [6.5, 38.0]
const ICPAC_ZOOM    = 5
const ICPAC_MIN_ZOOM = 4
const ICPAC_MAX_ZOOM = 10
// maxBounds adds ~2 deg padding so the user cannot pan outside the region
const MAX_BOUNDS    = [[-16.0, 18.0], [26.0, 56.0]]
// Tight bounds used for initial fitBounds
const REGION_BOUNDS = [[-12.0, 22.0], [23.0, 52.0]]

// ISO-2 codes for ICPAC GHA countries
const ICPAC_ISO2 = ['DJ','ER','ET','KE','RW','SO','SS','SD','TZ','UG','BI']
const GEO_BASE   = 'https://raw.githubusercontent.com/johan/world.geo.json/master/countries'

const TILE_DARK  = 'https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png'
const TILE_LABELS= 'https://{s}.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}{r}.png'
const TILE_LIGHT = 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'
const ATTR       = '(c) OpenStreetMap contributors, (c) CARTO | NASA EONET v3'

// ------------------------------------------------------------------
// Helper: category colour
// ------------------------------------------------------------------
function getCatColor(cat) {
  return (CATEGORIES[cat] || {}).color || '#484f58'
}

// ------------------------------------------------------------------
// FlyTo -- reacts to selectedEventId changes
// ------------------------------------------------------------------
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

// ------------------------------------------------------------------
// FitRegion -- sets initial bounds on mount
// ------------------------------------------------------------------
function FitRegion() {
  const map = useMap()
  useEffect(() => {
    map.fitBounds(REGION_BOUNDS, { padding: [10, 10] })
  }, [map])
  return null
}

// ------------------------------------------------------------------
// CountryBorders -- fetches and renders ICPAC country boundaries
// ------------------------------------------------------------------
function CountryBorders({ lightMode }) {
  const [geo, setGeo] = useState(null)

  useEffect(() => {
    Promise.allSettled(
      ICPAC_ISO2.map((iso) =>
        fetch(GEO_BASE + '/' + iso + '.geo.json', { signal: AbortSignal.timeout(6000) })
          .then((r) => (r.ok ? r.json() : null))
          .catch(() => null)
      )
    ).then((results) => {
      const features = results
        .filter((r) => r.status === 'fulfilled' && r.value)
        .flatMap((r) => {
          const d = r.value
          if (d && d.type === 'FeatureCollection') return d.features
          if (d && d.type === 'Feature') return [d]
          return []
        })
      if (features.length > 0) {
        setGeo({ type: 'FeatureCollection', features })
      }
    })
  }, [])

  if (!geo) return null

  return (
    <GeoJSON
      key={lightMode ? 'light' : 'dark'}
      data={geo}
      style={() => ({
        color:       lightMode ? '#94a3b8' : '#4a5568',
        weight:      1.2,
        fillColor:   lightMode ? '#e2e8f0' : '#1e293b',
        fillOpacity: lightMode ? 0.15 : 0.10,
        dashArray:   null,
      })}
    />
  )
}

// ------------------------------------------------------------------
// OutsideMask -- dims the area outside the ICPAC bbox
// ------------------------------------------------------------------
function OutsideMask() {
  // Cover west, east, north, south strips outside the region
  const strips = [
    [[-90, -180], [90,   22.0]],  // west of region
    [[-90,  52.0], [90,  180]],   // east of region
    [[ 23.0, 22.0], [90,  52.0]], // north of region
    [[-90,  22.0], [-12.0, 52.0]],// south of region
  ]
  return strips.map((b, i) => (
    <Rectangle
      key={i}
      bounds={b}
      pathOptions={{
        color:       'transparent',
        fillColor:   '#000',
        fillOpacity: 0.45,
        weight:      0,
      }}
    />
  ))
}

// ------------------------------------------------------------------
// Main MapPanel
// ------------------------------------------------------------------
export default function MapPanel({ height }) {
  const {
    activeCategories, activeStatus,
    selectedEventId, selectEvent, lightMode,
  } = useAppStore()

  const { data: rawEvents = [], isLoading } = useEvents()

  // Apply local filters
  const events = rawEvents.filter((ev) => {
    if (!activeCategories.includes(ev.category)) return false
    if (activeStatus === 'open'   && ev.status !== 'open')   return false
    if (activeStatus === 'closed' && ev.status !== 'closed') return false
    return ev.coords != null
  })

  return (
    <div style={{
      flex: 1,
      position: 'relative',
      background: '#0d1117',
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

      {/* Region label */}
      <div style={{
        position: 'absolute', top: 10, left: 10, zIndex: 400,
        background: 'rgba(13,17,23,0.75)',
        border: '1px solid var(--border-primary)',
        borderRadius: 6, padding: '4px 10px',
        fontSize: 11, fontWeight: 600,
        color: 'var(--accent-green)',
        letterSpacing: '0.05em',
        pointerEvents: 'none',
      }}>
        ICPAC Greater Horn of Africa
      </div>

      {/* Event count */}
      <div style={{
        position: 'absolute', top: 10, right: 10, zIndex: 400,
        background: 'rgba(13,17,23,0.75)',
        border: '1px solid var(--border-primary)',
        borderRadius: 6, padding: '4px 10px',
        fontSize: 12, color: 'var(--text-secondary)',
        pointerEvents: 'none',
      }}>
        {events.length} event{events.length !== 1 ? 's' : ''} shown
      </div>

      {/* Legend */}
      <div style={{
        position: 'absolute', bottom: 30, left: 10, zIndex: 400,
        background: 'rgba(13,17,23,0.80)',
        border: '1px solid var(--border-primary)',
        borderRadius: 6, padding: '8px 10px',
        pointerEvents: 'none',
      }}>
        <div style={{ fontSize: 10, color: 'var(--text-muted)',
                      textTransform: 'uppercase', letterSpacing: '0.06em',
                      marginBottom: 6, fontWeight: 600 }}>
          Legend
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <LegendRow color="#1D9E75" label="Open event"   dash={false} />
          <LegendRow color="#6e7681" label="Closed event" dash={true}  />
        </div>
      </div>

      <MapContainer
        center={ICPAC_CENTER}
        zoom={ICPAC_ZOOM}
        minZoom={ICPAC_MIN_ZOOM}
        maxZoom={ICPAC_MAX_ZOOM}
        maxBounds={MAX_BOUNDS}
        maxBoundsViscosity={0.85}
        style={{ width: '100%', height: '100%' }}
        zoomControl={true}
      >
        {/* Base tiles -- no labels so we can add our own label layer on top */}
        {lightMode ? (
          <TileLayer url={TILE_LIGHT} attribution={ATTR} />
        ) : (
          <>
            <TileLayer url={TILE_DARK}   attribution={ATTR} />
            <TileLayer url={TILE_LABELS} />
          </>
        )}

        {/* Dim everything outside ICPAC bbox */}
        <OutsideMask />

        {/* Country boundary lines */}
        <CountryBorders lightMode={lightMode} />

        {/* Helpers */}
        <FitRegion />
        <FlyTo events={events} selectedId={selectedEventId} />

        {/* Event markers */}
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
                color:       isSel ? '#fff'       : color,
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
                    <span style={{
                      fontSize: 11, fontWeight: 500,
                      padding: '2px 8px', borderRadius: 100,
                      background: color + '33', color: color,
                      border: '1px solid ' + color + '55',
                    }}>
                      {cat.label || ev.category}
                    </span>
                    <span style={{
                      fontSize: 11, fontWeight: 600,
                      color: isOpen ? '#1D9E75' : '#6e7681',
                    }}>
                      {isOpen ? 'OPEN' : 'CLOSED'}
                    </span>
                  </div>

                  <p style={{ fontWeight: 600, fontSize: 13,
                              color: 'var(--text-primary)', lineHeight: 1.4,
                              marginBottom: 8 }}>
                    {ev.title}
                  </p>

                  <table style={{ fontSize: 12, color: 'var(--text-secondary)',
                                  borderCollapse: 'collapse', width: '100%' }}>
                    <tbody>
                      <PopupRow label="Date"   value={ev.latest_date?.slice(0,10) || '--'} />
                      {ev.closed && (
                        <PopupRow label="Closed" value={ev.closed.slice(0,10)} />
                      )}
                      {ev.magnitude && (
                        <PopupRow label="Magnitude"
                          value={ev.magnitude.value + ' ' + (ev.magnitude.unit || '')} />
                      )}
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
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <svg width="16" height="12" viewBox="0 0 16 12">
        <circle cx="8" cy="6" r="5"
          fill={color}
          fillOpacity={dash ? 0.4 : 0.85}
          stroke={color}
          strokeWidth={1.5}
          strokeDasharray={dash ? '3 2' : null}
        />
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
# AnalyticsPanel.jsx  --  Phase 3 charts
# =============================================================================
FILES["src/components/AnalyticsPanel.jsx"] = """import React, { useMemo } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  AreaChart, Area, CartesianGrid, Cell, PieChart, Pie,
} from 'recharts'
import useAppStore, { CATEGORIES } from '../store/useAppStore.js'
import { useEvents, useSummary } from '../api/queries.js'

// ------------------------------------------------------------------
// Helpers
// ------------------------------------------------------------------
function getCatColor(cat) {
  return (CATEGORIES[cat] || {}).color || '#484f58'
}

function binByMonth(events) {
  const bins = {}
  events.forEach((ev) => {
    const d = ev.latest_date || ''
    const month = d.slice(0, 7)
    if (month) bins[month] = (bins[month] || 0) + 1
  })
  return Object.entries(bins)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([month, count]) => ({ month, count }))
}

function shortMonth(ym) {
  if (!ym) return ''
  const parts = ym.split('-')
  if (parts.length < 2) return ym
  const months = ['Jan','Feb','Mar','Apr','May','Jun',
                  'Jul','Aug','Sep','Oct','Nov','Dec']
  const idx = parseInt(parts[1], 10) - 1
  return months[idx] + ' ' + parts[0].slice(2)
}

// Custom tooltip style used by all charts
const TT_STYLE = {
  background: 'var(--bg-elevated)',
  border: '1px solid var(--border-primary)',
  borderRadius: 6,
  fontSize: 12,
  color: 'var(--text-primary)',
}

// ------------------------------------------------------------------
// Sub-components
// ------------------------------------------------------------------

function SectionTitle({ children }) {
  return (
    <p style={{
      fontSize: 11, fontWeight: 600, letterSpacing: '0.07em',
      textTransform: 'uppercase', color: 'var(--text-muted)',
      marginBottom: 12,
    }}>
      {children}
    </p>
  )
}

// Events by category -- horizontal bar chart
function CategoryChart({ events }) {
  const data = useMemo(() => {
    const counts = {}
    events.forEach((ev) => {
      counts[ev.category] = (counts[ev.category] || 0) + 1
    })
    return Object.entries(counts)
      .sort(([, a], [, b]) => b - a)
      .map(([cat, count]) => ({
        cat,
        label: (CATEGORIES[cat] || {}).label || cat,
        count,
        color: getCatColor(cat),
      }))
  }, [events])

  if (!data.length) return <Empty />

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} layout="vertical" margin={{ top: 0, right: 20, bottom: 0, left: 100 }}>
        <XAxis
          type="number"
          allowDecimals={false}
          tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
          axisLine={{ stroke: 'var(--border-primary)' }}
          tickLine={false}
        />
        <YAxis
          type="category"
          dataKey="label"
          width={95}
          tick={{ fontSize: 12, fill: 'var(--text-secondary)' }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          contentStyle={TT_STYLE}
          labelStyle={{ color: 'var(--text-primary)', fontWeight: 500 }}
          formatter={(value) => [value, 'Events']}
        />
        <Bar dataKey="count" radius={[0, 3, 3, 0]} maxBarSize={18}>
          {data.map((entry) => (
            <Cell key={entry.cat} fill={entry.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

// Events over time -- monthly area chart
function TimelineChart({ events }) {
  const data = useMemo(() => binByMonth(events), [events])

  if (!data.length) return <Empty />

  return (
    <ResponsiveContainer width="100%" height={160}>
      <AreaChart data={data} margin={{ top: 4, right: 10, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="area-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%"   stopColor="#1D9E75" stopOpacity={0.35} />
            <stop offset="100%" stopColor="#1D9E75" stopOpacity={0.0}  />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="var(--border-primary)" strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="month"
          tickFormatter={shortMonth}
          tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
          axisLine={{ stroke: 'var(--border-primary)' }}
          tickLine={false}
        />
        <YAxis
          allowDecimals={false}
          tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
          axisLine={false}
          tickLine={false}
          width={24}
        />
        <Tooltip
          contentStyle={TT_STYLE}
          labelFormatter={shortMonth}
          formatter={(value) => [value, 'Events']}
        />
        <Area
          type="monotone"
          dataKey="count"
          stroke="#1D9E75"
          strokeWidth={2}
          fill="url(#area-grad)"
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

// Open vs closed donut
function StatusDonut({ summary }) {
  const open   = summary?.open   || 0
  const closed = summary?.closed || 0
  const total  = open + closed || 1

  const data = [
    { name: 'Open',   value: open,   color: '#1D9E75' },
    { name: 'Closed', value: closed, color: '#484f58' },
  ]

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
      <PieChart width={100} height={100}>
        <Pie
          data={data}
          cx={45}
          cy={45}
          innerRadius={28}
          outerRadius={44}
          dataKey="value"
          paddingAngle={2}
          startAngle={90}
          endAngle={-270}
        >
          {data.map((entry, i) => (
            <Cell key={i} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={TT_STYLE}
          formatter={(value, name) => [value, name]}
        />
      </PieChart>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {data.map((d) => (
          <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{
              width: 10, height: 10, borderRadius: '50%',
              background: d.color, flexShrink: 0,
            }} />
            <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
              {d.name}
            </span>
            <span style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)',
                           marginLeft: 4 }}>
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

// Source breakdown list
function SourceList({ events }) {
  const sources = useMemo(() => {
    const counts = {}
    events.forEach((ev) => {
      (ev.sources || []).forEach((s) => {
        counts[s.id] = (counts[s.id] || { id: s.id, url: s.url, count: 0 })
        counts[s.id].count += 1
      })
    })
    return Object.values(counts).sort((a, b) => b.count - a.count).slice(0, 6)
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
               style={{ color: '#378ADD', textDecoration: 'none' }}>
              {s.id}
            </a>
            <span style={{ color: 'var(--text-muted)' }}>{s.count}</span>
          </div>
          <div style={{ height: 4, background: 'var(--bg-elevated)', borderRadius: 2 }}>
            <div style={{
              height: '100%',
              width: Math.round((s.count / max) * 100) + '%',
              background: '#378ADD',
              borderRadius: 2,
              transition: 'width 0.4s',
            }} />
          </div>
        </div>
      ))}
    </div>
  )
}

// Recent events list
function RecentEvents({ events }) {
  const recent = useMemo(() =>
    [...events]
      .sort((a, b) => (b.latest_date || '').localeCompare(a.latest_date || ''))
      .slice(0, 8),
    [events]
  )

  if (!recent.length) return <Empty />

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {recent.map((ev) => {
        const color  = getCatColor(ev.category)
        const isOpen = ev.status === 'open'
        const cat    = CATEGORIES[ev.category] || {}
        return (
          <div key={ev.id} style={{
            display: 'flex', alignItems: 'flex-start', gap: 10,
            padding: '8px 10px',
            background: 'var(--bg-elevated)',
            borderRadius: 6,
            border: '1px solid var(--border-primary)',
            borderLeft: '3px solid ' + color,
          }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <p style={{ fontSize: 12, color: 'var(--text-primary)',
                          fontWeight: 500, marginBottom: 2,
                          overflow: 'hidden', textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap' }}>
                {ev.title}
              </p>
              <div style={{ display: 'flex', gap: 8, fontSize: 11,
                            color: 'var(--text-muted)' }}>
                <span>{cat.label || ev.category}</span>
                <span>|</span>
                <span>{ev.latest_date?.slice(0,10) || '--'}</span>
              </div>
            </div>
            <span style={{
              fontSize: 10, fontWeight: 600, flexShrink: 0,
              padding: '2px 6px', borderRadius: 100,
              background: isOpen ? '#1D9E7522' : 'var(--bg-hover)',
              color:      isOpen ? '#1D9E75'   : 'var(--text-muted)',
              border:     '1px solid ' + (isOpen ? '#1D9E7544' : 'transparent'),
            }}>
              {isOpen ? 'OPEN' : 'CLOSED'}
            </span>
          </div>
        )
      })}
    </div>
  )
}

function Empty() {
  return (
    <p style={{ fontSize: 12, color: 'var(--text-muted)', textAlign: 'center',
                padding: '20px 0' }}>
      No data available
    </p>
  )
}

// ------------------------------------------------------------------
// Main AnalyticsPanel
// ------------------------------------------------------------------
export default function AnalyticsPanel() {
  const { activeCategories, activeStatus } = useAppStore()
  const { data: rawEvents = [] }           = useEvents()
  const { data: summary }                  = useSummary()

  // Apply same filters as map
  const events = rawEvents.filter((ev) => {
    if (!activeCategories.includes(ev.category)) return false
    if (activeStatus === 'open'   && ev.status !== 'open')   return false
    if (activeStatus === 'closed' && ev.status !== 'closed') return false
    return true
  })

  return (
    <div style={{
      flex: 1, overflowY: 'auto',
      padding: '14px',
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gridTemplateRows: 'auto auto auto',
      gap: 14,
      alignContent: 'start',
    }}>

      {/* Events by category */}
      <Card title="Events by category" style={{ gridColumn: '1 / 2' }}>
        <CategoryChart events={events} />
      </Card>

      {/* Open vs closed */}
      <Card title="Open vs closed" style={{ gridColumn: '2 / 3' }}>
        <StatusDonut summary={summary} />
        <div style={{ marginTop: 16 }}>
          <SectionTitle>Data sources</SectionTitle>
          <SourceList events={events} />
        </div>
      </Card>

      {/* Timeline */}
      <Card title="Events over time (monthly)" style={{ gridColumn: '1 / -1' }}>
        <TimelineChart events={events} />
      </Card>

      {/* Recent events */}
      <Card title="Most recent events" style={{ gridColumn: '1 / -1' }}>
        <RecentEvents events={events} />
      </Card>

    </div>
  )
}

function Card({ title, children, style }) {
  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border-primary)',
      borderRadius: 'var(--radius-lg)',
      padding: '14px 16px',
      ...style,
    }}>
      <SectionTitle>{title}</SectionTitle>
      {children}
    </div>
  )
}
"""

# =============================================================================
# App.jsx  --  Map / Analytics tabs
# =============================================================================
FILES["src/App.jsx"] = """import React, { useState } from 'react'
import TopNav          from './components/TopNav.jsx'
import FilterSidebar   from './components/FilterSidebar.jsx'
import StatCards       from './components/StatCards.jsx'
import MapPanel        from './components/MapPanel.jsx'
import EventList       from './components/EventList.jsx'
import AnalyticsPanel  from './components/AnalyticsPanel.jsx'
import useAppStore     from './store/useAppStore.js'

const TABS = [
  { id: 'map',       label: 'Map view' },
  { id: 'analytics', label: 'Analytics' },
]

export default function App() {
  const { sidebarOpen } = useAppStore()
  const [activeTab, setActiveTab] = useState('map')

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      <TopNav />

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Sidebar -- always visible across tabs */}
        {sidebarOpen && <FilterSidebar />}

        {/* Main area */}
        <main style={{ flex: 1, display: 'flex', flexDirection: 'column',
                       overflow: 'hidden', minWidth: 0 }}>

          {/* Stat cards + tab bar */}
          <StatCards />

          {/* Tab bar */}
          <div style={{
            display: 'flex', alignItems: 'center',
            gap: 2, padding: '8px 14px 0',
            borderBottom: '1px solid var(--border-primary)',
            background: 'var(--bg-base)',
            flexShrink: 0,
          }}>
            {TABS.map((tab) => {
              const active = activeTab === tab.id
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  style={{
                    padding: '6px 14px',
                    fontSize: 13,
                    fontWeight: active ? 600 : 400,
                    color: active ? 'var(--text-primary)' : 'var(--text-secondary)',
                    background: 'transparent',
                    border: 'none',
                    borderBottom: '2px solid',
                    borderBottomColor: active ? 'var(--accent-green)' : 'transparent',
                    cursor: 'pointer',
                    transition: 'all 0.15s',
                    marginBottom: -1,
                  }}
                >
                  {tab.label}
                </button>
              )
            })}
            <div style={{ flex: 1 }} />
            <span style={{ fontSize: 11, color: 'var(--text-muted)',
                           paddingBottom: 6 }}>
              ICPAC GHA Region
            </span>
          </div>

          {/* Tab content */}
          {activeTab === 'map' && (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column',
                          overflow: 'hidden' }}>
              <MapPanel />
              <EventList />
            </div>
          )}

          {activeTab === 'analytics' && (
            <AnalyticsPanel />
          )}

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
    hdr(f"Setting up Phase 3 in: {root}")
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
    print("  Restart the Vite dev server:")
    print("    cd frontend")
    print("    npm run dev")
    print()
    print("  New in Phase 3:")
    print("    - Map restricted to ICPAC GHA region")
    print("    - ICPAC country boundary layer (fetched from GitHub)")
    print("    - Outside-region dim mask")
    print("    - Analytics tab: category bar chart, timeline, donut, recent events")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 3 -- ICPAC map + analytics")
    parser.add_argument("--path", default=".", help="Project root (default: current dir)")
    import argparse
    args   = parser.parse_args()
    root   = Path(args.path).resolve()
    if not (root / "backend").exists():
        print(f"WARNING: {root} may not be the project root. Continue? [y/N] ", end="")
        if input().strip().lower() != "y":
            sys.exit(0)
    build(root)

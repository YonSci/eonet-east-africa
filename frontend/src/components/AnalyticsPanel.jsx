import React, { useMemo } from 'react'
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

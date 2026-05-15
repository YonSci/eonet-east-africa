import React, { useEffect, useState, useCallback } from 'react'
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

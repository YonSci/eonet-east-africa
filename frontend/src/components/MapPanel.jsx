import React, { useEffect, useState, useCallback, useRef } from 'react'
import {
  MapContainer, TileLayer, WMSTileLayer, CircleMarker,
  Popup, GeoJSON, Rectangle, useMap,
} from 'react-leaflet'
import MarkerClusterGroup from 'react-leaflet-cluster'
import 'leaflet/dist/leaflet.css'
import useAppStore, { CATEGORIES, COUNTRY_MAP } from '../store/useAppStore.js'
import { useEvents } from '../api/queries.js'
import NetworkError from './NetworkError.jsx'
import { DistrictLayer } from './DistrictLayer.jsx'
import { COUNTRY_GEO } from '../api/geoData.js'

// -- Region constants -------------------------------------------------------
const ICPAC_CENTER   = [6.5, 38.0]
const MAX_BOUNDS     = [[-18.0, 18.0], [26.0, 56.0]]
const REGION_BOUNDS  = [[-14.0, 22.0], [23.0, 52.0]]

// Country bbox for event assignment
const COUNTRY_BBOX = {
  SD:{ minLat:9,  maxLat:22, minLon:21, maxLon:38 },
  SS:{ minLat:3,  maxLat:12, minLon:24, maxLon:36 },
  ET:{ minLat:3,  maxLat:15, minLon:33, maxLon:48 },
  ER:{ minLat:12, maxLat:18, minLon:36, maxLon:44 },
  DJ:{ minLat:10, maxLat:13, minLon:41, maxLon:44 },
  SO:{ minLat:-2, maxLat:12, minLon:40, maxLon:52 },
  KE:{ minLat:-5, maxLat:5,  minLon:33, maxLon:42 },
  UG:{ minLat:-2, maxLat:4,  minLon:29, maxLon:35 },
  TZ:{ minLat:-12,maxLat:0,  minLon:29, maxLon:41 },
  RW:{ minLat:-3, maxLat:0,  minLon:28, maxLon:31 },
  BI:{ minLat:-5, maxLat:-2, minLon:28, maxLon:31 },
}

export function assignCountry(coords) {
  if (!coords) return null
  const lon = coords[0]; const lat = coords[1]
  for (const [iso, b] of Object.entries(COUNTRY_BBOX)) {
    if (lon >= b.minLon && lon <= b.maxLon &&
        lat >= b.minLat && lat <= b.maxLat) return iso
  }
  return null
}

// -- Tile layers ------------------------------------------------------------
const TILE_LIGHT     = 'https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png'
const TILE_DARK      = 'https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png'
const TILE_LBL_LIGHT = 'https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}{r}.png'
const TILE_LBL_DARK  = 'https://{s}.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}{r}.png'
const ATTR           = '(c) OpenStreetMap contributors, (c) CARTO | NASA EONET v3'
const GIBS_WMS       = 'https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi'

const GIBS_LAYERS = [
  { id: 'MODIS_Terra_CorrectedReflectance_TrueColor', label: 'True colour (Terra)' },
  { id: 'VIIRS_SNPP_CorrectedReflectance_TrueColor',  label: 'True colour (VIIRS)' },
  { id: 'FIRMS_VIIRS_375m_FireAndThermalAnomalies',   label: 'Fire detections'      },
  { id: 'MODIS_Terra_Chlorophyll_A',                  label: 'Chlorophyll (Terra)'  },
]

function todayStr() { return new Date().toISOString().slice(0, 10) }
function getCatColor(cat) { return (CATEGORIES[cat] || {}).color || '#484f58' }

function worldviewURL(ev) {
  if (!ev.coords) return null
  const lon = ev.coords[0]; const lat = ev.coords[1]; const pad = 3
  const date = (ev.latest_date || todayStr()).slice(0, 10)
  return 'https://worldview.earthdata.nasa.gov/?v=' +
    (lon-pad)+','+(lat-pad)+','+(lon+pad)+','+(lat+pad)+'&t='+date
}

// -- Leaflet helpers --------------------------------------------------------
function FitRegion() {
  const map = useMap()
  useEffect(() => {
    map.fitBounds(REGION_BOUNDS, {
      paddingTopLeft: [50, 10],
      paddingBottomRight: [150, 100],
    })
  }, [map])
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
    [[-90,-180],[90,22]], [[-90,52],[90,180]],
    [[23,22],[90,52]], [[-90,22],[-14,52]],
  ]
  return strips.map((b, i) => (
    <Rectangle key={i} bounds={b}
      pathOptions={{ color:'transparent', fillColor:'#000', fillOpacity:0.38, weight:0 }} />
  ))
}

// Country layer using inline GeoJSON -- no network fetch needed
function CountriesLayer({ lightMode, selectedCountry, onCountryClick }) {
  const styleFunc = useCallback((feature) => {
    const iso2     = feature.properties && feature.properties.iso2
    const isActive = iso2 === selectedCountry
    return {
      color:       isActive ? '#1D9E75' : (lightMode ? '#94a3b8' : '#4a5568'),
      weight:      isActive ? 2.5 : 1.2,
      fillColor:   isActive ? '#1D9E75' : (lightMode ? '#e2e8f0' : '#1e293b'),
      fillOpacity: isActive ? 0.22 : 0.10,
      cursor:      'pointer',
    }
  }, [lightMode, selectedCountry])

  const onEachFeature = useCallback((feature, layer) => {
    const iso2 = feature.properties && feature.properties.iso2
    if (!iso2) return
    const name = COUNTRY_MAP[iso2] || iso2
    layer.bindTooltip(name, { sticky: true, className: 'country-tooltip' })
    layer.on('click', () => onCountryClick(iso2))
  }, [onCountryClick])

  const key = 'countries-' + (lightMode ? 'l' : 'd') + '-' + (selectedCountry || 'none')
  return <GeoJSON key={key} data={COUNTRY_GEO} style={styleFunc} onEachFeature={onEachFeature} />
}

// -- Satellite control (fixed position to escape Leaflet z-index) -----------
function SatelliteControl({ satOn, setSatOn, satLayer, setSatLayer, satDate, setSatDate }) {
  const [open, setOpen] = useState(false)
  const btnRef          = useRef(null)
  const [pos, setPos]   = useState({ top: 0, right: 0 })

  function openPanel() {
    if (btnRef.current) {
      const r = btnRef.current.getBoundingClientRect()
      setPos({ top: r.bottom + 6, right: window.innerWidth - r.right })
    }
    setOpen((v) => !v)
  }

  useEffect(() => {
    if (!open) return
    function onDown(e) {
      const panel = document.getElementById('sat-panel')
      if (btnRef.current && !btnRef.current.contains(e.target) &&
          panel && !panel.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onDown)
    return () => document.removeEventListener('mousedown', onDown)
  }, [open])

  return (
    <>
      <button ref={btnRef} onClick={openPanel} style={{
        fontSize:11, padding:'4px 10px', borderRadius:6, border:'1px solid',
        borderColor: satOn ? '#378ADD' : 'var(--border-primary)',
        background:  satOn ? 'rgba(55,138,221,0.15)' : 'rgba(255,255,255,0.92)',
        color:       satOn ? '#185FA5' : 'var(--text-secondary)',
        cursor:'pointer', fontWeight: satOn ? 600 : 400,
        boxShadow:'0 1px 4px rgba(0,0,0,0.12)',
      }}>
        Satellite{satOn ? ' (on)' : ''}
      </button>

      {open && (
        <div id="sat-panel" style={{
          position:'fixed', top:pos.top, right:pos.right, zIndex:99999,
          background:'var(--bg-surface)', border:'1px solid var(--border-primary)',
          borderRadius:10, padding:'14px 16px', minWidth:250,
          boxShadow:'0 8px 28px rgba(0,0,0,0.18)',
        }}>
          <div style={{ fontSize:12, fontWeight:600, color:'var(--text-primary)',
                        marginBottom:12, paddingBottom:8,
                        borderBottom:'1px solid var(--border-muted)' }}>
            NASA GIBS Satellite Layer
          </div>
          {GIBS_LAYERS.map((gl) => (
            <label key={gl.id} style={{ display:'flex', alignItems:'center',
                                        gap:8, marginBottom:8, cursor:'pointer' }}>
              <input type="radio" name="gibs-layer" checked={satLayer === gl.id}
                onChange={() => setSatLayer(gl.id)} style={{ accentColor:'#378ADD' }} />
              <span style={{ fontSize:13, color:'var(--text-secondary)' }}>{gl.label}</span>
            </label>
          ))}
          <div style={{ marginTop:10, paddingTop:10,
                        borderTop:'1px solid var(--border-muted)' }}>
            <div style={{ fontSize:11, fontWeight:500, color:'var(--text-muted)',
                          marginBottom:5 }}>Image date</div>
            <input type="date" value={satDate} max={todayStr()}
              onChange={(e) => setSatDate(e.target.value)}
              style={{ width:'100%', fontSize:12, padding:'5px 8px',
                       border:'1px solid var(--border-primary)', borderRadius:5,
                       background:'var(--bg-elevated)', color:'var(--text-primary)' }} />
          </div>
          <div style={{ marginTop:12, display:'flex', gap:8 }}>
            <button onClick={() => { setSatOn(true); setOpen(false) }}
              style={{ flex:1, padding:'6px', borderRadius:6, fontSize:12,
                       border:'none', background:'#378ADD', color:'#fff',
                       cursor:'pointer', fontWeight:500 }}>Apply</button>
            <button onClick={() => { setSatOn(false); setOpen(false) }}
              style={{ flex:1, padding:'6px', borderRadius:6, fontSize:12,
                       border:'1px solid var(--border-primary)',
                       background:'transparent', color:'var(--text-secondary)',
                       cursor:'pointer' }}>Turn off</button>
          </div>
        </div>
      )}
    </>
  )
}

function LegendRow({ color, label, dash }) {
  return (
    <div style={{ display:'flex', alignItems:'center', gap:6, marginTop:4 }}>
      <svg width="16" height="12" viewBox="0 0 16 12">
        <circle cx="8" cy="6" r="5" fill={color}
          fillOpacity={dash ? 0.4 : 0.85} stroke={color}
          strokeWidth={1.5} strokeDasharray={dash ? '3 2' : null} />
      </svg>
      <span style={{ fontSize:11, color:'var(--text-secondary)' }}>{label}</span>
    </div>
  )
}

function PopupRow({ label, value }) {
  return (
    <tr>
      <td style={{ color:'var(--text-muted)',paddingRight:10,paddingBottom:3,
                   whiteSpace:'nowrap',fontSize:12 }}>{label}</td>
      <td style={{ color:'var(--text-secondary)',paddingBottom:3,fontSize:12 }}>{value}</td>
    </tr>
  )
}

// -- Main MapPanel ----------------------------------------------------------
export default function MapPanel({ height }) {
  const {
    activeCategories, activeStatus, selectedEventId, selectEvent,
    lightMode, selectedCountry, setSelectedCountry, magFilters,
  } = useAppStore()
  const { data: rawEvents = [], isLoading, isError, error } = useEvents()

  const [satOn,    setSatOn]    = useState(false)
  const [satLayer, setSatLayer] = useState(GIBS_LAYERS[0].id)
  const [satDate,  setSatDate]  = useState(todayStr)
  const [distOn,   setDistOn]   = useState(false)

  // Apply filters
  const events = rawEvents.filter((ev) => {
    if (!activeCategories.includes(ev.category)) return false
    if (activeStatus === 'open'   && ev.status !== 'open')   return false
    if (activeStatus === 'closed' && ev.status !== 'closed') return false
    if (!ev.coords) return false
    if (selectedCountry && assignCountry(ev.coords) !== selectedCountry) return false
    if (magFilters && ev.magnitude) {
      const minMag = magFilters[ev.category] || 0
      if (minMag > 0 && ev.magnitude.value < minMag) return false
    }
    return true
  })

  const countryName = selectedCountry ? (COUNTRY_MAP[selectedCountry] || selectedCountry) : null

  return (
    <div style={{
      flex:1, position:'relative',
      background: lightMode ? '#e8f0e0' : '#0d1117',
      minHeight: 0, overflow:'hidden',
    }}>
      {/* Loading */}
      {isLoading && (
        <div style={{ position:'absolute', inset:0, zIndex:1000,
                      display:'flex', flexDirection:'column',
                      alignItems:'center', justifyContent:'center',
                      background:'rgba(246,248,250,0.75)',
                      fontSize:13, color:'var(--text-secondary)',
                      pointerEvents:'none' }}>
          <div style={{ width:28, height:28, border:'3px solid #1D9E75',
                        borderTopColor:'transparent', borderRadius:'50%',
                        animation:'spin 0.9s linear infinite', marginBottom:8 }} />
          Loading events from NASA EONET...
        </div>
      )}
      {isError && <NetworkError error={error} />}

      {/* Country filter badge -- top left */}
      <div style={{ position:'absolute', top:10, left:10, zIndex:1001,
                    display:'flex', alignItems:'center', gap:6, flexWrap:'wrap' }}>
        {countryName && (
          <div style={{ background:'#E1F5EE', border:'1px solid #1D9E7555',
                        borderRadius:6, padding:'4px 10px', fontSize:11,
                        fontWeight:600, color:'#085041', display:'flex',
                        alignItems:'center', gap:6,
                        boxShadow:'0 1px 4px rgba(0,0,0,0.10)' }}>
            {countryName}
            <button onClick={() => { setSelectedCountry(null); setDistOn(false) }}
              style={{ background:'none', border:'none', cursor:'pointer',
                       color:'#085041', fontSize:14, lineHeight:1, padding:'0 0 0 2px' }}>
              x
            </button>
          </div>
        )}
      </div>

      {/* Top right controls */}
      <div style={{ position:'absolute', top:10, right:10, zIndex:1001,
                    display:'flex', gap:6, alignItems:'flex-start' }}>

        {/* Districts button with tooltip */}
        <div style={{ position:'relative' }} className="districts-btn-wrap">
          <button
            onClick={() => selectedCountry && setDistOn((v) => !v)}
            style={{
              fontSize:11, padding:'4px 10px', borderRadius:6, border:'1px solid',
              borderColor: distOn ? '#7F77DD' : 'var(--border-primary)',
              background: distOn
                ? 'rgba(127,119,221,0.18)'
                : selectedCountry ? 'rgba(255,255,255,0.92)' : 'rgba(240,240,240,0.85)',
              color: distOn ? '#534AB7'
                   : selectedCountry ? 'var(--text-secondary)' : 'var(--text-faint)',
              cursor: selectedCountry ? 'pointer' : 'default',
              fontWeight: distOn ? 600 : 400,
              boxShadow:'0 1px 4px rgba(0,0,0,0.12)',
              display:'flex', alignItems:'center', gap:5,
            }}>
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"
              strokeLinejoin="round" style={{ opacity: selectedCountry ? 1 : 0.4 }}>
              <path d="M3 3h18v18H3z"/>
              <path d="M3 9h18M3 15h18M9 3v18M15 3v18"/>
            </svg>
            {distOn && selectedCountry ? 'Districts ON' : 'Districts'}
          </button>
          <div className="districts-tooltip" style={{
            position:'absolute', top:'calc(100% + 6px)', right:0,
            background:'#1a1e23', color:'#e6edf3', fontSize:11, lineHeight:1.5,
            padding:'7px 10px', borderRadius:6, whiteSpace:'nowrap', zIndex:99998,
            boxShadow:'0 4px 12px rgba(0,0,0,0.25)', display:'none', pointerEvents:'none',
          }}>
            {selectedCountry
              ? (distOn ? 'Click to hide district boundaries'
                        : 'Click to show districts for ' + (COUNTRY_MAP[selectedCountry] || ''))
              : 'Click a country on the map first'}
          </div>
        </div>

        <SatelliteControl satOn={satOn} setSatOn={setSatOn}
          satLayer={satLayer} setSatLayer={setSatLayer}
          satDate={satDate} setSatDate={setSatDate} />

        <div style={{ background:'rgba(255,255,255,0.92)',
                      border:'1px solid var(--border-primary)', borderRadius:6,
                      padding:'4px 10px', fontSize:12, color:'var(--text-secondary)',
                      pointerEvents:'none', boxShadow:'0 1px 4px rgba(0,0,0,0.10)' }}>
          {events.length} event{events.length !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Legend -- right side, below buttons */}
      <div style={{ position:'absolute', top:160, right:10, left:'auto', zIndex:1001,
                    background:'rgba(255,255,255,0.92)',
                    border:'1px solid var(--border-primary)',
                    borderRadius:6, padding:'8px 10px', pointerEvents:'none',
                    boxShadow:'0 1px 4px rgba(0,0,0,0.10)' }}>
        <div style={{ fontSize:10, color:'var(--text-muted)', textTransform:'uppercase',
                      letterSpacing:'0.06em', marginBottom:4, fontWeight:600 }}>Legend</div>
        <LegendRow color="#1D9E75" label="Open event"   dash={false} />
        <LegendRow color="#6e7681" label="Closed event" dash={true}  />
        {!selectedCountry ? (
          <div style={{ marginTop:6, paddingTop:6,
                        borderTop:'1px solid var(--border-muted)',
                        fontSize:10, color:'var(--text-muted)', lineHeight:1.5 }}>
            Click a country to<br/>filter + enable Districts
          </div>
        ) : (
          <div style={{ marginTop:6, paddingTop:6,
                        borderTop:'1px solid var(--border-muted)',
                        fontSize:10, color:'var(--text-muted)' }}>
            Click country to deselect
          </div>
        )}
      </div>

      <MapContainer
        center={ICPAC_CENTER} zoom={5} minZoom={4} maxZoom={10}
        maxBounds={MAX_BOUNDS} maxBoundsViscosity={0.85}
        style={{ width:'100%', height:'100%', position:'absolute', inset:0 }}>

        {lightMode ? (
          <>
            <TileLayer url={TILE_LIGHT}     attribution={ATTR} />
          </>
        ) : (
          <>
            <TileLayer url={TILE_DARK}    attribution={ATTR} />
          </>
        )}

        {satOn && (
          <WMSTileLayer url={GIBS_WMS} layers={satLayer}
            format="image/jpeg" version="1.1.1"
            time={satDate} opacity={0.72} transparent={false} />
        )}

        <OutsideMask />

        {/* Country boundaries from inline GeoJSON -- no network fetch */}
        <CountriesLayer
          lightMode={lightMode}
          selectedCountry={selectedCountry}
          onCountryClick={setSelectedCountry}
        />

        {/* District boundaries -- loaded when country selected + distOn */}
        {distOn && selectedCountry && (
          <DistrictLayer iso2={selectedCountry} lightMode={lightMode} />
        )}

        <FitRegion />
        <FlyTo events={events} selectedId={selectedEventId} />

        <MarkerClusterGroup chunkedLoading maxClusterRadius={60} showCoverageOnHover={false}>
          {events.map((ev) => {
            const color  = getCatColor(ev.category)
            const isOpen = ev.status === 'open'
            const isSel  = ev.id === selectedEventId
            const cat    = CATEGORIES[ev.category] || {}
            const wvLink = worldviewURL(ev)
            const cName  = COUNTRY_MAP[assignCountry(ev.coords) || ''] || ''

            return (
              <CircleMarker key={ev.id}
                center={[ev.coords[1], ev.coords[0]]}
                radius={isSel ? 13 : isOpen ? 9 : 7}
                pathOptions={{
                  color:       isSel ? '#1a1e23' : color,
                  fillColor:   color,
                  fillOpacity: isOpen ? 0.88 : 0.42,
                  weight:      isSel ? 2.5 : isOpen ? 1.5 : 1,
                  dashArray:   isOpen ? null : '4 3',
                }}
                eventHandlers={{ click: () => selectEvent(ev.id) }}>
                <Popup maxWidth={290}>
                  <div style={{ fontFamily:'inherit', minWidth:230 }}>
                    <div style={{ marginBottom:8, display:'flex', gap:6,
                                  flexWrap:'wrap', alignItems:'center' }}>
                      <span style={{ fontSize:11, fontWeight:500, padding:'2px 8px',
                                     borderRadius:100, background:color+'33', color:color,
                                     border:'1px solid '+color+'55' }}>
                        {cat.label || ev.category}
                      </span>
                      <span style={{ fontSize:11, fontWeight:600,
                                     color: isOpen ? '#1D9E75' : '#6e7681' }}>
                        {isOpen ? 'OPEN' : 'CLOSED'}
                      </span>
                    </div>
                    <p style={{ fontWeight:600, fontSize:13, color:'var(--text-primary)',
                                lineHeight:1.4, marginBottom:8 }}>
                      {ev.title}
                    </p>
                    <table style={{ borderCollapse:'collapse', width:'100%' }}>
                      <tbody>
                        <PopupRow label="Date"
                          value={(ev.latest_date || '--').slice(0,10)} />
                        {ev.closed && (
                          <PopupRow label="Closed" value={ev.closed.slice(0,10)} />
                        )}
                        {ev.magnitude && (
                          <PopupRow label="Magnitude"
                            value={ev.magnitude.value+' '+(ev.magnitude.unit||'')} />
                        )}
                        {cName && <PopupRow label="Country" value={cName} />}
                        <PopupRow label="Coords"
                          value={ev.coords[1].toFixed(2)+', '+ev.coords[0].toFixed(2)} />
                      </tbody>
                    </table>
                    <div style={{ marginTop:10, display:'flex', gap:10, flexWrap:'wrap' }}>
                      {ev.sources && ev.sources[0] && (
                        <a href={ev.sources[0].url} target="_blank" rel="noreferrer"
                           style={{ fontSize:11, color:'#378ADD' }}>
                          {ev.sources[0].id}
                        </a>
                      )}
                      {wvLink && (
                        <a href={wvLink} target="_blank" rel="noreferrer"
                           style={{ fontSize:11, color:'#1D9E75', fontWeight:500 }}>
                          View satellite image
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

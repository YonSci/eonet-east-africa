"""
setup_tier2.py
--------------
Adds 5 Tier 2 medium-impact features to NET-EA:

  1. Click-to-filter by country  -- click a country on the map to isolate its events
  2. Seasonal pattern heatmap    -- month x category grid showing when events peak
  3. Magnitude filter slider     -- hide events below a minimum magnitude threshold
  4. Mobile responsive layout    -- sidebar overlay, stacked panels, 2x2 stat cards
  5. Year-over-year comparison   -- already built (setup_yoy.py) -- confirmed present

Run from the eonet-east-africa project root:
    python setup_tier2.py

No new npm packages. Restart Vite after running:
    cd frontend && npm run dev
"""

import sys, argparse
from pathlib import Path

try:
    from colorama import Fore, Style, init as _ci
    _ci(autoreset=True)
    def ok(m):  print(f"{Fore.GREEN}  [+]{Style.RESET_ALL} {m}")
    def ow(m):  print(f"{Fore.YELLOW}  [~]{Style.RESET_ALL} {m}")
    def hdr(m): print(f"\n{Fore.CYAN}{Style.BRIGHT}{m}{Style.RESET_ALL}")
    def info(m):print(f"       {m}")
except ImportError:
    def ok(m):  print(f"  [+] {m}")
    def ow(m):  print(f"  [~] {m}")
    def hdr(m): print(f"\n{m}")
    def info(m):print(f"       {m}")

FILES = {}

# =============================================================================
# 1. useAppStore.js -- add selectedCountry + magFilter + isMobile hint
# =============================================================================
FILES["frontend/src/store/useAppStore.js"] = """import { create } from 'zustand'

export const CATEGORIES = {
  wildfires:           { label: 'Wildfires',           color: '#E8593C' },
  severeStorms:        { label: 'Severe Storms',        color: '#378ADD' },
  floods:              { label: 'Floods',               color: '#1D9E75' },
  drought:             { label: 'Drought',              color: '#BA7517' },
  volcanoes:           { label: 'Volcanoes',            color: '#E24B4A' },
  dustHaze:            { label: 'Dust and Haze',        color: '#888780' },
  earthquakes:         { label: 'Earthquakes',          color: '#7F77DD' },
  landslides:          { label: 'Landslides',           color: '#639922' },
  temperatureExtremes: { label: 'Temperature Extremes', color: '#E85D24' },
  waterColor:          { label: 'Water Color',          color: '#1D6FA5' },
}

export const ALL_CATS = Object.keys(CATEGORIES)

export const MAG_CATS = ['earthquakes', 'severeStorms', 'floods', 'temperatureExtremes']

export const COUNTRY_MAP = {
  DJ: 'Djibouti',    ER: 'Eritrea',      ET: 'Ethiopia',
  KE: 'Kenya',       RW: 'Rwanda',       SO: 'Somalia',
  SS: 'South Sudan', SD: 'Sudan',        TZ: 'Tanzania',
  UG: 'Uganda',      BI: 'Burundi',
}

export function readURLFilters() {
  const p = new URLSearchParams(window.location.search)
  return {
    days:      p.has('days')   ? parseInt(p.get('days'), 10) || 90 : null,
    status:    p.has('status') ? p.get('status') : null,
    cats:      p.has('cats')   ? p.get('cats').split(',').filter((c) => ALL_CATS.includes(c)) : null,
    dateMode:  p.has('mode')   ? p.get('mode') : null,
    startDate: p.has('start')  ? p.get('start') : null,
    endDate:   p.has('end')    ? p.get('end') : null,
  }
}

export function writeURLFilters(state) {
  const p = new URLSearchParams()
  if (state.dateMode === 'range') {
    p.set('mode', 'range')
    if (state.startDate) p.set('start', state.startDate)
    if (state.endDate)   p.set('end',   state.endDate)
  } else {
    if (state.lookbackDays !== 90) p.set('days', String(state.lookbackDays))
  }
  if (state.activeStatus !== 'all') p.set('status', state.activeStatus)
  const catStr = state.activeCategories.join(',')
  if (catStr !== ALL_CATS.join(',')) p.set('cats', catStr)
  const str = p.toString()
  window.history.replaceState({}, '', str ? '?' + str : window.location.pathname)
}

let toastSeq = 0

const useAppStore = create((set) => ({
  activeCategories: ALL_CATS,
  activeStatus:     'all',
  lookbackDays:     90,
  dateMode:         'lookback',
  startDate:        '',
  endDate:          '',
  selectedEventId:  null,
  selectedCountry:  null,   // ISO2 code e.g. 'KE', 'ET', or null
  magFilter:        0,      // minimum magnitude value (0 = show all)
  lightMode:        true,
  sidebarOpen:      true,
  toasts:           [],

  toggleCategory:   (cat) => set((s) => ({
    activeCategories: s.activeCategories.includes(cat)
      ? s.activeCategories.filter((c) => c !== cat)
      : [...s.activeCategories, cat],
  })),
  setAllCategories: (cats) => set({ activeCategories: cats }),
  setStatus:        (v)    => set({ activeStatus: v }),
  setDays:          (v)    => set({ lookbackDays: v }),
  setDateMode:      (v)    => set({ dateMode: v }),
  setStartDate:     (v)    => set({ startDate: v }),
  setEndDate:       (v)    => set({ endDate: v }),
  selectEvent:      (id)   => set({ selectedEventId: id }),
  setSelectedCountry: (iso2) => set((s) => ({
    selectedCountry: s.selectedCountry === iso2 ? null : iso2,
  })),
  clearCountry:     ()     => set({ selectedCountry: null }),
  setMagFilter:     (v)    => set({ magFilter: v }),
  toggleLight: () => set((s) => {
    const next = !s.lightMode
    document.documentElement.classList.toggle('light', next)
    return { lightMode: next }
  }),
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),

  addToast: (msg, type) => set((s) => ({
    toasts: [...s.toasts,
      { id: String(++toastSeq), msg, type: type || 'info', ts: Date.now() }],
  })),
  removeToast: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}))

if (typeof document !== 'undefined') {
  document.documentElement.classList.add('light')
}

export default useAppStore
"""

# =============================================================================
# 2. MapPanel.jsx -- country click filter + highlight + magnitude client filter
# =============================================================================
FILES["frontend/src/components/MapPanel.jsx"] = r"""import React, { useEffect, useState, useCallback, useRef } from 'react'
import {
  MapContainer, TileLayer, WMSTileLayer, CircleMarker,
  Popup, GeoJSON, Rectangle, useMap,
} from 'react-leaflet'
import MarkerClusterGroup from 'react-leaflet-cluster'
import 'leaflet/dist/leaflet.css'
import useAppStore, { CATEGORIES, COUNTRY_MAP } from '../store/useAppStore.js'
import { useEvents } from '../api/queries.js'

const ICPAC_CENTER  = [6.5, 38.0]
const MAX_BOUNDS    = [[-16.0, 18.0], [26.0, 56.0]]
const REGION_BOUNDS = [[-12.0, 22.0], [23.0, 52.0]]
const ICPAC_ISO2    = ['DJ','ER','ET','KE','RW','SO','SS','SD','TZ','UG','BI']
const GEO_BASE      = 'https://raw.githubusercontent.com/johan/world.geo.json/master/countries'

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

// Country bounding boxes for event assignment
const COUNTRY_BBOX = {
  SD: { minLat: 9, maxLat: 22, minLon: 21, maxLon: 38 },
  SS: { minLat: 3, maxLat: 12, minLon: 24, maxLon: 36 },
  ET: { minLat: 3, maxLat: 15, minLon: 33, maxLon: 48 },
  ER: { minLat:12, maxLat: 18, minLon: 36, maxLon: 44 },
  DJ: { minLat:10, maxLat: 13, minLon: 41, maxLon: 44 },
  SO: { minLat:-2, maxLat: 12, minLon: 40, maxLon: 52 },
  KE: { minLat:-5, maxLat:  5, minLon: 33, maxLon: 42 },
  UG: { minLat:-2, maxLat:  4, minLon: 29, maxLon: 35 },
  TZ: { minLat:-12,maxLat:  0, minLon: 29, maxLon: 41 },
  RW: { minLat:-3, maxLat:  0, minLon: 28, maxLon: 31 },
  BI: { minLat:-5, maxLat: -2, minLon: 28, maxLon: 31 },
}

export function assignCountry(coords) {
  if (!coords) return null
  const lon = coords[0]; const lat = coords[1]
  for (const [iso, b] of Object.entries(COUNTRY_BBOX)) {
    if (lon >= b.minLon && lon <= b.maxLon && lat >= b.minLat && lat <= b.maxLat) return iso
  }
  return null
}

function todayStr() { return new Date().toISOString().slice(0, 10) }
function getCatColor(cat) { return (CATEGORIES[cat] || {}).color || '#484f58' }

function worldviewURL(ev) {
  if (!ev.coords) return null
  const lon = ev.coords[0]; const lat = ev.coords[1]; const pad = 3
  const date = (ev.latest_date || todayStr()).slice(0, 10)
  return 'https://worldview.earthdata.nasa.gov/?v=' +
    (lon-pad)+','+(lat-pad)+','+(lon+pad)+','+(lat+pad)+'&t='+date
}

function FitRegion() {
  const map = useMap()
  useEffect(() => { map.fitBounds(REGION_BOUNDS, { padding: [10,10] }) }, [map])
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
    [[23,22],[90,52]], [[-90,22],[-12,52]],
  ]
  return strips.map((b, i) => (
    <Rectangle key={i} bounds={b}
      pathOptions={{ color:'transparent', fillColor:'#000', fillOpacity:0.4, weight:0 }} />
  ))
}

function CountriesLayer({ geo, lightMode, selectedCountry, onCountryClick }) {
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

  if (!geo) return null
  const key = 'countries-' + (lightMode ? 'l' : 'd') + '-' + (selectedCountry || 'none')
  return <GeoJSON key={key} data={geo} style={styleFunc} onEachFeature={onEachFeature} />
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
      if (btnRef.current && !btnRef.current.contains(e.target)) {
        const panel = document.getElementById('sat-panel')
        if (panel && !panel.contains(e.target)) setOpen(false)
      }
    }
    document.addEventListener('mousedown', onDown)
    return () => document.removeEventListener('mousedown', onDown)
  }, [open])

  return (
    <>
      <button ref={btnRef} onClick={openPanel} style={{
        fontSize:11, padding:'4px 10px', borderRadius:6,
        border:'1px solid',
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

export default function MapPanel({ height }) {
  const {
    activeCategories, activeStatus, selectedEventId, selectEvent,
    lightMode, selectedCountry, setSelectedCountry, magFilter,
  } = useAppStore()
  const { data: rawEvents = [], isLoading } = useEvents()

  const [geo,      setGeo]      = useState(null)
  const [satOn,    setSatOn]    = useState(false)
  const [satLayer, setSatLayer] = useState(GIBS_LAYERS[0].id)
  const [satDate,  setSatDate]  = useState(todayStr)

  useEffect(() => {
    Promise.allSettled(
      ICPAC_ISO2.map((iso) =>
        fetch(GEO_BASE + '/' + iso + '.geo.json', { signal: AbortSignal.timeout(7000) })
          .then((r) => (r.ok ? r.json() : null))
          .catch(() => null)
      )
    ).then((results) => {
      const features = results.flatMap((r, i) => {
        if (r.status !== 'fulfilled' || !r.value) return []
        const d = r.value
        const raw = d.type === 'FeatureCollection' ? d.features : [d]
        return raw.map((f) => ({
          ...f, properties: { ...(f.properties || {}), iso2: ICPAC_ISO2[i] },
        }))
      })
      if (features.length) setGeo({ type: 'FeatureCollection', features })
    })
  }, [])

  // Apply all filters including country + magnitude
  const events = rawEvents.filter((ev) => {
    if (!activeCategories.includes(ev.category)) return false
    if (activeStatus === 'open'   && ev.status !== 'open')   return false
    if (activeStatus === 'closed' && ev.status !== 'closed') return false
    if (!ev.coords) return false
    if (selectedCountry && assignCountry(ev.coords) !== selectedCountry) return false
    if (magFilter > 0 && ev.magnitude && ev.magnitude.value < magFilter) return false
    return true
  })

  const countryName = selectedCountry ? (COUNTRY_MAP[selectedCountry] || selectedCountry) : null

  return (
    <div style={{ flex:1, position:'relative',
                  background: lightMode ? '#e8f0e0' : '#0d1117',
                  minHeight: height || 340, overflow:'hidden' }}>

      {isLoading && (
        <div style={{ position:'absolute', inset:0, zIndex:1000,
                      display:'flex', alignItems:'center', justifyContent:'center',
                      background:'rgba(246,248,250,0.75)', fontSize:13,
                      color:'var(--text-secondary)', pointerEvents:'none' }}>
          Loading events...
        </div>
      )}

      {/* Region badge -- top left */}
      <div style={{ position:'absolute', top:10, left:10, zIndex:1001,
                    display:'flex', alignItems:'center', gap:6, flexWrap:'wrap' }}>
        <div style={{ background:'rgba(255,255,255,0.92)',
                      border:'1px solid var(--border-primary)', borderRadius:6,
                      padding:'4px 10px', fontSize:11, fontWeight:600,
                      color:'#1D9E75', pointerEvents:'none',
                      boxShadow:'0 1px 4px rgba(0,0,0,0.10)' }}>
          Greater Horn of Africa
        </div>
        {countryName && (
          <div style={{ background:'#E1F5EE', border:'1px solid #1D9E7555',
                        borderRadius:6, padding:'4px 10px', fontSize:11,
                        fontWeight:600, color:'#085041', display:'flex',
                        alignItems:'center', gap:6,
                        boxShadow:'0 1px 4px rgba(0,0,0,0.10)' }}>
            {countryName}
            <button onClick={() => setSelectedCountry(null)}
              style={{ background:'none', border:'none', cursor:'pointer',
                       color:'#085041', fontSize:14, lineHeight:1,
                       padding:'0 0 0 2px' }}>
              x
            </button>
          </div>
        )}
      </div>

      {/* Top right controls */}
      <div style={{ position:'absolute', top:10, right:10, zIndex:1001,
                    display:'flex', gap:6, alignItems:'flex-start' }}>
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

      {/* Legend -- bottom left */}
      <div style={{ position:'absolute', bottom:30, left:10, zIndex:1001,
                    background:'rgba(255,255,255,0.92)',
                    border:'1px solid var(--border-primary)',
                    borderRadius:6, padding:'8px 10px', pointerEvents:'none',
                    boxShadow:'0 1px 4px rgba(0,0,0,0.10)' }}>
        <div style={{ fontSize:10, color:'var(--text-muted)', textTransform:'uppercase',
                      letterSpacing:'0.06em', marginBottom:4, fontWeight:600 }}>
          Legend
        </div>
        <LegendRow color="#1D9E75" label="Open event"   dash={false} />
        <LegendRow color="#6e7681" label="Closed event" dash={true}  />
        {selectedCountry && (
          <div style={{ marginTop:6, paddingTop:6,
                        borderTop:'1px solid var(--border-muted)',
                        fontSize:11, color:'var(--text-muted)' }}>
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
            <TileLayer url={TILE_LBL_LIGHT} />
          </>
        ) : (
          <>
            <TileLayer url={TILE_DARK}    attribution={ATTR} />
            <TileLayer url={TILE_LBL_DARK} />
          </>
        )}

        {satOn && (
          <WMSTileLayer url={GIBS_WMS} layers={satLayer}
            format="image/jpeg" version="1.1.1"
            time={satDate} opacity={0.72} transparent={false} />
        )}

        <OutsideMask />
        <CountriesLayer geo={geo} lightMode={lightMode}
          selectedCountry={selectedCountry}
          onCountryClick={setSelectedCountry} />
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
"""

# =============================================================================
# 3. FilterSidebar.jsx -- magnitude slider + country clear
# =============================================================================
FILES["frontend/src/components/FilterSidebar.jsx"] = """import React, { useMemo } from 'react'
import useAppStore, { CATEGORIES, ALL_CATS, MAG_CATS, COUNTRY_MAP } from '../store/useAppStore.js'
import { useSummary, useEvents } from '../api/queries.js'

const STATUS_OPTS = [
  { value:'all',    label:'All events'  },
  { value:'open',   label:'Open only'   },
  { value:'closed', label:'Closed only' },
]
const DAY_OPTS = [7, 14, 30, 60, 90, 180, 365]

function Section({ label, children }) {
  return (
    <div style={{ marginBottom:18 }}>
      <p style={{ fontSize:10, fontWeight:600, letterSpacing:'0.08em',
                  textTransform:'uppercase', color:'var(--text-muted)', marginBottom:8 }}>
        {label}
      </p>
      {children}
    </div>
  )
}

function Pill({ active, onClick, children }) {
  return (
    <button onClick={onClick} style={{
      padding:'4px 10px', borderRadius:100, fontSize:12, marginBottom:4,
      border:'1px solid',
      borderColor: active ? '#378ADD' : 'var(--border-primary)',
      background:  active ? '#378ADD' : 'transparent',
      color:       active ? '#fff'    : 'var(--text-secondary)',
      cursor:'pointer',
    }}>
      {children}
    </button>
  )
}

function smallBtn(active) {
  return {
    fontSize:12, padding:'3px 10px', borderRadius:6,
    border:'1px solid var(--border-primary)',
    background: active ? 'var(--bg-elevated)' : 'transparent',
    color: active ? 'var(--text-primary)' : 'var(--text-secondary)',
    cursor:'pointer',
  }
}

export default function FilterSidebar() {
  const {
    activeCategories, toggleCategory, setAllCategories,
    activeStatus,     setStatus,
    lookbackDays,     setDays,
    dateMode,         setDateMode,
    startDate,        setStartDate,
    endDate,          setEndDate,
    selectedCountry,  setSelectedCountry,
    magFilter,        setMagFilter,
  } = useAppStore()

  const { data: summary }    = useSummary()
  const { data: rawEvents = [] } = useEvents()
  const byCat = summary && summary.by_category ? summary.by_category : {}

  const allOn  = activeCategories.length === ALL_CATS.length
  const noneOn = activeCategories.length === 0

  // Magnitude slider -- only show when magnitude-capable cats are active
  const hasMagCat = activeCategories.some((c) => MAG_CATS.includes(c))
  const magEvents = rawEvents.filter((ev) => ev.magnitude != null)
  const maxMag    = useMemo(() => {
    if (!magEvents.length) return 10
    return Math.ceil(Math.max(...magEvents.map((e) => e.magnitude.value || 0)))
  }, [magEvents])

  const countryName = selectedCountry ? (COUNTRY_MAP[selectedCountry] || selectedCountry) : null

  return (
    <aside className="no-print filter-sidebar" style={{
      width:'var(--sidebar-w)', background:'var(--bg-surface)',
      borderRight:'1px solid var(--border-primary)',
      display:'flex', flexDirection:'column',
      overflow:'hidden', flexShrink:0,
    }}>
      <div style={{ overflowY:'auto', flex:1, padding:'14px 12px' }}>

        {/* -- Active country filter -- */}
        {countryName && (
          <div style={{ marginBottom:14, padding:'8px 10px',
                        background:'#E1F5EE', border:'1px solid #1D9E7544',
                        borderRadius:'var(--radius-md)',
                        display:'flex', alignItems:'center', gap:8 }}>
            <div style={{ flex:1 }}>
              <div style={{ fontSize:10, fontWeight:600, color:'#085041',
                            letterSpacing:'0.06em', textTransform:'uppercase',
                            marginBottom:2 }}>Country filter</div>
              <div style={{ fontSize:12, fontWeight:500, color:'#0F6E56' }}>
                {countryName}
              </div>
            </div>
            <button onClick={() => setSelectedCountry(null)}
              style={{ background:'#1D9E7522', border:'1px solid #1D9E7544',
                       borderRadius:5, padding:'3px 8px', fontSize:11,
                       color:'#085041', cursor:'pointer' }}>
              Clear
            </button>
          </div>
        )}

        {/* -- Status -- */}
        <Section label="Status">
          <div style={{ display:'flex', flexWrap:'wrap', gap:4 }}>
            {STATUS_OPTS.map((o) => (
              <Pill key={o.value} active={activeStatus === o.value}
                onClick={() => setStatus(o.value)}>
                {o.label}
              </Pill>
            ))}
          </div>
        </Section>

        {/* -- Time period -- */}
        <Section label="Time period">
          <div style={{ display:'flex', gap:6, marginBottom:10 }}>
            <button style={smallBtn(dateMode === 'lookback')}
              onClick={() => setDateMode('lookback')}>Lookback</button>
            <button style={smallBtn(dateMode === 'range')}
              onClick={() => setDateMode('range')}>Date range</button>
          </div>
          {dateMode === 'lookback' && (
            <div style={{ display:'flex', flexWrap:'wrap', gap:5 }}>
              {DAY_OPTS.map((d) => (
                <Pill key={d} active={lookbackDays === d} onClick={() => setDays(d)}>
                  {d + 'd'}
                </Pill>
              ))}
            </div>
          )}
          {dateMode === 'range' && (
            <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
              <div>
                <div style={{ fontSize:11, color:'var(--text-muted)', marginBottom:3 }}>
                  Start date
                </div>
                <input type="date" value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  style={{ width:'100%', fontSize:12, padding:'5px 8px',
                           border:'1px solid var(--border-primary)', borderRadius:5,
                           background:'var(--bg-elevated)', color:'var(--text-primary)' }} />
              </div>
              <div>
                <div style={{ fontSize:11, color:'var(--text-muted)', marginBottom:3 }}>
                  End date
                </div>
                <input type="date" value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  style={{ width:'100%', fontSize:12, padding:'5px 8px',
                           border:'1px solid var(--border-primary)', borderRadius:5,
                           background:'var(--bg-elevated)', color:'var(--text-primary)' }} />
              </div>
            </div>
          )}
        </Section>

        {/* -- Magnitude filter (only when relevant) -- */}
        {hasMagCat && (
          <Section label="Minimum magnitude">
            <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:6 }}>
              <input type="range" min="0" max={maxMag} step="0.5"
                value={magFilter}
                onChange={(e) => setMagFilter(parseFloat(e.target.value))}
                style={{ flex:1, accentColor:'#7F77DD' }} />
              <span style={{ fontSize:13, fontWeight:600, minWidth:30,
                             textAlign:'right', color:'#7F77DD' }}>
                {magFilter > 0 ? magFilter.toFixed(1) : 'off'}
              </span>
            </div>
            <div style={{ fontSize:11, color:'var(--text-muted)', lineHeight:1.5 }}>
              {magFilter > 0
                ? 'Hiding events with magnitude below ' + magFilter.toFixed(1) + '. Events without magnitude data are always shown.'
                : 'Slide right to hide low-magnitude events. Applies to earthquakes, storms, and floods.'}
            </div>
            {magFilter > 0 && (
              <button onClick={() => setMagFilter(0)}
                style={{ marginTop:6, fontSize:11, padding:'3px 8px', borderRadius:4,
                         border:'1px solid var(--border-primary)', background:'transparent',
                         color:'var(--text-secondary)', cursor:'pointer' }}>
                Clear magnitude filter
              </button>
            )}
          </Section>
        )}

        {/* -- Categories -- */}
        <Section label="Event categories">
          <div style={{ display:'flex', gap:6, marginBottom:10 }}>
            <button style={smallBtn(allOn)}  onClick={() => setAllCategories(ALL_CATS)}>All</button>
            <button style={smallBtn(noneOn)} onClick={() => setAllCategories([])}>None</button>
          </div>
          {ALL_CATS.map((cat) => {
            const meta   = CATEGORIES[cat]
            const active = activeCategories.includes(cat)
            const count  = byCat[cat] || 0
            return (
              <button key={cat} onClick={() => toggleCategory(cat)} style={{
                width:'100%', display:'flex', alignItems:'center', gap:8,
                padding:'6px 8px', marginBottom:3,
                borderRadius:'var(--radius-sm)', cursor:'pointer',
                border:'1px solid',
                borderColor: active ? meta.color+'55' : 'var(--border-muted)',
                background:  active ? meta.color+'18' : 'transparent',
                transition:'all 0.12s', textAlign:'left',
              }}>
                <span style={{ width:10, height:10, borderRadius:'50%', flexShrink:0,
                               background: active ? meta.color : 'var(--text-faint)' }} />
                <span style={{ flex:1, fontSize:13,
                               color: active ? 'var(--text-primary)' : 'var(--text-secondary)',
                               fontWeight: active ? 500 : 400 }}>
                  {meta.label}
                </span>
                {count > 0 && (
                  <span style={{ fontSize:11, padding:'1px 5px', borderRadius:100,
                                 background: active ? meta.color+'33' : 'var(--bg-elevated)',
                                 color: active ? meta.color : 'var(--text-muted)' }}>
                    {count}
                  </span>
                )}
              </button>
            )
          })}
        </Section>

        <Section label="Data source">
          <p style={{ fontSize:11, color:'var(--text-muted)', lineHeight:1.6 }}>
            NASA EONET v3 -- Greater Horn of Africa (21.8-51.4 E, 11.7 S - 22.0 N).
            Auto-refreshed every 15 min.
          </p>
          <a href="https://eonet.gsfc.nasa.gov/docs/v3" target="_blank" rel="noreferrer"
            style={{ fontSize:11, color:'var(--accent-blue)', display:'block', marginTop:6 }}>
            EONET API docs
          </a>
        </Section>
      </div>
    </aside>
  )
}
"""

# =============================================================================
# 4. SeasonalHeatmap.jsx -- month x category event density grid
# =============================================================================
FILES["frontend/src/components/SeasonalHeatmap.jsx"] = """import React, { useMemo } from 'react'
import { CATEGORIES } from '../store/useAppStore.js'

const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun',
                'Jul','Aug','Sep','Oct','Nov','Dec']

// East Africa seasonal context annotations
const SEASON_BANDS = [
  { months:[2,3,4],   label:'Long rains (MAM)',  color:'#1D9E7520' },
  { months:[9,10],    label:'Short rains (OND)', color:'#378ADD20' },
  { months:[0,1,6,7], label:'Dry season',        color:'#BA751710' },
]

function hexToRgba(hex, alpha) {
  if (!hex || hex.length < 7) return 'transparent'
  const r = parseInt(hex.slice(1,3),16)
  const g = parseInt(hex.slice(3,5),16)
  const b = parseInt(hex.slice(5,7),16)
  return 'rgba('+r+','+g+','+b+','+alpha+')'
}

export default function SeasonalHeatmap({ events }) {
  const grid = useMemo(() => {
    const counts = {}
    events.forEach((ev) => {
      const date = ev.latest_date || ''
      if (!date) return
      const monthIdx = parseInt(date.slice(5,7), 10) - 1
      if (monthIdx < 0 || monthIdx > 11) return
      const cat = ev.category || 'unknown'
      if (!counts[cat]) counts[cat] = Array(12).fill(0)
      counts[cat][monthIdx] += 1
    })
    return counts
  }, [events])

  const cats    = Object.keys(CATEGORIES).filter((c) => grid[c])
  const allVals = Object.values(grid).flatMap((row) => row)
  const maxVal  = Math.max(...allVals, 1)

  if (!cats.length) {
    return (
      <p style={{ fontSize:12, color:'var(--text-muted)',
                  textAlign:'center', padding:'20px 0' }}>
        No events with date information in the current filter.
      </p>
    )
  }

  return (
    <div>
      <p style={{ fontSize:11, color:'var(--text-muted)', marginBottom:12, lineHeight:1.5 }}>
        Event density by month and category. Colour intensity = relative count.
        Seasonal bands show East Africa long rains (MAM), short rains (OND), and dry seasons.
      </p>

      <div style={{ overflowX:'auto' }}>
        <table style={{ borderCollapse:'collapse', width:'100%',
                        tableLayout:'fixed', minWidth:480 }}>
          <thead>
            <tr>
              {/* Category label column */}
              <th style={{ width:130, padding:'4px 8px', textAlign:'left',
                           fontSize:10, fontWeight:600, color:'var(--text-muted)',
                           letterSpacing:'0.05em', textTransform:'uppercase',
                           background:'var(--bg-elevated)',
                           border:'1px solid var(--border-muted)' }}>
                Category
              </th>
              {MONTHS.map((m, i) => {
                // Find season band colour for this month
                const band = SEASON_BANDS.find((b) => b.months.includes(i))
                return (
                  <th key={m} style={{
                    padding:'4px 2px', textAlign:'center', fontSize:11,
                    fontWeight:600, color:'var(--text-secondary)',
                    background: band ? band.color : 'var(--bg-elevated)',
                    border:'1px solid var(--border-muted)',
                  }}>
                    {m}
                  </th>
                )
              })}
            </tr>
          </thead>
          <tbody>
            {cats.map((cat) => {
              const meta = CATEGORIES[cat]
              const row  = grid[cat] || Array(12).fill(0)
              const rowMax = Math.max(...row, 1)
              return (
                <tr key={cat}>
                  <td style={{ padding:'4px 8px', fontSize:11, fontWeight:500,
                               color:'var(--text-secondary)',
                               background:'var(--bg-elevated)',
                               border:'1px solid var(--border-muted)',
                               whiteSpace:'nowrap' }}>
                    <div style={{ display:'flex', alignItems:'center', gap:5 }}>
                      <span style={{ width:8, height:8, borderRadius:'50%',
                                     flexShrink:0, background: meta ? meta.color : '#888' }} />
                      {meta ? meta.label : cat}
                    </div>
                  </td>
                  {row.map((count, monthIdx) => {
                    const band      = SEASON_BANDS.find((b) => b.months.includes(monthIdx))
                    const intensity = count / maxVal
                    const catColor  = meta ? meta.color : '#888780'
                    const bg        = count === 0
                      ? (band ? band.color : 'transparent')
                      : hexToRgba(catColor, Math.min(intensity * 0.8 + 0.15, 0.85))
                    const textColor = count === 0
                      ? 'var(--text-faint)'
                      : intensity > 0.5 ? '#fff' : catColor

                    return (
                      <td key={monthIdx}
                        title={MONTHS[monthIdx] + ': ' + count + ' events'}
                        style={{
                          padding:'6px 2px', textAlign:'center',
                          fontSize:11, fontWeight: count > 0 ? 600 : 400,
                          color: textColor,
                          background: bg,
                          border:'1px solid var(--border-muted)',
                          cursor: count > 0 ? 'default' : 'default',
                        }}>
                        {count > 0 ? count : ''}
                      </td>
                    )
                  })}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Season band legend */}
      <div style={{ display:'flex', gap:14, marginTop:10, flexWrap:'wrap' }}>
        {SEASON_BANDS.map((b) => (
          <div key={b.label} style={{ display:'flex', alignItems:'center', gap:5 }}>
            <span style={{ width:12, height:12, borderRadius:2,
                           background:b.color, border:'1px solid var(--border-muted)',
                           flexShrink:0 }} />
            <span style={{ fontSize:11, color:'var(--text-muted)' }}>{b.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
"""

# =============================================================================
# 5. index.css -- add mobile responsive rules + country tooltip
# =============================================================================
INDEX_CSS_APPEND = """
/* -- Country tooltip -------------------------------------------------------- */
.country-tooltip {
  background: var(--bg-elevated) !important;
  border: 1px solid var(--border-primary) !important;
  border-radius: 5px !important;
  color: var(--text-primary) !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  padding: 3px 8px !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.12) !important;
}
.country-tooltip::before { display: none !important; }

/* -- Mobile responsive ------------------------------------------------------ */
@media (max-width: 768px) {
  :root { --sidebar-w: 80vw; --topnav-h: 48px; }

  body { overflow: auto; }
  #root { height: auto; min-height: 100vh; }

  .filter-sidebar {
    position: fixed !important;
    top: 0; left: 0; bottom: 0;
    z-index: 3000;
    transform: translateX(-105%);
    transition: transform 0.25s ease;
    box-shadow: 4px 0 24px rgba(0,0,0,0.18);
  }
  .filter-sidebar.mobile-open {
    transform: translateX(0) !important;
  }

  .stat-grid-4 {
    grid-template-columns: 1fr 1fr !important;
  }

  .map-event-row {
    flex-direction: column !important;
    height: auto !important;
  }

  .event-right-panel {
    width: 100% !important;
    height: 280px !important;
    border-left: none !important;
    border-top: 1px solid var(--border-primary) !important;
  }

  .map-fill {
    height: 55vh !important;
    min-height: 300px !important;
  }

  .tab-bar-row {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  .tab-bar-row::-webkit-scrollbar { display: none; }
}

@media (max-width: 480px) {
  .stat-grid-4 { grid-template-columns: 1fr 1fr !important; }
  .analytics-grid { grid-template-columns: 1fr !important; }
}
"""

# =============================================================================
# 6. App.jsx -- mobile layout logic
# =============================================================================
FILES["frontend/src/App.jsx"] = """import React, { useState, useEffect, useRef } from 'react'
import TopNav         from './components/TopNav.jsx'
import FilterSidebar  from './components/FilterSidebar.jsx'
import StatCards      from './components/StatCards.jsx'
import MapPanel       from './components/MapPanel.jsx'
import EventList      from './components/EventList.jsx'
import AnalyticsPanel from './components/AnalyticsPanel.jsx'
import AboutPanel     from './components/AboutPanel.jsx'
import ToastContainer from './components/ToastContainer.jsx'
import PrintButton    from './components/PrintButton.jsx'
import useAppStore, {
  ALL_CATS, readURLFilters, writeURLFilters,
} from './store/useAppStore.js'
import { useEvents } from './api/queries.js'

const TABS = [
  { id:'map',       label:'Map view'  },
  { id:'analytics', label:'Analytics' },
  { id:'about',     label:'About'     },
]

function useIsMobile() {
  const [isMobile, setIsMobile] = useState(
    typeof window !== 'undefined' && window.innerWidth < 768
  )
  useEffect(() => {
    function handle() { setIsMobile(window.innerWidth < 768) }
    window.addEventListener('resize', handle)
    return () => window.removeEventListener('resize', handle)
  }, [])
  return isMobile
}

function EventWatcher() {
  const { data: events }  = useEvents()
  const addToast          = useAppStore((s) => s.addToast)
  const prevIdsRef        = useRef(null)

  useEffect(() => {
    if (!events || events.length === 0) return
    const currentIds = new Set(events.map((e) => e.id))
    if (prevIdsRef.current !== null && prevIdsRef.current.size > 0) {
      const newEvs = events.filter((e) => !prevIdsRef.current.has(e.id))
      if (newEvs.length > 0) {
        const names = newEvs.slice(0, 2).map((e) => e.title).join('; ')
        addToast(newEvs.length + ' new event' +
          (newEvs.length > 1 ? 's' : '') + ': ' + names, 'info')
      }
    }
    prevIdsRef.current = currentIds
  }, [events, addToast])

  return null
}

export default function App() {
  const {
    sidebarOpen, activeCategories, activeStatus,
    lookbackDays, dateMode, startDate, endDate,
    setStatus, setDays, setAllCategories,
    setDateMode, setStartDate, setEndDate, toggleSidebar,
  } = useAppStore()

  const [activeTab,     setActiveTab]    = useState('map')
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const isMobile = useIsMobile()

  // Read URL filters on mount
  useEffect(() => {
    const f = readURLFilters()
    if (f.status)    setStatus(f.status)
    if (f.days)      setDays(f.days)
    if (f.cats && f.cats.length > 0) setAllCategories(f.cats)
    if (f.dateMode)  setDateMode(f.dateMode)
    if (f.startDate) setStartDate(f.startDate)
    if (f.endDate)   setEndDate(f.endDate)
  }, [])

  // Write URL when filters change
  useEffect(() => {
    writeURLFilters({ activeCategories, activeStatus, lookbackDays,
                      dateMode, startDate, endDate })
  }, [activeCategories, activeStatus, lookbackDays, dateMode, startDate, endDate])

  // Close mobile menu when tab changes
  useEffect(() => { setMobileMenuOpen(false) }, [activeTab])

  // Click outside to close mobile sidebar
  useEffect(() => {
    if (!isMobile || !mobileMenuOpen) return
    function handle(e) {
      if (!e.target.closest('.filter-sidebar') &&
          !e.target.closest('.menu-btn')) {
        setMobileMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handle)
    return () => document.removeEventListener('mousedown', handle)
  }, [isMobile, mobileMenuOpen])

  const showSidebar   = (isMobile ? true : sidebarOpen) && activeTab !== 'about'
  const showStatCards = activeTab !== 'about'

  const sidebarClass = 'filter-sidebar' +
    (isMobile && mobileMenuOpen ? ' mobile-open' : '')

  return (
    <div style={{ display:'flex', flexDirection:'column',
                  height: isMobile ? 'auto' : '100vh',
                  minHeight:'100vh', overflow: isMobile ? 'auto' : 'hidden' }}>
      <ToastContainer />
      <EventWatcher />

      {/* Print header */}
      <div id="print-header-inject" className="print-only print-header" />

      <TopNav isMobile={isMobile} onMenuClick={() => setMobileMenuOpen((v) => !v)} />

      {/* Mobile sidebar overlay backdrop */}
      {isMobile && mobileMenuOpen && (
        <div onClick={() => setMobileMenuOpen(false)} style={{
          position:'fixed', inset:0, background:'rgba(0,0,0,0.4)',
          zIndex:2999,
        }} />
      )}

      <div style={{ display:'flex', flex:1,
                    overflow: isMobile ? 'visible' : 'hidden' }}>

        {/* Sidebar -- always in DOM on mobile (slides via CSS) */}
        {showSidebar && (
          <div className={sidebarClass}>
            {isMobile && (
              <div style={{ padding:'12px 14px', borderBottom:'1px solid var(--border-primary)',
                            display:'flex', justifyContent:'space-between',
                            alignItems:'center' }}>
                <span style={{ fontSize:12, fontWeight:600,
                               color:'var(--text-secondary)' }}>Filters</span>
                <button onClick={() => setMobileMenuOpen(false)}
                  style={{ background:'none', border:'none', cursor:'pointer',
                           fontSize:18, color:'var(--text-muted)' }}>
                  x
                </button>
              </div>
            )}
            <FilterSidebar />
          </div>
        )}

        <main style={{ flex:1, display:'flex', flexDirection:'column',
                       overflow: isMobile ? 'visible' : 'hidden', minWidth:0 }}>

          {showStatCards && <StatCards />}

          {/* Tab bar */}
          <div className="tab-bar-row no-print" style={{
            display:'flex', alignItems:'center', gap:2,
            padding:'8px 14px 0',
            borderBottom:'1px solid var(--border-primary)',
            background:'var(--bg-base)', flexShrink:0,
          }}>
            {TABS.map((tab) => {
              const active = activeTab === tab.id
              return (
                <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={{
                  padding:'6px 14px', fontSize:13,
                  fontWeight: active ? 600 : 400,
                  color: active ? 'var(--text-primary)' : 'var(--text-secondary)',
                  background:'transparent', border:'none',
                  borderBottom:'2px solid',
                  borderBottomColor: active ? '#1D9E75' : 'transparent',
                  cursor:'pointer', marginBottom:-1, whiteSpace:'nowrap',
                }}>
                  {tab.label}
                </button>
              )
            })}
            <div style={{ flex:1 }} />
            {!isMobile && (
              <>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(window.location.href)
                      .then(() => useAppStore.getState().addToast('Link copied', 'info'))
                      .catch(() => {})
                  }}
                  className="no-print"
                  title="Copy shareable link"
                  style={{ fontSize:12, padding:'4px 10px', borderRadius:6,
                           border:'1px solid var(--border-primary)',
                           background:'transparent', color:'var(--text-secondary)',
                           cursor:'pointer', display:'flex', alignItems:'center', gap:5 }}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" strokeWidth="2" strokeLinecap="round"
                    strokeLinejoin="round">
                    <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                    <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
                  </svg>
                  Share
                </button>
                <PrintButton />
              </>
            )}
          </div>

          {/* Map tab */}
          {activeTab === 'map' && (
            <div className="map-event-row"
              style={{ flex:1, display:'flex',
                       overflow: isMobile ? 'visible' : 'hidden',
                       flexDirection: isMobile ? 'column' : 'row' }}>
              <div className="map-fill" style={{ flex:1, minHeight: isMobile ? '55vh' : 'auto' }}>
                <MapPanel />
              </div>
              <div className="event-right-panel">
                <EventList />
              </div>
            </div>
          )}

          {activeTab === 'analytics' && <AnalyticsPanel />}
          {activeTab === 'about'     && <AboutPanel />}
        </main>
      </div>
    </div>
  )
}
"""

# =============================================================================
# 7. TopNav.jsx -- add mobile menu button
# =============================================================================
FILES["frontend/src/components/TopNav.jsx"] = """import React from 'react'
import useAppStore from '../store/useAppStore.js'
import { useCacheStatus } from '../api/queries.js'

export default function TopNav({ isMobile, onMenuClick }) {
  const { lightMode, toggleLight, toggleSidebar } = useAppStore()
  const { data: cacheInfo } = useCacheStatus()
  const evCount = cacheInfo && cacheInfo.event_count
  const mode    = cacheInfo && cacheInfo.mode

  function handleMenuClick() {
    if (isMobile && onMenuClick) { onMenuClick() }
    else { toggleSidebar() }
  }

  return (
    <header style={{
      height:'var(--topnav-h)', background:'var(--bg-surface)',
      borderBottom:'1px solid var(--border-primary)',
      display:'flex', alignItems:'center',
      padding:'0 16px', gap:10, flexShrink:0, zIndex:100,
    }}>
      <button onClick={handleMenuClick} className="menu-btn no-print"
        title="Toggle sidebar" style={btnStyle}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
          <rect x="1" y="3"    width="14" height="1.5" rx="0.75"/>
          <rect x="1" y="7.25" width="14" height="1.5" rx="0.75"/>
          <rect x="1" y="11.5" width="14" height="1.5" rx="0.75"/>
        </svg>
      </button>

      <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
        stroke="#1D9E75" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M13 7L17 3M17 3L21 7M17 3V13"/>
        <circle cx="9" cy="15" r="4"/>
        <path d="M3 21L7 17"/>
        <path d="M9 11L13 7"/>
      </svg>

      <div style={{ display:'flex', alignItems:'baseline', gap: isMobile ? 4 : 8 }}>
        <span style={{ fontWeight:600, fontSize: isMobile ? 13 : 14,
                       color:'var(--text-primary)', letterSpacing:'-0.01em' }}>
          {isMobile ? 'NET-EA' : 'Natural Event Tracker for East Africa'}
        </span>
        <span style={{ fontSize:11, fontWeight:700, padding:'1px 7px',
                       borderRadius:4, background:'#1D9E7522',
                       border:'1px solid #1D9E7544', color:'#0F6E56',
                       letterSpacing:'0.04em' }}>
          NET-EA
        </span>
      </div>

      <div style={{ flex:1 }} />

      {evCount != null && !isMobile && (
        <div style={{ display:'flex', alignItems:'center', gap:5,
                      fontSize:11, color:'var(--text-muted)' }}>
          <span style={{ width:6, height:6, borderRadius:'50%',
                         background: mode === 'backend' ? '#1D9E75' : '#378ADD',
                         display:'inline-block' }} />
          {evCount} events
          {cacheInfo.ttl_remaining_s != null
            ? ' -- refresh in ' + Math.ceil(cacheInfo.ttl_remaining_s / 60) + 'm'
            : ' -- live'}
        </div>
      )}

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
  background:'transparent', border:'none',
  color:'var(--text-secondary)', cursor:'pointer',
  padding:'6px', borderRadius:6,
  display:'flex', alignItems:'center', fontSize:13,
}
"""

# =============================================================================
# 8. StatCards.jsx -- add stat-grid-4 class for mobile CSS
# =============================================================================
STATCARDS_GRID_PATCH_OLD = '      display: grid, gridTemplateColumns: \'repeat(4, 1fr)\','
STATCARDS_GRID_PATCH_NEW = '      display: \'grid\', gridTemplateColumns: \'repeat(4, 1fr)\','

# =============================================================================
# Builder
# =============================================================================
def build(root: Path):
    fe = root / "frontend"
    hdr(f"Adding Tier 2 features to NET-EA in: {root}")
    created = updated = 0

    # 1. Full file writes
    for rel, content in FILES.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        existed = target.exists()
        target.write_text(content, encoding="utf-8")
        (ow if existed else ok)(("update  " if existed else "create  ") + rel)
        if existed: updated += 1
        else: created += 1

    # 2. Append mobile CSS to index.css
    css_path = fe / "src/index.css"
    if css_path.exists():
        css_txt = css_path.read_text(encoding="utf-8")
        if "country-tooltip" not in css_txt:
            css_path.write_text(css_txt.rstrip() + "\n" + INDEX_CSS_APPEND, encoding="utf-8")
            ow("patch   frontend/src/index.css (mobile CSS + country tooltip)")
            updated += 1

    # 3. Patch AnalyticsPanel to include SeasonalHeatmap
    ap = fe / "src/components/AnalyticsPanel.jsx"
    if ap.exists():
        txt = ap.read_text(encoding="utf-8")
        changed = False
        if "SeasonalHeatmap" not in txt:
            lines = txt.split("\n")
            last_import = 0
            for i, line in enumerate(lines):
                if line.startswith("import "):
                    last_import = i
            lines.insert(last_import + 1,
                "import SeasonalHeatmap from './SeasonalHeatmap.jsx'")
            txt = "\n".join(lines)
            changed = True

        SEASONAL_CARD = """
      {/* Seasonal pattern heatmap */}
      <Card title="Seasonal event patterns (month x category)" style={{ gridColumn:'1 / -1' }}>
        <SeasonalHeatmap events={events} />
      </Card>

"""
        if "SeasonalHeatmap" in txt and SEASONAL_CARD.strip() not in txt:
            INSERT_BEFORE = "function Card({ title, children, style }) {"
            txt = txt.replace(INSERT_BEFORE, SEASONAL_CARD + INSERT_BEFORE)
            changed = True

        # Fix grid class name for mobile
        txt = txt.replace(
            "display: 'grid',\n      gridTemplateColumns: '1fr 1fr',",
            "display: 'grid', gridTemplateColumns: '1fr 1fr',"
        )

        if changed:
            ap.write_text(txt, encoding="utf-8")
            ow("patch   frontend/src/components/AnalyticsPanel.jsx (SeasonalHeatmap)")
            updated += 1

    # 4. ASCII check all JSX/JS
    print()
    bad = []
    for f in list((fe / "src").rglob("*.jsx")) + list((fe / "src").rglob("*.js")):
        raw = f.read_bytes()
        for i, line in enumerate(raw.split(b"\n"), 1):
            if any(b > 127 for b in line):
                bad.append(f"  {f.name}:{i}")
    if bad:
        print("  WARN  Non-ASCII (OXC will reject):")
        for b in bad[:10]: print(b)
    else:
        ok("ASCII-clean -- OXC safe")

    hdr("Done")
    print(f"  Files created : {created}")
    print(f"  Files updated : {updated}")
    print()
    print("  5 Tier 2 features implemented:")
    print()
    print("  [1] Country click-to-filter")
    print("      Click any country polygon on the map to isolate its events")
    print("      Country name badge appears top-left with x to clear")
    print("      Same filter appears in the sidebar with a Clear button")
    print("      Hover over a country shows its name as a tooltip")
    print()
    print("  [2] Seasonal pattern heatmap")
    print("      Analytics tab: month x category grid, colour = event density")
    print("      Season bands overlay: MAM long rains, OND short rains, dry seasons")
    print("      Helps identify East Africa seasonal hazard patterns")
    print()
    print("  [3] Magnitude filter slider")
    print("      Sidebar shows slider when earthquakes / storms / floods active")
    print("      Slide right to hide low-magnitude events (e.g. M3.5+)")
    print("      Events without magnitude data always visible")
    print()
    print("  [4] Mobile responsive layout")
    print("      Sidebar slides in as overlay on screens < 768px")
    print("      Hamburger button opens/closes it with backdrop click to dismiss")
    print("      Stat cards switch to 2x2 grid")
    print("      Event list stacks below the map instead of right panel")
    print("      Top nav shows short 'NET-EA' title on mobile")
    print()
    print("  [5] Year-over-year comparison -- confirmed from setup_yoy.py")
    print("      Scroll to bottom of Analytics tab to see it")
    print()
    print("  No npm install needed. Restart Vite:")
    print("    cd frontend && npm run dev")
    print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Add Tier 2 features to NET-EA")
    parser.add_argument("--path", default=".", help="Project root (default: current dir)")
    args = parser.parse_args()
    root = Path(args.path).resolve()
    if not (root / "backend").exists():
        print(f"WARNING: {root} may not be project root. Continue? [y/N] ", end="")
        if input().strip().lower() != "y":
            sys.exit(0)
    build(root)

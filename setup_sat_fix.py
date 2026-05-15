"""
setup_sat_fix.py
----------------
Fixes the satellite button / dropdown being hidden behind the Leaflet map.

Root cause: Leaflet creates its own stacking context that overrides
z-index on siblings. The dropdown needs position:fixed so it escapes
the Leaflet stacking context entirely.

Changes:
  - Satellite button gets a useRef to measure its screen position
  - Dropdown renders with position:fixed + computed top/right coords
  - Button z-index raised to 1001 to stay above all Leaflet layers
  - Close-on-outside-click behaviour added via useEffect

Run from the eonet-east-africa project root:
    python setup_sat_fix.py
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
# MapPanel.jsx -- fixed-position satellite dropdown
# =============================================================================
FILES["frontend/src/components/MapPanel.jsx"] = r"""import React, { useEffect, useState, useCallback, useRef } from 'react'
import {
  MapContainer, TileLayer, WMSTileLayer, CircleMarker,
  Popup, GeoJSON, Rectangle, useMap,
} from 'react-leaflet'
import MarkerClusterGroup from 'react-leaflet-cluster'
import 'leaflet/dist/leaflet.css'
import useAppStore, { CATEGORIES } from '../store/useAppStore.js'
import { useEvents } from '../api/queries.js'

// -- ICPAC region constants ------------------------------------------------
const ICPAC_CENTER   = [6.5, 38.0]
const MAX_BOUNDS     = [[-16.0, 18.0], [26.0, 56.0]]
const REGION_BOUNDS  = [[-12.0, 22.0], [23.0, 52.0]]
const ICPAC_ISO2     = ['DJ','ER','ET','KE','RW','SO','SS','SD','TZ','UG','BI']
const GEO_BASE       = 'https://raw.githubusercontent.com/johan/world.geo.json/master/countries'

const TILE_LIGHT       = 'https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png'
const TILE_DARK        = 'https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png'
const TILE_LBL_LIGHT   = 'https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}{r}.png'
const TILE_LBL_DARK    = 'https://{s}.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}{r}.png'
const ATTR             = '(c) OpenStreetMap contributors, (c) CARTO | NASA EONET v3'
const GIBS_WMS         = 'https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi'

const GIBS_LAYERS = [
  { id: 'MODIS_Terra_CorrectedReflectance_TrueColor', label: 'True colour (Terra)'  },
  { id: 'VIIRS_SNPP_CorrectedReflectance_TrueColor',  label: 'True colour (VIIRS)'  },
  { id: 'FIRMS_VIIRS_375m_FireAndThermalAnomalies',   label: 'Fire detections'       },
  { id: 'MODIS_Terra_Chlorophyll_A',                  label: 'Chlorophyll (Terra)'   },
]

function todayStr() { return new Date().toISOString().slice(0, 10) }

function getCatColor(cat) { return (CATEGORIES[cat] || {}).color || '#484f58' }

function worldviewURL(ev) {
  if (!ev.coords) return null
  const lon  = ev.coords[0]; const lat = ev.coords[1]; const pad = 3
  const date = (ev.latest_date || todayStr()).slice(0, 10)
  const bbox = (lon-pad)+','+(lat-pad)+','+(lon+pad)+','+(lat+pad)
  return 'https://worldview.earthdata.nasa.gov/?v=' + bbox + '&t=' + date
}

// -- Leaflet helpers ---------------------------------------------------------

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
    [[-90,-180],[90,22.0]], [[-90,52.0],[90,180]],
    [[23.0,22.0],[90,52.0]], [[-90,22.0],[-12.0,52.0]],
  ]
  return strips.map((b, i) => (
    <Rectangle key={i} bounds={b}
      pathOptions={{ color:'transparent', fillColor:'#000', fillOpacity:0.4, weight:0 }} />
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
  return <GeoJSON key={'c-'+(lightMode?'l':'d')} data={geo} style={style} />
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
      <td style={{ color:'var(--text-muted)', paddingRight:10, paddingBottom:3,
                   whiteSpace:'nowrap', fontSize:12 }}>{label}</td>
      <td style={{ color:'var(--text-secondary)', paddingBottom:3, fontSize:12 }}>{value}</td>
    </tr>
  )
}

// -- Satellite control rendered OUTSIDE Leaflet (fixed position) --------------

function SatelliteControl({ satOn, setSatOn, satLayer, setSatLayer, satDate, setSatDate }) {
  const [open, setOpen]   = useState(false)
  const btnRef            = useRef(null)
  const [pos, setPos]     = useState({ top: 0, right: 0 })

  function openPanel() {
    if (btnRef.current) {
      const r = btnRef.current.getBoundingClientRect()
      setPos({ top: r.bottom + 6, right: window.innerWidth - r.right })
    }
    setOpen((v) => !v)
  }

  // Close when clicking outside
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
      {/* The button sits in the map overlay (position:absolute) */}
      <button
        ref={btnRef}
        onClick={openPanel}
        style={{
          fontSize: 11, padding: '4px 10px', borderRadius: 6,
          border: '1px solid',
          borderColor: satOn ? '#378ADD' : 'var(--border-primary)',
          background:  satOn
            ? 'rgba(55,138,221,0.15)'
            : 'rgba(255,255,255,0.92)',
          color:       satOn ? '#185FA5' : 'var(--text-secondary)',
          cursor: 'pointer', fontWeight: satOn ? 600 : 400,
          boxShadow: '0 1px 4px rgba(0,0,0,0.12)',
        }}
      >
        Satellite{satOn ? ' (on)' : ''}
      </button>

      {/* Dropdown rendered at fixed position -- escapes Leaflet stacking context */}
      {open && (
        <div
          id="sat-panel"
          style={{
            position: 'fixed',
            top:   pos.top,
            right: pos.right,
            zIndex: 99999,
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-primary)',
            borderRadius: 10,
            padding: '14px 16px',
            minWidth: 250,
            boxShadow: '0 8px 28px rgba(0,0,0,0.18)',
          }}
        >
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)',
                        marginBottom: 12, paddingBottom: 8,
                        borderBottom: '1px solid var(--border-muted)' }}>
            NASA GIBS Satellite Layer
          </div>

          {GIBS_LAYERS.map((gl) => (
            <label key={gl.id} style={{ display:'flex', alignItems:'center',
                                        gap: 8, marginBottom: 8, cursor: 'pointer' }}>
              <input
                type="radio"
                name="gibs-layer"
                checked={satLayer === gl.id}
                onChange={() => setSatLayer(gl.id)}
                style={{ accentColor: '#378ADD' }}
              />
              <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                {gl.label}
              </span>
            </label>
          ))}

          <div style={{ marginTop: 12, paddingTop: 10,
                        borderTop: '1px solid var(--border-muted)' }}>
            <div style={{ fontSize: 11, fontWeight: 500,
                          color: 'var(--text-muted)', marginBottom: 5 }}>
              Image date
            </div>
            <input
              type="date"
              value={satDate}
              max={todayStr()}
              onChange={(e) => setSatDate(e.target.value)}
              style={{
                width: '100%', fontSize: 12, padding: '5px 8px',
                border: '1px solid var(--border-primary)', borderRadius: 5,
                background: 'var(--bg-elevated)', color: 'var(--text-primary)',
              }}
            />
          </div>

          <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
            <button
              onClick={() => { setSatOn(true); setOpen(false) }}
              style={{
                flex: 1, padding: '6px', borderRadius: 6, fontSize: 12,
                border: 'none', background: '#378ADD', color: '#fff',
                cursor: 'pointer', fontWeight: 500,
              }}
            >
              Apply
            </button>
            <button
              onClick={() => { setSatOn(false); setOpen(false) }}
              style={{
                flex: 1, padding: '6px', borderRadius: 6, fontSize: 12,
                border: '1px solid var(--border-primary)',
                background: 'transparent', color: 'var(--text-secondary)',
                cursor: 'pointer',
              }}
            >
              Turn off
            </button>
          </div>

          {satOn && (
            <div style={{ marginTop: 8, fontSize: 11, color: '#378ADD',
                          textAlign: 'center' }}>
              Satellite layer is active
            </div>
          )}
        </div>
      )}
    </>
  )
}

// -- Main MapPanel -----------------------------------------------------------

export default function MapPanel({ height }) {
  const { activeCategories, activeStatus,
          selectedEventId, selectEvent, lightMode } = useAppStore()
  const { data: rawEvents = [], isLoading } = useEvents()

  const [geo,      setGeo]      = useState(null)
  const [satOn,    setSatOn]    = useState(false)
  const [satLayer, setSatLayer] = useState(GIBS_LAYERS[0].id)
  const [satDate,  setSatDate]  = useState(todayStr)

  // Fetch country boundaries once
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
          ...f,
          properties: { ...(f.properties || {}), iso2: ICPAC_ISO2[i] },
        }))
      })
      if (features.length) setGeo({ type: 'FeatureCollection', features })
    })
  }, [])

  // Apply local filters
  const events = rawEvents.filter((ev) => {
    if (!activeCategories.includes(ev.category)) return false
    if (activeStatus === 'open'   && ev.status !== 'open')   return false
    if (activeStatus === 'closed' && ev.status !== 'closed') return false
    return ev.coords != null
  })

  return (
    <div style={{
      flex: 1, position: 'relative',
      background: lightMode ? '#e8f0e0' : '#0d1117',
      minHeight: height || 340,
      overflow: 'hidden',
    }}>
      {/* Loading overlay */}
      {isLoading && (
        <div style={{
          position: 'absolute', inset: 0, zIndex: 1000,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: 'rgba(246,248,250,0.75)', fontSize: 13,
          color: 'var(--text-secondary)', pointerEvents: 'none',
        }}>
          Loading events...
        </div>
      )}

      {/* -- Map overlay controls (position:absolute, z-index > leaflet) -- */}

      {/* Region badge -- top left */}
      <div style={{
        position: 'absolute', top: 10, left: 10, zIndex: 1001,
        background: 'rgba(255,255,255,0.92)',
        border: '1px solid var(--border-primary)', borderRadius: 6,
        padding: '4px 10px', fontSize: 11, fontWeight: 600,
        color: '#1D9E75', letterSpacing: '0.05em',
        pointerEvents: 'none',
        boxShadow: '0 1px 4px rgba(0,0,0,0.10)',
      }}>
        Greater Horn of Africa
      </div>

      {/* Top-right: satellite control + event count */}
      <div style={{
        position: 'absolute', top: 10, right: 10, zIndex: 1001,
        display: 'flex', gap: 6, alignItems: 'flex-start',
      }}>
        <SatelliteControl
          satOn={satOn} setSatOn={setSatOn}
          satLayer={satLayer} setSatLayer={setSatLayer}
          satDate={satDate} setSatDate={setSatDate}
        />
        <div style={{
          background: 'rgba(255,255,255,0.92)',
          border: '1px solid var(--border-primary)', borderRadius: 6,
          padding: '4px 10px', fontSize: 12, color: 'var(--text-secondary)',
          pointerEvents: 'none',
          boxShadow: '0 1px 4px rgba(0,0,0,0.10)',
        }}>
          {events.length} event{events.length !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Legend -- bottom left */}
      <div style={{
        position: 'absolute', bottom: 30, left: 10, zIndex: 1001,
        background: 'rgba(255,255,255,0.92)',
        border: '1px solid var(--border-primary)',
        borderRadius: 6, padding: '8px 10px',
        pointerEvents: 'none',
        boxShadow: '0 1px 4px rgba(0,0,0,0.10)',
      }}>
        <div style={{ fontSize: 10, color: 'var(--text-muted)',
                      textTransform: 'uppercase', letterSpacing: '0.06em',
                      marginBottom: 4, fontWeight: 600 }}>Legend</div>
        <LegendRow color="#1D9E75" label="Open event"   dash={false} />
        <LegendRow color="#6e7681" label="Closed event" dash={true}  />
      </div>

      {/* -- Leaflet map -- */}
      <MapContainer
        center={ICPAC_CENTER} zoom={5}
        minZoom={4} maxZoom={10}
        maxBounds={MAX_BOUNDS} maxBoundsViscosity={0.85}
        style={{ width: '100%', height: '100%', position: 'absolute', inset: 0 }}
      >
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
          <WMSTileLayer
            url={GIBS_WMS}
            layers={satLayer}
            format="image/jpeg"
            version="1.1.1"
            time={satDate}
            opacity={0.72}
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
                    <div style={{ marginBottom: 8, display: 'flex',
                                  gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
                      <span style={{
                        fontSize: 11, fontWeight: 500, padding: '2px 8px',
                        borderRadius: 100, background: color+'33', color: color,
                        border: '1px solid ' + color + '55',
                      }}>
                        {cat.label || ev.category}
                      </span>
                      <span style={{ fontSize: 11, fontWeight: 600,
                                     color: isOpen ? '#1D9E75' : '#6e7681' }}>
                        {isOpen ? 'OPEN' : 'CLOSED'}
                      </span>
                    </div>

                    <p style={{ fontWeight: 600, fontSize: 13,
                                color: 'var(--text-primary)', lineHeight: 1.4,
                                marginBottom: 8 }}>
                      {ev.title}
                    </p>

                    <table style={{ borderCollapse: 'collapse', width: '100%' }}>
                      <tbody>
                        <PopupRow label="Date"
                          value={(ev.latest_date || '--').slice(0, 10)} />
                        {ev.closed && (
                          <PopupRow label="Closed" value={ev.closed.slice(0, 10)} />
                        )}
                        {ev.magnitude && (
                          <PopupRow label="Magnitude"
                            value={ev.magnitude.value+' '+(ev.magnitude.unit||'')} />
                        )}
                        <PopupRow label="Coords"
                          value={ev.coords[1].toFixed(2)+', '+ev.coords[0].toFixed(2)} />
                      </tbody>
                    </table>

                    <div style={{ marginTop: 10, display: 'flex',
                                  gap: 10, flexWrap: 'wrap' }}>
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
                          EONET
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
# Builder
# =============================================================================
def build(root: Path):
    hdr(f"Applying satellite z-index fix in: {root}")
    fe = root / "frontend"

    target = fe / "src/components/MapPanel.jsx"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(FILES["frontend/src/components/MapPanel.jsx"], encoding="utf-8")
    ow("update  frontend/src/components/MapPanel.jsx")

    hdr("Done")
    print()
    print("  Fix summary:")
    print("    SatelliteControl is now a separate component")
    print("    Dropdown uses position:fixed with coords from getBoundingClientRect()")
    print("    z-index: 99999 -- escapes Leaflet stacking context completely")
    print("    Close-on-outside-click via mousedown event listener")
    print("    All map overlays (badge, legend, event count) raised to z-index: 1001")
    print()
    print("  No npm install needed -- just restart Vite:")
    print("    cd frontend && npm run dev")
    print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Fix satellite panel z-index issue")
    parser.add_argument("--path", default=".", help="Project root (default: current dir)")
    args   = parser.parse_args()
    root   = Path(args.path).resolve()
    if not (root / "backend").exists():
        print(f"WARNING: {root} may not be project root. Continue? [y/N] ", end="")
        if input().strip().lower() != "y":
            sys.exit(0)
    build(root)

"""
setup_about.py
--------------
Three changes in one script:
  1. Title renamed to "Natural Event Tracker for East Africa"
  2. Two new event categories added: Temperature Extremes + Water Color
  3. About tab added with full dashboard documentation

Run from the eonet-east-africa project root:
    python setup_about.py

Files updated/created:
    frontend/index.html
    frontend/src/store/useAppStore.js   -- 2 new categories
    frontend/src/api/queries.js         -- mock events for new categories
    frontend/src/components/TopNav.jsx  -- new title
    frontend/src/components/AboutPanel.jsx  -- NEW
    frontend/src/App.jsx                -- adds About tab
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
# index.html
# =============================================================================
FILES["index.html"] = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Natural Event Tracker for East Africa</title>
    <meta name="description"
      content="Near real-time natural hazard monitoring for the ICPAC Greater Horn of Africa region, powered by NASA EONET v3." />
    <link rel="icon" type="image/svg+xml"
      href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>satellite</text></svg>" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
"""

# =============================================================================
# useAppStore.js  --  add 2 new categories
# =============================================================================
FILES["src/store/useAppStore.js"] = """import { create } from 'zustand'

export const CATEGORIES = {
  wildfires:           { label: 'Wildfires',            color: '#E8593C' },
  severeStorms:        { label: 'Severe Storms',         color: '#378ADD' },
  floods:              { label: 'Floods',                color: '#1D9E75' },
  drought:             { label: 'Drought',               color: '#BA7517' },
  volcanoes:           { label: 'Volcanoes',             color: '#E24B4A' },
  dustHaze:            { label: 'Dust and Haze',         color: '#888780' },
  earthquakes:         { label: 'Earthquakes',           color: '#7F77DD' },
  landslides:          { label: 'Landslides',            color: '#639922' },
  temperatureExtremes: { label: 'Temperature Extremes',  color: '#E85D24' },
  waterColor:          { label: 'Water Color',           color: '#1D6FA5' },
}

export const ALL_CATS = Object.keys(CATEGORIES)

const useAppStore = create((set) => ({
  activeCategories: ALL_CATS,
  activeStatus:     'all',
  lookbackDays:     90,
  selectedEventId:  null,
  lightMode:        true,
  sidebarOpen:      true,
  dataSource:       'auto',

  toggleCategory: (cat) => set((s) => ({
    activeCategories: s.activeCategories.includes(cat)
      ? s.activeCategories.filter((c) => c !== cat)
      : [...s.activeCategories, cat],
  })),
  setAllCategories: (cats) => set({ activeCategories: cats }),
  setStatus:        (v)    => set({ activeStatus: v }),
  setDays:          (v)    => set({ lookbackDays: v }),
  selectEvent:      (id)   => set({ selectedEventId: id }),
  toggleLight: () => set((s) => {
    const next = !s.lightMode
    document.documentElement.classList.toggle('light', next)
    return { lightMode: next }
  }),
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setDataSource:  (v)    => set({ dataSource: v }),
}))

if (typeof document !== 'undefined') {
  document.documentElement.classList.add('light')
}

export default useAppStore
"""

# =============================================================================
# queries.js  --  add mock events for new categories
# =============================================================================
FILES["src/api/queries.js"] = """import { useQuery } from '@tanstack/react-query'
import useAppStore from '../store/useAppStore.js'

export const MOCK_EVENTS = [
  { id:'EONET_6001', title:'Wildfire - Marsabit County, Kenya',            category:'wildfires',           status:'open',   closed:null,        latest_date:'2025-03-15', coords:[37.97,2.34],   sources:[{id:'MODIS_C6_Terra',url:'https://earthdata.nasa.gov/firms'}],         magnitude:null },
  { id:'EONET_6002', title:'Wildfire - Serengeti-Mara, Tanzania',          category:'wildfires',           status:'closed', closed:'2025-02-28', latest_date:'2025-02-20', coords:[34.83,-2.31],  sources:[{id:'MODIS_C6_Aqua',url:'https://earthdata.nasa.gov/firms'}],          magnitude:null },
  { id:'EONET_6003', title:'Wildfire - Ogaden, Somali Region, Ethiopia',   category:'wildfires',           status:'open',   closed:null,        latest_date:'2025-03-22', coords:[43.52,7.86],   sources:[{id:'VIIRS_SNPP_NRT',url:'https://earthdata.nasa.gov/firms'}],         magnitude:null },
  { id:'EONET_6004', title:'Flood - Tana River Basin, Kenya',              category:'floods',              status:'closed', closed:'2025-04-02', latest_date:'2025-03-10', coords:[40.12,-0.52],  sources:[{id:'GDACS',url:'https://gdacs.org'}],                                 magnitude:{value:3.5,unit:'m'} },
  { id:'EONET_6005', title:'Flood - Sobat River, South Sudan',             category:'floods',              status:'open',   closed:null,        latest_date:'2025-03-05', coords:[33.57,9.34],   sources:[{id:'GDACS',url:'https://gdacs.org'}],                                 magnitude:{value:2.1,unit:'m'} },
  { id:'EONET_6006', title:'Dust and Haze - Horn of Africa',               category:'dustHaze',            status:'open',   closed:null,        latest_date:'2025-03-20', coords:[44.51,8.12],   sources:[{id:'MODIS_C6_Aqua',url:'https://worldview.earthdata.nasa.gov'}],      magnitude:null },
  { id:'EONET_6007', title:'Dust and Haze - Lake Turkana Region',          category:'dustHaze',            status:'closed', closed:'2025-02-16', latest_date:'2025-02-14', coords:[36.10,3.55],   sources:[{id:'MODIS_C6_Terra',url:'https://worldview.earthdata.nasa.gov'}],     magnitude:null },
  { id:'EONET_6008', title:'Volcano - Ol Doinyo Lengai, Tanzania',         category:'volcanoes',           status:'open',   closed:null,        latest_date:'2025-01-10', coords:[35.90,-2.76],  sources:[{id:'Smithsonian_GVP',url:'https://volcano.si.edu'}],                  magnitude:null },
  { id:'EONET_6009', title:'Earthquake - East African Rift, Tanzania',     category:'earthquakes',         status:'closed', closed:'2025-03-25', latest_date:'2025-03-25', coords:[29.68,-7.12],  sources:[{id:'USGS_EHP',url:'https://earthquake.usgs.gov'}],                    magnitude:{value:4.5,unit:'Richter'} },
  { id:'EONET_6010', title:'Severe Storm - Tropical Cyclone Jude',         category:'severeStorms',        status:'closed', closed:'2025-03-18', latest_date:'2025-03-12', coords:[40.30,-14.20], sources:[{id:'JTWC',url:'https://www.metoc.navy.mil/jtwc/jtwc.html'}],          magnitude:{value:95,unit:'kts'} },
  { id:'EONET_6011', title:'Drought - Horn of Africa',                     category:'drought',             status:'open',   closed:null,        latest_date:'2024-12-01', coords:[43.14,10.30],  sources:[{id:'FEWS_NET',url:'https://fews.net'}],                               magnitude:null },
  { id:'EONET_6012', title:'Landslide - Kericho County, Kenya Highlands',  category:'landslides',          status:'closed', closed:'2025-03-28', latest_date:'2025-03-28', coords:[35.28,-0.37],  sources:[{id:'ReliefWeb',url:'https://reliefweb.int'}],                         magnitude:null },
  { id:'EONET_6013', title:'Heat Extreme - Somalia and Eastern Ethiopia',   category:'temperatureExtremes', status:'open',   closed:null,        latest_date:'2025-03-18', coords:[45.34,9.00],   sources:[{id:'GHCN',url:'https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily'}], magnitude:{value:43.2,unit:'C'} },
  { id:'EONET_6014', title:'Temperature Extreme - Cold Snap Ethiopian Highlands', category:'temperatureExtremes', status:'closed', closed:'2025-02-10', latest_date:'2025-02-08', coords:[38.75,9.02], sources:[{id:'GHCN',url:'https://www.ncei.noaa.gov'}], magnitude:{value:2.1,unit:'C'} },
  { id:'EONET_6015', title:'Water Color - Lake Victoria Algal Bloom',       category:'waterColor',          status:'open',   closed:null,        latest_date:'2025-03-30', coords:[32.90,-0.40],  sources:[{id:'OB_DAAC',url:'https://oceancolor.gsfc.nasa.gov'}],                magnitude:null },
]

const MOCK_SUMMARY = {
  total: 15,
  open: 8,
  closed: 7,
  by_category: {
    wildfires:3, floods:2, dustHaze:2, volcanoes:1, earthquakes:1,
    severeStorms:1, drought:1, landslides:1,
    temperatureExtremes:2, waterColor:1
  }
}

const API = import.meta.env.VITE_API_BASE_URL || ''

async function fetchEvents(days, status) {
  const params = new URLSearchParams({ days, status })
  const res = await fetch(API + '/events?' + params)
  if (!res.ok) throw new Error('HTTP ' + res.status)
  const data = await res.json()
  return data.events || []
}

async function fetchSummary() {
  const res = await fetch(API + '/summary')
  if (!res.ok) throw new Error('HTTP ' + res.status)
  return res.json()
}

async function fetchStatus() {
  const res = await fetch(API + '/status')
  if (!res.ok) throw new Error('HTTP ' + res.status)
  return res.json()
}

export function useEvents() {
  const { activeStatus, lookbackDays, dataSource } = useAppStore()
  return useQuery({
    queryKey: ['events', activeStatus, lookbackDays, dataSource],
    queryFn: async () => {
      if (dataSource === 'mock') return MOCK_EVENTS
      try { return await fetchEvents(lookbackDays, activeStatus) }
      catch { console.warn('[useEvents] backend unreachable -- using mock'); return MOCK_EVENTS }
    },
    staleTime: 10 * 60 * 1000,
  })
}

export function useSummary() {
  const { dataSource } = useAppStore()
  return useQuery({
    queryKey: ['summary', dataSource],
    queryFn: async () => {
      if (dataSource === 'mock') return MOCK_SUMMARY
      try { return await fetchSummary() } catch { return MOCK_SUMMARY }
    },
    staleTime: 10 * 60 * 1000,
  })
}

export function useCacheStatus() {
  const { dataSource } = useAppStore()
  return useQuery({
    queryKey: ['cache_status', dataSource],
    queryFn: async () => {
      if (dataSource === 'mock') return { cached: false, event_count: 15, note: 'offline mock' }
      try { return await fetchStatus() } catch { return null }
    },
    refetchInterval: 60 * 1000,
  })
}
"""

# =============================================================================
# TopNav.jsx  --  new title
# =============================================================================
FILES["src/components/TopNav.jsx"] = """import React from 'react'
import useAppStore from '../store/useAppStore.js'
import { useCacheStatus } from '../api/queries.js'

export default function TopNav() {
  const { lightMode, toggleLight, toggleSidebar, dataSource, setDataSource } = useAppStore()
  const { data: cacheInfo } = useCacheStatus()
  const isMock = dataSource === 'mock'

  return (
    <header style={{
      height: 'var(--topnav-h)',
      background: 'var(--bg-surface)',
      borderBottom: '1px solid var(--border-primary)',
      display: 'flex', alignItems: 'center',
      padding: '0 16px', gap: 10, flexShrink: 0, zIndex: 100,
    }}>
      <button onClick={toggleSidebar} title="Toggle sidebar" style={btnStyle}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
          <rect x="1" y="3"    width="14" height="1.5" rx="0.75"/>
          <rect x="1" y="7.25" width="14" height="1.5" rx="0.75"/>
          <rect x="1" y="11.5" width="14" height="1.5" rx="0.75"/>
        </svg>
      </button>

      {/* Satellite icon */}
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
           stroke="#1D9E75" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M13 7L17 3M17 3L21 7M17 3V13"/>
        <circle cx="9" cy="15" r="4"/>
        <path d="M3 21L7 17"/>
        <path d="M9 11L13 7"/>
      </svg>

      {/* Title */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        <span style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-primary)',
                       lineHeight: 1, letterSpacing: '-0.01em' }}>
          Natural Event Tracker
        </span>
        <span style={{ fontSize: 10, color: '#1D9E75', fontWeight: 500,
                       letterSpacing: '0.04em', textTransform: 'uppercase' }}>
          East Africa
        </span>
      </div>

      {/* Divider */}
      <div style={{ width: 1, height: 28, background: 'var(--border-primary)',
                    margin: '0 4px' }} />

      <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>
        ICPAC GHA Region
      </span>

      <div style={{ flex: 1 }} />

      {isMock && (
        <span style={{ fontSize: 11, fontWeight: 500, padding: '2px 8px',
                       borderRadius: 100, background: '#412402', color: '#FAC775',
                       border: '1px solid #633806' }}>
          OFFLINE MOCK
        </span>
      )}

      {cacheInfo && !isMock && (
        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
          {cacheInfo.event_count} events
          {cacheInfo.ttl_remaining_s != null
            ? ' -- refresh in ' + Math.ceil(cacheInfo.ttl_remaining_s / 60) + 'm'
            : ''}
        </span>
      )}

      <button
        onClick={() => setDataSource(isMock ? 'auto' : 'mock')}
        style={{ ...btnStyle, fontSize: 11, padding: '4px 10px', borderRadius: 6,
                 background: isMock ? 'var(--bg-elevated)' : 'transparent' }}
      >
        {isMock ? 'Use live API' : 'Use mock'}
      </button>

      <button onClick={toggleLight} title="Toggle light mode" style={btnStyle}>
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

      <span style={{ fontSize: 11, fontWeight: 600, padding: '3px 8px',
                     border: '1px solid var(--border-primary)', borderRadius: 6,
                     color: 'var(--text-secondary)' }}>
        ILRI
      </span>
    </header>
  )
}

const btnStyle = {
  background: 'transparent', border: 'none',
  color: 'var(--text-secondary)', cursor: 'pointer',
  padding: '6px', borderRadius: 6,
  display: 'flex', alignItems: 'center', fontSize: 13,
}
"""

# =============================================================================
# AboutPanel.jsx  --  full dashboard documentation page
# =============================================================================
FILES["src/components/AboutPanel.jsx"] = """import React from 'react'
import { CATEGORIES } from '../store/useAppStore.js'

// ---- Small layout helpers ----

function Section({ title, children }) {
  return (
    <section style={{ marginBottom: 32 }}>
      <h2 style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)',
                   marginBottom: 12, paddingBottom: 8,
                   borderBottom: '1px solid var(--border-primary)' }}>
        {title}
      </h2>
      {children}
    </section>
  )
}

function Para({ children }) {
  return (
    <p style={{ fontSize: 13, color: 'var(--text-secondary)',
                lineHeight: 1.75, marginBottom: 10 }}>
      {children}
    </p>
  )
}

function InfoRow({ label, value, link }) {
  return (
    <div style={{ display: 'flex', gap: 10, padding: '7px 0',
                  borderBottom: '1px solid var(--border-muted)',
                  alignItems: 'flex-start' }}>
      <span style={{ fontSize: 12, color: 'var(--text-muted)', width: 160,
                     flexShrink: 0, paddingTop: 1 }}>
        {label}
      </span>
      {link ? (
        <a href={link} target="_blank" rel="noreferrer"
           style={{ fontSize: 13, color: '#378ADD', textDecoration: 'none' }}>
          {value}
        </a>
      ) : (
        <span style={{ fontSize: 13, color: 'var(--text-primary)', flex: 1 }}>{value}</span>
      )}
    </div>
  )
}

function UsageCard({ icon, title, items }) {
  return (
    <div style={{ background: 'var(--bg-elevated)',
                  border: '1px solid var(--border-primary)',
                  borderRadius: 'var(--radius-md)', padding: '12px 14px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <span style={{ fontSize: 18 }}>{icon}</span>
        <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
          {title}
        </span>
      </div>
      <ul style={{ paddingLeft: 16 }}>
        {items.map((item, i) => (
          <li key={i} style={{ fontSize: 12, color: 'var(--text-secondary)',
                               lineHeight: 1.7, marginBottom: 2 }}>
            {item}
          </li>
        ))}
      </ul>
    </div>
  )
}

// ---- Main component ----

export default function AboutPanel() {
  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: '24px 32px',
                  maxWidth: 820, margin: '0 auto' }}>

      {/* Header */}
      <div style={{ marginBottom: 32, paddingBottom: 20,
                    borderBottom: '2px solid #1D9E75' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12,
                      marginBottom: 8 }}>
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none"
               stroke="#1D9E75" strokeWidth="1.8" strokeLinecap="round"
               strokeLinejoin="round">
            <path d="M13 7L17 3M17 3L21 7M17 3V13"/>
            <circle cx="9" cy="15" r="4"/>
            <path d="M3 21L7 17"/>
            <path d="M9 11L13 7"/>
          </svg>
          <div>
            <h1 style={{ fontSize: 20, fontWeight: 600, color: 'var(--text-primary)',
                         lineHeight: 1, marginBottom: 4 }}>
              Natural Event Tracker for East Africa
            </h1>
            <p style={{ fontSize: 12, color: '#1D9E75', fontWeight: 500,
                        letterSpacing: '0.04em', textTransform: 'uppercase' }}>
              NET-EA -- Version 2.0
            </p>
          </div>
        </div>
        <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
          A near real-time natural hazard monitoring dashboard for the ICPAC
          Greater Horn of Africa region, powered by the NASA Earth Observatory
          Natural Event Tracker (EONET) API v3.
        </p>
      </div>

      {/* Purpose */}
      <Section title="Purpose">
        <Para>
          The Natural Event Tracker for East Africa (NET-EA) was developed at
          the International Livestock Research Institute (ILRI) Climate Services
          unit to provide a unified, accessible view of natural hazard events
          across the 11-country ICPAC Greater Horn of Africa (GHA) region.
          It bridges the gap between raw NASA satellite-derived event metadata
          and actionable situational awareness for climate, agriculture, and
          humanitarian professionals working in the region.
        </Para>
        <Para>
          The dashboard integrates event categories that are most relevant to
          East Africa -- wildfires, floods, drought, dust storms, earthquakes,
          volcanoes, landslides, severe storms, temperature extremes, and water
          color anomalies -- and presents them on an interactive map with
          filtering, analytics, and export capabilities.
        </Para>
        <Para>
          It is designed to complement, not replace, official operational
          monitoring systems such as ICPAC Drought Watch, FEWS NET, and GDACS.
          All event metadata is sourced directly from NASA EONET and reflects
          the quality and completeness of that upstream dataset.
        </Para>
      </Section>

      {/* ICPAC Region */}
      <Section title="ICPAC Greater Horn of Africa region">
        <Para>
          The dashboard is geographically scoped to the 11-country ICPAC GHA
          region using the bounding box 21.8 E to 51.4 E, 11.7 S to 22.0 N.
          Events outside this region are excluded from all views.
        </Para>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)',
                      gap: 6, marginBottom: 14 }}>
          {['Sudan','South Sudan','Ethiopia','Eritrea','Djibouti','Somalia',
            'Kenya','Uganda','Tanzania','Rwanda','Burundi'].map((c) => (
            <div key={c} style={{ fontSize: 12, padding: '5px 10px',
                                  background: '#E1F5EE',
                                  color: '#085041', borderRadius: 6,
                                  fontWeight: 500, textAlign: 'center' }}>
              {c}
            </div>
          ))}
        </div>
        <Para>
          Country-level event assignment uses bounding box lookup. Events near
          shared borders may be attributed to adjacent countries. For precise
          spatial analysis, use the GeoJSON export and cross-reference with
          official administrative boundaries.
        </Para>
      </Section>

      {/* Data source */}
      <Section title="Data source">
        <Para>
          All event data comes from the NASA Earth Observatory Natural Event
          Tracker (EONET) v3 API. EONET is a continuously updated metadata
          repository maintained by NASA Goddard Space Flight Center. It curates
          events from multiple upstream sources and links them to satellite
          imagery layers via NASA GIBS (Global Imagery Browse Services).
        </Para>
        <InfoRow label="Primary API"        value="NASA EONET v3"
          link="https://eonet.gsfc.nasa.gov/docs/v3" />
        <InfoRow label="GeoJSON endpoint"   value="eonet.gsfc.nasa.gov/api/v3/events/geojson" />
        <InfoRow label="Update frequency"   value="Near real-time -- events added within hours of detection" />
        <InfoRow label="Lookback window"    value="Up to 365 days; default is 90 days" />
        <InfoRow label="Bounding box param" value="21.8,22.0,51.4,-11.7 (min_lon, max_lat, max_lon, min_lat)" />
        <InfoRow label="Key upstream sources"
          value="MODIS/VIIRS (NASA), USGS EHP, GDACS, Smithsonian GVP, JTWC, FEWS NET, ReliefWeb" />
        <InfoRow label="Spatial formats"    value="Point and Polygon GeoJSON geometries" />
        <InfoRow label="Magnitude fields"   value="Available for storms (kts), earthquakes (Richter), floods (m), temperatures (C)" />
      </Section>

      {/* Event categories */}
      <Section title="Monitored event categories">
        <Para>
          Ten EONET event categories are currently monitored. Categories
          are displayed as colour-coded markers on the map and can be toggled
          individually from the filter sidebar.
        </Para>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          {Object.entries(CATEGORIES).map(([id, meta]) => (
            <div key={id} style={{
              display: 'flex', alignItems: 'flex-start', gap: 10,
              padding: '8px 10px',
              border: '1px solid var(--border-primary)',
              borderLeft: '3px solid ' + meta.color,
              borderRadius: 'var(--radius-md)',
              background: 'var(--bg-surface)',
            }}>
              <div>
                <div style={{ fontSize: 12, fontWeight: 600,
                              color: 'var(--text-primary)', marginBottom: 2 }}>
                  {meta.label}
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)',
                              fontFamily: 'var(--font-mono)' }}>
                  {id}
                </div>
              </div>
            </div>
          ))}
        </div>
      </Section>

      {/* Potential applications */}
      <Section title="Potential applications for East Africa">
        <Para>
          The dashboard is designed to serve a wide range of users and use
          cases across the region. Representative applications include:
        </Para>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr',
                      gap: 10, marginBottom: 14 }}>
          <UsageCard
            icon="food"
            title="Food security and agriculture"
            items={[
              'Monitor drought onset and progression during growing seasons',
              'Track wildfire spread in agricultural buffer zones and rangelands',
              'Identify flood events threatening crop areas along major river systems',
              'Alert livestock keepers to heat extremes in pastoral areas',
            ]}
          />
          <UsageCard
            icon="warning"
            title="Disaster risk reduction"
            items={[
              'Early situational awareness for multi-hazard events',
              'Support national disaster management authority reporting',
              'Identify compound events (e.g. drought followed by flood)',
              'Export GeoJSON for integration with GIS-based risk models',
            ]}
          />
          <UsageCard
            icon="globe"
            title="Climate services and research"
            items={[
              'Historical event frequency analysis across ICPAC GHA countries',
              'Cross-reference with seasonal forecast outlooks (e.g. MAM, OND)',
              'Track volcanic aerosol events with potential regional climate impacts',
              'Study interannual variability of fire and flood seasons',
            ]}
          />
          <UsageCard
            icon="heart"
            title="Humanitarian response"
            items={[
              'Monitor open events for active displacement-risk situations',
              'Identify affected countries for resource allocation decisions',
              'Link events to population exposure layers via GeoJSON export',
              'Support OCHA and WFP situation reporting workflows',
            ]}
          />
          <UsageCard
            icon="chart"
            title="Environmental monitoring"
            items={[
              'Track water color anomalies in Lake Victoria for fisheries alerts',
              'Monitor dust transport events affecting air quality',
              'Detect vegetation fire patterns linked to land degradation',
              'Observe earthquake activity along the East African Rift System',
            ]}
          />
          <UsageCard
            icon="settings"
            title="Technical integration"
            items={[
              'REST API backend for ingestion into institutional dashboards',
              'GeoJSON/CSV export for ArcGIS, QGIS, and Python geopandas workflows',
              'GitHub Pages deployment for low-infrastructure public access',
              'Docker Compose packaging for on-premise ILRI/ICPAC server deployment',
            ]}
          />
        </div>
      </Section>

      {/* Technical stack */}
      <Section title="Technical stack">
        <InfoRow label="Frontend"    value="React 18 + Vite, React-Leaflet, Recharts, Zustand, TanStack Query" />
        <InfoRow label="Backend"     value="FastAPI (Python 3.12), uvicorn, httpx, APScheduler" />
        <InfoRow label="Map"         value="Leaflet.js with CartoDB basemap tiles" />
        <InfoRow label="Boundaries"  value="Natural Earth via world.geo.json (MIT license)" />
        <InfoRow label="Deployment"  value="GitHub Pages (frontend), Docker Compose (backend)" />
        <InfoRow label="Refresh"     value="15-minute automatic cache refresh via APScheduler" />
        <InfoRow label="Offline mode" value="12-event mock dataset for development without network access" />
      </Section>

      {/* Credits */}
      <Section title="Credits and contacts">
        <InfoRow label="Built at"       value="ILRI Climate Services, Addis Ababa, Ethiopia"
          link="https://www.ilri.org" />
        <InfoRow label="In collaboration with" value="ICPAC (IGAD Climate Prediction and Applications Centre)"
          link="https://www.icpac.net" />
        <InfoRow label="Data provider"  value="NASA Goddard Space Flight Center -- EONET"
          link="https://eonet.gsfc.nasa.gov" />
        <InfoRow label="Satellite data" value="NASA MODIS, VIIRS, Ocean Color instruments" />
        <InfoRow label="Hazard sources" value="USGS, GDACS, Smithsonian GVP, JTWC, FEWS NET, ReliefWeb" />
        <InfoRow label="Open source"    value="MIT License -- source code on GitHub" />
      </Section>

      {/* Disclaimer */}
      <Section title="Disclaimer">
        <div style={{ background: '#FAEEDA', border: '1px solid #EF9F2755',
                      borderRadius: 'var(--radius-md)', padding: '12px 14px',
                      marginBottom: 10 }}>
          <p style={{ fontSize: 12, color: '#633806', lineHeight: 1.7 }}>
            This dashboard is intended for general situational awareness and
            research purposes only. Event metadata is sourced from NASA EONET
            and reflects the completeness and accuracy of that upstream dataset.
            It should not be used as the sole basis for operational disaster
            response decisions. For authoritative hazard information, consult
            ICPAC, national meteorological agencies, and official disaster
            management authorities in the relevant country.
          </p>
        </div>
        <Para>
          Data density for East Africa is lower than for North America and
          Europe in the EONET dataset, as NASA's primary data curation
          effort has historically focused on those regions. Some events
          may be absent or delayed. Drought events in particular are
          sparsely represented and should be supplemented with FEWS NET,
          NDVI, and SPI-based monitoring.
        </Para>
      </Section>

      {/* Footer */}
      <div style={{ borderTop: '1px solid var(--border-primary)',
                    paddingTop: 16, marginTop: 8,
                    display: 'flex', gap: 20, flexWrap: 'wrap',
                    alignItems: 'center' }}>
        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
          NET-EA v2.0 -- ILRI Climate Services 2025
        </span>
        <a href="https://eonet.gsfc.nasa.gov" target="_blank" rel="noreferrer"
           style={{ fontSize: 11, color: '#378ADD' }}>NASA EONET</a>
        <a href="https://www.icpac.net" target="_blank" rel="noreferrer"
           style={{ fontSize: 11, color: '#378ADD' }}>ICPAC</a>
        <a href="https://www.ilri.org" target="_blank" rel="noreferrer"
           style={{ fontSize: 11, color: '#378ADD' }}>ILRI</a>
      </div>
    </div>
  )
}
"""

# =============================================================================
# App.jsx  --  add About tab
# =============================================================================
FILES["src/App.jsx"] = """import React, { useState } from 'react'
import TopNav         from './components/TopNav.jsx'
import FilterSidebar  from './components/FilterSidebar.jsx'
import StatCards      from './components/StatCards.jsx'
import MapPanel       from './components/MapPanel.jsx'
import EventList      from './components/EventList.jsx'
import AnalyticsPanel from './components/AnalyticsPanel.jsx'
import AboutPanel     from './components/AboutPanel.jsx'
import useAppStore    from './store/useAppStore.js'

const TABS = [
  { id: 'map',       label: 'Map view'  },
  { id: 'analytics', label: 'Analytics' },
  { id: 'about',     label: 'About'     },
]

export default function App() {
  const { sidebarOpen } = useAppStore()
  const [activeTab, setActiveTab] = useState('map')

  // Sidebar and stat cards are only shown on map and analytics tabs
  const showSidebar  = sidebarOpen && activeTab !== 'about'
  const showStatCards = activeTab !== 'about'

  return (
    <div style={{ display: 'flex', flexDirection: 'column',
                  height: '100vh', overflow: 'hidden' }}>
      <TopNav />

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {showSidebar && <FilterSidebar />}

        <main style={{ flex: 1, display: 'flex', flexDirection: 'column',
                       overflow: 'hidden', minWidth: 0 }}>

          {showStatCards && <StatCards />}

          {/* Tab bar */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 2,
            padding: '8px 14px 0',
            borderBottom: '1px solid var(--border-primary)',
            background: 'var(--bg-base)',
            flexShrink: 0,
          }}>
            {TABS.map((tab) => {
              const active = activeTab === tab.id
              return (
                <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={{
                  padding: '6px 14px', fontSize: 13,
                  fontWeight: active ? 600 : 400,
                  color:  active ? 'var(--text-primary)' : 'var(--text-secondary)',
                  background: 'transparent', border: 'none',
                  borderBottom: '2px solid',
                  borderBottomColor: active ? '#1D9E75' : 'transparent',
                  cursor: 'pointer', transition: 'all 0.15s', marginBottom: -1,
                }}>
                  {tab.label}
                </button>
              )
            })}
            <div style={{ flex: 1 }} />
            {activeTab !== 'about' && (
              <span style={{ fontSize: 11, color: 'var(--text-muted)', paddingBottom: 6 }}>
                ICPAC GHA Region
              </span>
            )}
          </div>

          {activeTab === 'map' && (
            <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
              <MapPanel />
              <EventList />
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
# Builder
# =============================================================================
def build(root: Path):
    hdr(f"Applying title + categories + About tab in: {root}")
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
    print("  Changes applied:")
    print("    Title: 'Natural Event Tracker for East Africa' with satellite icon")
    print("    2 new categories: Temperature Extremes + Water Color")
    print("    About tab: purpose, region, data source, usage, credits, disclaimer")
    print("    Mock data: 15 events now (was 12), includes 2 new category examples")
    print()
    print("  Restart Vite:")
    print("    cd frontend && npm run dev")
    print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Title + About tab update")
    parser.add_argument("--path", default=".", help="Project root (default: current dir)")
    args   = parser.parse_args()
    root   = Path(args.path).resolve()
    if not (root / "backend").exists():
        print(f"WARNING: {root} may not be project root. Continue? [y/N] ", end="")
        if input().strip().lower() != "y":
            sys.exit(0)
    build(root)

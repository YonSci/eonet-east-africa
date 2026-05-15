import React from 'react'
import { CATEGORIES } from '../store/useAppStore.js'
import AlertSubscription from './AlertSubscription.jsx'

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
          A near real-time natural hazard monitoring dashboard for the NET-EA
          Greater Horn of Africa region, powered by the NASA Earth Observatory
          Natural Event Tracker (EONET) API v3.
        </p>
      </div>

      {/* Purpose */}
      <Section title="Purpose">
        <Para>
          The Natural Event Tracker for East Africa (NET-EA) provides a unified,
          accessible view of natural hazard events across the 11-country
          Greater Horn of Africa region. It bridges the gap between raw
          NASA satellite-derived event metadata and actionable situational
          awareness for climate, agriculture, and humanitarian professionals.
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
          monitoring systems such as NET-EA Drought Watch, FEWS NET, and GDACS.
          All event metadata is sourced directly from NASA EONET and reflects
          the quality and completeness of that upstream dataset.
        </Para>
      </Section>

      {/* NET-EA Region */}
      <Section title="Greater Horn of Africa region">
        <Para>
          The dashboard is geographically scoped to the 11-country Greater Horn
          of Africa region using the bounding box 21.8 E to 51.4 E, 11.7 S to 22.0 N.
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
              'Historical event frequency analysis across Greater Horn of Africa countries',
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
              'Docker Compose packaging for on-premise server deployment',
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
        <InfoRow label="Built at"       value="East Africa Climate Services" />
        <InfoRow label="Data region" value="Greater Horn of Africa (11 countries)" />
        <InfoRow label="Data provider"  value="NASA Goddard Space Flight Center -- EONET"
          link="https://eonet.gsfc.nasa.gov" />
        <InfoRow label="Satellite data" value="NASA MODIS, VIIRS, Ocean Color instruments" />
        <InfoRow label="Hazard sources" value="USGS, GDACS, Smithsonian GVP, JTWC, FEWS NET, ReliefWeb" />
        <InfoRow label="Open source"    value="MIT License -- source code on GitHub" />
      </Section>

      {/* Email alert subscriptions */}
      <Section title="Email alert subscriptions">
        <Para>
          Subscribe to receive email notifications when new events matching your
          selected categories and countries are detected during the 15-minute
          automatic refresh. Requires the FastAPI backend to be running with
          SMTP configured.
        </Para>
        <AlertSubscription />
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
            NET-EA, national meteorological agencies, and official disaster
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
          NET-EA v2.0 -- Natural Event Tracker for East Africa 2025
        </span>
        <a href="https://eonet.gsfc.nasa.gov" target="_blank" rel="noreferrer"
           style={{ fontSize: 11, color: '#378ADD' }}>NASA EONET</a>

      </div>
    </div>
  )
}

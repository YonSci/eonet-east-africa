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
    <div style={{ flex: 1, minHeight: 0, overflowY: 'auto', padding: '24px 32px',
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
              Natural Hazard Monitoring & Tracking for East Africa
            </h1>
            <p style={{ fontSize: 12, color: '#1D9E75', fontWeight: 500,
                        letterSpacing: '0.04em', textTransform: 'uppercase' }}>
              NHMT-EA -- Version 2.0
            </p>
          </div>
        </div>
        <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
          A near real-time natural hazard monitoring dashboard for the NHMT-EA
          Greater Horn of Africa region, powered by the NASA Earth Observatory
          Natural Hazard Monitoring & Tracking (EONET) API v3.
        </p>
      </div>

      {/* Purpose */}
      {/* Dashboard features */}
      <Section title="Dashboard features">

        {[
          {
            group: 'Map view',
            color: '#1D9E75',
            items: [
              ['Interactive Leaflet map', 'Greater Horn of Africa region with CartoDB basemap, light/dark tile layers, bounded to EA'],
              ['Marker clustering', 'Nearby events collapse into numbered clusters. Handles 180+ events cleanly'],
              ['Real country boundaries', 'Natural Earth 1:50m polygons for all 11 countries, embedded inline -- no network fetch'],
              ['Country click-to-filter', 'Click any country to highlight it and filter all events and charts to that country'],
              ['NASA GIBS satellite layers', 'True colour (Terra/VIIRS), fire detections, chlorophyll overlays. Date picker for historical imagery'],
              ['District boundaries', 'GADM Level-1 sub-national boundaries per country after selecting a country on the map'],
              ['Event popups', 'Category, status, title, date, magnitude, country, coordinates, source link, satellite image link'],
              ['Category bar strip', 'Proportional colour bar and clickable category pills showing live event counts below the map'],
            ]
          },
          {
            group: 'Filter sidebar',
            color: '#BA7517',
            items: [
              ['Status filter', 'Toggle between All events, Open only, and Closed only'],
              ['Time period filter', '7d / 14d / 30d / 60d / 90d / 180d / 365d lookback, or custom start and end date range'],
              ['Per-category magnitude sliders', 'Separate slider for earthquakes (Richter), storms (kts), floods (m), temperature (C)'],
              ['Category toggles', '10 event categories, colour-coded with live count badges. All/None shortcuts'],
              ['Saved filter presets', 'Save any filter combination by name. 3 built-in defaults. Stored in browser localStorage'],
            ]
          },
          {
            group: 'Event list panel',
            color: '#378ADD',
            items: [
              ['Scrollable event list', 'Sortable table: date, category pill, status, title. Click a row to fly the map to that event'],
              ['Event search', 'Filter the list by keyword matching title, category, or event ID'],
              ['CSV export', 'Download the current filtered event list with all fields including coordinates and magnitude'],
            ]
          },
          {
            group: 'Analytics tab',
            color: '#E8593C',
            items: [
              ['Category bar chart', 'Horizontal bars sorted by count. Click a bar to toggle that category on the map'],
              ['Monthly timeline', 'Area chart of total events per month over the selected period'],
              ['Status donut and sources', 'Open vs closed breakdown. Data sources bar chart (MODIS, USGS, GDACS, JTWC, etc.)'],
              ['Duration histogram', 'Closed event duration binned: under 1 day, 1-7 days, 8-30 days, over 30 days'],
              ['Country table', 'Events per country with open/closed split and proportional bar'],
              ['Seasonal heatmap', 'Month x category grid coloured by event density. MAM, OND, and dry season bands annotated'],
              ['Year-over-year comparison', 'Select any two years: category bars, dual-line monthly trend, biggest movers table'],
              ['GeoJSON and CSV export', 'Export filtered events as GeoJSON (QGIS/ArcGIS compatible) or CSV'],
            ]
          },
          {
            group: 'Sharing and export',
            color: '#639922',
            items: [
              ['Shareable URLs', 'Active filters encoded in the URL. Share button copies the link to clipboard with a toast confirmation'],
              ['PDF bulletin export', 'Print-optimised layout with header showing name, email, date generated, and active filters'],
            ]
          },
          {
            group: 'Alert subscriptions',
            color: '#1D9E75',
            items: [
              ['Browser notifications', 'Popup alert when the 15-minute refresh detects new events matching saved subscriptions'],
              ['Email alerts via EmailJS', 'Confirmation email on subscribe and alert email when new events are detected. No backend needed'],
              ['Subscription management', 'View, delete, and export subscriptions. Filter by category and country'],
            ]
          },
          {
            group: 'UX and accessibility',
            color: '#888780',
            items: [
              ['Mobile responsive layout', 'Sidebar slides in as overlay on small screens. 2x2 stat cards. Map stacks above event list'],
              ['Skeleton loading states', 'Pulsing placeholder shapes for stat cards while data fetches'],
              ['Network error panel', 'When NASA EONET is blocked (9s timeout), shows clear panel with fix options and retry button'],
              ['Toast notifications', 'Green toast when refresh detects new events. Auto-dismisses after 5 seconds'],
              ['Light and dark theme', 'Toggle in top nav. Map tiles, popups, and all UI components adapt'],
              ['Offline banner', 'Amber banner when network lost, green when reconnected. Backed by PWA service worker cache'],
            ]
          },
          {
            group: 'PWA and deployment',
            color: '#185FA5',
            items: [
              ['Installable PWA', 'Install button in browser address bar. Offline mode serves last cached EONET data for 24 hours'],
              ['Netlify deployment', 'netlify.toml auto-config. Browser-direct NASA fetch. SPA routing redirect included'],
              ['Podman containerisation', 'Containerfile.backend (FastAPI) and Containerfile.frontend (Nginx). Rootless, daemonless'],
              ['Hetzner server deployment', 'Deploy scripts: build locally, export images, scp to server, load and start with Nginx proxy'],
            ]
          },
        ].map(({ group, color, items }) => (
          <div key={group} style={{ marginBottom: 18 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <div style={{ width: 10, height: 10, borderRadius: '50%',
                            background: color, flexShrink: 0 }} />
              <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                {group}
              </span>
              <span style={{ fontSize: 11, color: 'var(--text-muted)',
                             background: 'var(--bg-elevated)',
                             padding: '1px 6px', borderRadius: 100 }}>
                {items.length}
              </span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 5,
                          paddingLeft: 18 }}>
              {items.map(([title, desc]) => (
                <div key={title} style={{
                  padding: '7px 10px',
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border-muted)',
                  borderLeft: '3px solid ' + color,
                  borderRadius: 'var(--radius-md)',
                }}>
                  <div style={{ fontSize: 12, fontWeight: 600,
                                color: 'var(--text-primary)', marginBottom: 2 }}>
                    {title}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)',
                                lineHeight: 1.4 }}>
                    {desc}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}

        <div style={{ marginTop: 8, padding: '8px 12px',
                      background: 'var(--bg-elevated)',
                      border: '1px solid var(--border-muted)',
                      borderRadius: 'var(--radius-md)',
                      fontSize: 11, color: 'var(--text-muted)',
                      display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 18, fontWeight: 600,
                         color: 'var(--text-secondary)' }}>40+</span>
          features across 8 functional areas -- all running on NASA EONET v3
          and Natural Earth public domain data.
        </div>
      </Section>

      <Section title="Purpose">
        <Para>
          The Natural Hazard Monitoring & Tracking for East Africa (NHMT-EA) provides a unified,
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
          monitoring systems such as NHMT-EA Drought Watch, FEWS NET, and GDACS.
          All event metadata is sourced directly from NASA EONET and reflects
          the quality and completeness of that upstream dataset.
        </Para>
      </Section>

      {/* NHMT-EA Region */}
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

            {/* Credits and contacts -- standalone block, no Section wrapper */}
      <div style={{ marginBottom: 32 }}>
        <h2 style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)',
                     marginBottom: 16, paddingBottom: 8,
                     borderBottom: '1px solid var(--border-primary)' }}>
          Credits and contacts
        </h2>

        {/* --- Yonas Mersha card --- */}
        <div style={{
          display: 'flex', alignItems: 'flex-start', gap: 16,
          padding: '16px 18px', marginBottom: 12,
          background: '#ffffff',
          border: '1.5px solid #1D9E75',
          borderLeft: '5px solid #1D9E75',
          borderRadius: 10,
          boxShadow: '0 2px 8px rgba(29,158,117,0.10)',
        }}>
          {/* Avatar */}
          <div style={{
            width: 52, height: 52, borderRadius: '50%', flexShrink: 0,
            background: '#1D9E75',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 16, fontWeight: 700, color: '#ffffff',
            letterSpacing: '0.04em',
          }}>
            YM
          </div>
          {/* Info */}
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 16, fontWeight: 700,
                          color: '#0F2E24', marginBottom: 3 }}>
              Yonas Mersha
            </div>
            <div style={{ fontSize: 13, color: '#1D9E75', fontWeight: 600,
                          marginBottom: 4 }}>
              Hydro-Climate Modelling and AI Expert
            </div>
            <div style={{ fontSize: 12, color: '#4a5568', marginBottom: 10 }}>
              International Livestock Research Institute (ILRI)
            </div>
            <a href="mailto:Y.Mersha@cgiar.org"
               style={{
                 display: 'inline-flex', alignItems: 'center', gap: 6,
                 fontSize: 13, color: '#378ADD', fontWeight: 500,
                 textDecoration: 'none',
                 padding: '4px 10px', borderRadius: 6,
                 background: '#E6F1FB',
                 border: '1px solid #378ADD44',
               }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" strokeWidth="2" strokeLinecap="round"
                   strokeLinejoin="round">
                <rect x="2" y="4" width="20" height="16" rx="2"/>
                <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
              </svg>
              Y.Mersha@cgiar.org
            </a>
          </div>
        </div>

        {/* --- Dr. Teferi Demissie card --- */}
        <div style={{
          display: 'flex', alignItems: 'flex-start', gap: 16,
          padding: '16px 18px', marginBottom: 20,
          background: '#ffffff',
          border: '1.5px solid #378ADD',
          borderLeft: '5px solid #378ADD',
          borderRadius: 10,
          boxShadow: '0 2px 8px rgba(55,138,221,0.10)',
        }}>
          {/* Avatar */}
          <div style={{
            width: 52, height: 52, borderRadius: '50%', flexShrink: 0,
            background: '#378ADD',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 16, fontWeight: 700, color: '#ffffff',
            letterSpacing: '0.04em',
          }}>
            TD
          </div>
          {/* Info */}
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 16, fontWeight: 700,
                          color: '#0C1A2E', marginBottom: 3 }}>
              Dr. Teferi Demissie
            </div>
            <div style={{ fontSize: 13, color: '#185FA5', fontWeight: 600,
                          marginBottom: 4 }}>
              Senior Climate Scientist
            </div>
            <div style={{ fontSize: 12, color: '#4a5568', marginBottom: 10 }}>
              International Livestock Research Institute (ILRI)
            </div>
            <a href="mailto:t.demissie@cgiar.org"
               style={{
                 display: 'inline-flex', alignItems: 'center', gap: 6,
                 fontSize: 13, color: '#185FA5', fontWeight: 500,
                 textDecoration: 'none',
                 padding: '4px 10px', borderRadius: 6,
                 background: '#E6F1FB',
                 border: '1px solid #378ADD44',
               }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" strokeWidth="2" strokeLinecap="round"
                   strokeLinejoin="round">
                <rect x="2" y="4" width="20" height="16" rx="2"/>
                <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
              </svg>
              t.demissie@cgiar.org
            </a>
          </div>
        </div>

        {/* Info rows */}
        <InfoRow label="Data region"    value="Greater Horn of Africa (11 countries)" />
        <InfoRow label="Data provider"  value="NASA Goddard Space Flight Center -- EONET"
          link="https://eonet.gsfc.nasa.gov" />
        <InfoRow label="Satellite data" value="NASA MODIS, VIIRS, Ocean Color instruments" />
        <InfoRow label="Hazard sources" value="USGS, GDACS, Smithsonian GVP, JTWC, FEWS NET, ReliefWeb" />
        <InfoRow label="Open source"    value="MIT License -- source code on GitHub" />
      </div>

      {/* Email alert subscriptions */}
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
            NHMT-EA, national meteorological agencies, and official disaster
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
          NHMT-EA v3.0 -- Yonas Mersha -- Y.Mersha@cgiar.org -- ILRI
        </span>
        <a href="https://eonet.gsfc.nasa.gov" target="_blank" rel="noreferrer"
           style={{ fontSize: 11, color: '#378ADD' }}>NASA EONET</a>

      </div>
    </div>
  )
}

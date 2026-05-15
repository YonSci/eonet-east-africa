import React, { useMemo } from 'react'
import useAppStore, { CATEGORIES, ALL_CATS, MAG_CATS, COUNTRY_MAP } from '../store/useAppStore.js'
import { useSummary, useEvents } from '../api/queries.js'
import SavedFilters from './SavedFilters.jsx'

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
    magFilters,       setMagFilter,  clearMagFilters,
  } = useAppStore()

  const { data: summary }    = useSummary()
  const { data: rawEvents = [] } = useEvents()
  const byCat = summary && summary.by_category ? summary.by_category : {}

  const allOn  = activeCategories.length === ALL_CATS.length
  const noneOn = activeCategories.length === 0

  // Per-category magnitude sliders
  const hasMagCat     = activeCategories.some((c) => MAG_CATS.includes(c))
  const activeMagCats = activeCategories.filter((c) => MAG_CATS.includes(c))

  // Max magnitude per category derived from fetched events (excludes wildfire FRP)
  const catMaxMag = useMemo(() => {
    const result = {}
    ;(rawEvents || []).filter((ev) => ev.magnitude != null && MAG_CATS.includes(ev.category))
      .forEach((ev) => {
        const v = ev.magnitude.value || 0
        if (!result[ev.category] || v > result[ev.category]) result[ev.category] = v
      })
    return result
  }, [rawEvents])

  const countryName = selectedCountry ? (COUNTRY_MAP[selectedCountry] || selectedCountry) : null

  return (
    <div className="no-print" style={{
      display:'flex', flexDirection:'column',
      flex:1, minHeight:0, overflow:'hidden',
    }}>
      <div style={{ overflowY:'auto', flex:1, minHeight:0, padding:'14px 12px' }}>

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

        {/* -- Per-category magnitude filters -- */}
        {hasMagCat && activeMagCats.map((cat) => {
          const META = {
            earthquakes:         { label:'Richter',       unit:'M',   max:9,   step:0.5, dec:1,
              desc:'M3.0 minor, M4.5+ widely felt, M6.0+ damaging' },
            severeStorms:        { label:'Wind speed',     unit:'kts', max:200, step:5,   dec:0,
              desc:'Storm: 34-64 kts. Cat 1: 64 kts. Cat 5: 137+ kts' },
            floods:              { label:'Water depth',    unit:'m',   max:10,  step:0.5, dec:1,
              desc:'Reported water depth above normal level (metres)' },
            temperatureExtremes: { label:'Temperature',   unit:'C',   max:50,  step:1,   dec:0,
              desc:'Recorded temperature in degrees Celsius' },
          }
          const meta    = META[cat] || { label:cat, unit:'', max:100, step:1, dec:1, desc:'' }
          const dataMax = catMaxMag[cat] ? Math.ceil(catMaxMag[cat]) : 0
          const sliderMax = Math.max(dataMax, meta.max)
          const val     = magFilters[cat] || 0
          const catColor = (CATEGORIES[cat] || {}).color || '#7F77DD'
          return (
            <div key={cat} style={{ marginBottom:16 }}>
              <div style={{ display:'flex', alignItems:'center', gap:6, marginBottom:5 }}>
                <span style={{ width:8, height:8, borderRadius:'50%',
                               background:catColor, flexShrink:0 }} />
                <span style={{ fontSize:11, fontWeight:600,
                               color:'var(--text-secondary)', flex:1 }}>
                  {(CATEGORIES[cat] || {}).label || cat}
                </span>
                <span style={{ fontSize:10, color:'var(--text-muted)' }}>
                  {meta.label}
                </span>
              </div>
              <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:4 }}>
                <input
                  type="range"
                  min="0"
                  max={sliderMax}
                  step={meta.step}
                  value={val}
                  onChange={(e) => setMagFilter(cat, parseFloat(e.target.value))}
                  style={{ flex:1, accentColor:catColor }}
                />
                <span style={{ fontSize:12, fontWeight:600, minWidth:44,
                               textAlign:'right', color:catColor,
                               fontFamily:'var(--font-mono, monospace)' }}>
                  {val > 0
                    ? (cat === 'earthquakes' ? 'M' : '') + val.toFixed(meta.dec) + (cat === 'earthquakes' ? '' : ' ' + meta.unit)
                    : 'off'}
                </span>
              </div>
              <div style={{ fontSize:10, color:'var(--text-muted)', lineHeight:1.5 }}>
                {val > 0
                  ? 'Hiding ' + (CATEGORIES[cat]||{}).label + ' below ' + val.toFixed(meta.dec) + ' ' + meta.unit + '. Events without magnitude always shown.'
                  : meta.desc}
              </div>
            </div>
          )
        })}
        {hasMagCat && Object.values(magFilters).some((v) => v > 0) && (
          <button
            onClick={clearMagFilters}
            style={{ fontSize:11, padding:'3px 10px', borderRadius:4, marginBottom:14,
                     border:'1px solid var(--border-primary)', background:'transparent',
                     color:'var(--text-secondary)', cursor:'pointer' }}>
            Clear all magnitude filters
          </button>
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

        <SavedFilters />

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
    </div>
  )
}

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
    </aside>
  )
}

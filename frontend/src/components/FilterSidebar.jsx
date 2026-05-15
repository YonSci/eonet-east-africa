import React from 'react'
import useAppStore, { CATEGORIES, ALL_CATS } from '../store/useAppStore.js'
import { useSummary } from '../api/queries.js'

const STATUS_OPTS = [
  { value: 'all',    label: 'All events' },
  { value: 'open',   label: 'Open only' },
  { value: 'closed', label: 'Closed only' },
]

const DAY_OPTS = [7, 14, 30, 60, 90, 180, 365]

export default function FilterSidebar() {
  const {
    activeCategories, toggleCategory, setAllCategories,
    activeStatus, setStatus,
    lookbackDays, setDays,
  } = useAppStore()

  const { data: summary } = useSummary()
  const byCat = summary?.by_category || {}

  const allOn  = activeCategories.length === ALL_CATS.length
  const noneOn = activeCategories.length === 0

  return (
    <aside style={{
      width: 'var(--sidebar-w)',
      background: 'var(--bg-surface)',
      borderRight: '1px solid var(--border-primary)',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
      flexShrink: 0,
    }}>
      <div style={{ overflowY: 'auto', flex: 1, padding: '14px 12px' }}>

        {/* -- Status -- */}
        <Section label="Status">
          {STATUS_OPTS.map((o) => (
            <Pill
              key={o.value}
              active={activeStatus === o.value}
              onClick={() => setStatus(o.value)}
            >
              {o.label}
            </Pill>
          ))}
        </Section>

        {/* -- Lookback -- */}
        <Section label="Lookback window">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {DAY_OPTS.map((d) => (
              <Pill
                key={d}
                active={lookbackDays === d}
                onClick={() => setDays(d)}
              >
                {d}d
              </Pill>
            ))}
          </div>
        </Section>

        {/* -- Categories -- */}
        <Section label="Event categories">
          <div style={{ display: 'flex', gap: 6, marginBottom: 10 }}>
            <button
              style={smallBtn(allOn)}
              onClick={() => setAllCategories(ALL_CATS)}
            >All</button>
            <button
              style={smallBtn(noneOn)}
              onClick={() => setAllCategories([])}
            >None</button>
          </div>

          {ALL_CATS.map((cat) => {
            const meta    = CATEGORIES[cat]
            const active  = activeCategories.includes(cat)
            const count   = byCat[cat] || 0

            return (
              <button
                key={cat}
                onClick={() => toggleCategory(cat)}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '6px 8px',
                  marginBottom: 3,
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid',
                  borderColor: active ? meta.color + '55' : 'var(--border-muted)',
                  background: active ? meta.color + '1A' : 'transparent',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.15s',
                }}
              >
                {/* Dot */}
                <span style={{
                  width: 10, height: 10, borderRadius: '50%', flexShrink: 0,
                  background: active ? meta.color : 'var(--text-faint)',
                  transition: 'background 0.15s',
                }} />
                {/* Label */}
                <span style={{
                  flex: 1, fontSize: 13,
                  color: active ? 'var(--text-primary)' : 'var(--text-secondary)',
                  fontWeight: active ? 500 : 400,
                }}>
                  {meta.label}
                </span>
                {/* Count badge */}
                {count > 0 && (
                  <span style={{
                    fontSize: 11, padding: '1px 5px', borderRadius: 100,
                    background: active ? meta.color + '33' : 'var(--bg-elevated)',
                    color: active ? meta.color : 'var(--text-muted)',
                  }}>
                    {count}
                  </span>
                )}
              </button>
            )
          })}
        </Section>

        {/* -- About -- */}
        <Section label="Data source">
          <p style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.6 }}>
            NASA EONET v3 API filtered to the Greater Horn of Africa
            (21.8-51.4 E, 11.7 S - 22.0 N). Auto-refreshed every 15 min.
          </p>
          <a
            href="https://eonet.gsfc.nasa.gov/docs/v3"
            target="_blank"
            rel="noreferrer"
            style={{ fontSize: 11, color: 'var(--accent-blue)', display: 'block', marginTop: 6 }}
          >
            EONET API docs
          </a>
        </Section>
      </div>
    </aside>
  )
}

// ---- Small components ----

function Section({ label, children }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <p style={{
        fontSize: 10, fontWeight: 600, letterSpacing: '0.08em',
        textTransform: 'uppercase', color: 'var(--text-muted)',
        marginBottom: 8,
      }}>
        {label}
      </p>
      {children}
    </div>
  )
}

function Pill({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '4px 10px', borderRadius: 100, fontSize: 12,
        border: '1px solid',
        borderColor: active ? 'var(--accent-blue)' : 'var(--border-primary)',
        background: active ? 'var(--accent-blue)' : 'transparent',
        color: active ? '#fff' : 'var(--text-secondary)',
        cursor: 'pointer', marginBottom: 4,
      }}
    >
      {children}
    </button>
  )
}

function smallBtn(active) {
  return {
    fontSize: 12, padding: '3px 10px', borderRadius: 6,
    border: '1px solid var(--border-primary)',
    background: active ? 'var(--bg-elevated)' : 'transparent',
    color: active ? 'var(--text-primary)' : 'var(--text-secondary)',
    cursor: 'pointer',
  }
}

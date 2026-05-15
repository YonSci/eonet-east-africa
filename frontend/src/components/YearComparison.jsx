import React, { useState, useMemo } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend,
  ResponsiveContainer, LineChart, Line, CartesianGrid,
  Cell,
} from 'recharts'
import { useYearData } from '../api/queries.js'
import { CATEGORIES } from '../store/useAppStore.js'

// -- constants ---------------------------------------------------------------

const THIS_YEAR  = new Date().getFullYear()
const YEAR_OPTS  = Array.from({ length: 8 }, (_, i) => THIS_YEAR - i)

const COLOR_A = '#1D9E75'
const COLOR_B = '#378ADD'

const TT_STYLE = {
  background: 'var(--bg-elevated)',
  border: '1px solid var(--border-primary)',
  borderRadius: 6, fontSize: 12,
  color: 'var(--text-primary)',
}

const MONTH_LABELS = ['Jan','Feb','Mar','Apr','May','Jun',
                      'Jul','Aug','Sep','Oct','Nov','Dec']

// -- helpers -----------------------------------------------------------------

function getCatColor(cat) { return (CATEGORIES[cat] || {}).color || '#888780' }
function getCatLabel(cat) { return (CATEGORIES[cat] || {}).label || cat }

function monthKey(year, m) {
  return year + '-' + String(m).padStart(2, '0')
}

function buildMonthlyBins(events, year) {
  const bins = {}
  for (let m = 1; m <= 12; m++) {
    bins[monthKey(year, m)] = 0
  }
  events.forEach((ev) => {
    const k = (ev.latest_date || '').slice(0, 7)
    if (k in bins) bins[k] += 1
  })
  return bins
}

function buildCatCounts(events) {
  const counts = {}
  events.forEach((ev) => {
    counts[ev.category] = (counts[ev.category] || 0) + 1
  })
  return counts
}

function pct(a, b) {
  if (!b) return a > 0 ? '+100%' : '--'
  const diff = ((a - b) / b) * 100
  return (diff >= 0 ? '+' : '') + Math.round(diff) + '%'
}

function pctNum(a, b) {
  if (!b) return a > 0 ? 999 : 0
  return ((a - b) / b) * 100
}

// -- sub-components ----------------------------------------------------------

function SectionTitle({ children }) {
  return (
    <p style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.08em',
                textTransform: 'uppercase', color: 'var(--text-muted)',
                marginBottom: 12 }}>
      {children}
    </p>
  )
}

function StatCard({ label, value, sub, color, highlight }) {
  return (
    <div style={{
      background: 'var(--bg-elevated)',
      border: '1px solid var(--border-primary)',
      borderTop: '2px solid ' + (color || 'var(--border-primary)'),
      borderRadius: 'var(--radius-md)',
      padding: '10px 14px',
      outline: highlight ? '2px solid ' + color + '44' : 'none',
    }}>
      <div style={{ fontSize: 22, fontWeight: 600,
                    color: color || 'var(--text-primary)', lineHeight: 1,
                    marginBottom: 3 }}>
        {value}
      </div>
      <div style={{ fontSize: 12, fontWeight: 500,
                    color: 'var(--text-primary)', marginBottom: 2 }}>
        {label}
      </div>
      {sub && (
        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{sub}</div>
      )}
    </div>
  )
}

function YearSelector({ value, onChange, label, color }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <span style={{ width: 10, height: 10, borderRadius: '50%', flexShrink: 0,
                     background: color }} />
      <span style={{ fontSize: 12, color: 'var(--text-secondary)',
                     fontWeight: 500, minWidth: 46 }}>
        {label}
      </span>
      <select
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value, 10))}
        style={{
          fontSize: 13, fontWeight: 600, color: color,
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border-primary)',
          borderRadius: 5, padding: '4px 8px', cursor: 'pointer',
        }}
      >
        {YEAR_OPTS.map((y) => (
          <option key={y} value={y}>{y}</option>
        ))}
      </select>
    </div>
  )
}

function LoadingRow() {
  return (
    <div style={{ padding: '28px 0', textAlign: 'center',
                  fontSize: 12, color: 'var(--text-muted)' }}>
      Fetching EONET data for selected years...
    </div>
  )
}

// -- category comparison bar chart ------------------------------------------

function CategoryComparisonChart({ catsA, catsB, yearA, yearB, onCatClick }) {
  const allCats = useMemo(() => {
    const cats = new Set([...Object.keys(catsA), ...Object.keys(catsB)])
    return [...cats].sort((a, b) => {
      const totalA = (catsA[a] || 0) + (catsB[a] || 0)
      const totalB = (catsA[b] || 0) + (catsB[b] || 0)
      return totalB - totalA
    })
  }, [catsA, catsB])

  const data = allCats.map((cat) => ({
    label: getCatLabel(cat),
    cat,
    yearA: catsA[cat] || 0,
    yearB: catsB[cat] || 0,
  }))

  return (
    <ResponsiveContainer width="100%" height={Math.max(180, data.length * 32)}>
      <BarChart data={data} layout="vertical"
        margin={{ top: 0, right: 16, bottom: 0, left: 110 }}>
        <XAxis type="number" allowDecimals={false}
          tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
          axisLine={{ stroke: 'var(--border-primary)' }} tickLine={false} />
        <YAxis type="category" dataKey="label" width={105}
          tick={{ fontSize: 12, fill: 'var(--text-secondary)' }}
          axisLine={false} tickLine={false} />
        <Tooltip contentStyle={TT_STYLE}
          labelStyle={{ color: 'var(--text-primary)', fontWeight: 500 }}
          formatter={(value, name) => [value, name]} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="yearA" name={String(yearA)} fill={COLOR_A}
          radius={[0,3,3,0]} maxBarSize={12} />
        <Bar dataKey="yearB" name={String(yearB)} fill={COLOR_B}
          radius={[0,3,3,0]} maxBarSize={12} />
      </BarChart>
    </ResponsiveContainer>
  )
}

// -- monthly timeline dual-line chart ---------------------------------------

function MonthlyTimelineChart({ binsA, binsB, yearA, yearB }) {
  const data = MONTH_LABELS.map((mon, i) => {
    const m    = String(i + 1).padStart(2, '0')
    const keyA = yearA + '-' + m
    const keyB = yearB + '-' + m
    const vA   = binsA[keyA]
    const vB   = binsB[keyB]
    return {
      month: mon,
      [yearA]: vA != null ? vA : null,
      [yearB]: vB != null ? vB : null,
    }
  })

  return (
    <ResponsiveContainer width="100%" height={180}>
      <LineChart data={data} margin={{ top: 4, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="var(--border-primary)" strokeDasharray="3 3"
          vertical={false} />
        <XAxis dataKey="month"
          tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
          axisLine={{ stroke: 'var(--border-primary)' }} tickLine={false} />
        <YAxis allowDecimals={false}
          tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
          axisLine={false} tickLine={false} width={24} />
        <Tooltip contentStyle={TT_STYLE}
          formatter={(value, name) => [value, name]} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Line type="monotone" dataKey={yearA} stroke={COLOR_A}
          strokeWidth={2.5} dot={false} connectNulls />
        <Line type="monotone" dataKey={yearB} stroke={COLOR_B}
          strokeWidth={2} dot={false} strokeDasharray="5 3" connectNulls />
      </LineChart>
    </ResponsiveContainer>
  )
}

// -- biggest changes table --------------------------------------------------

function ChangesTable({ catsA, catsB, yearA, yearB }) {
  const rows = useMemo(() => {
    const allCats = new Set([...Object.keys(catsA), ...Object.keys(catsB)])
    return [...allCats]
      .map((cat) => {
        const a    = catsA[cat] || 0
        const b    = catsB[cat] || 0
        const diff = a - b
        return { cat, label: getCatLabel(cat), a, b, diff, pctVal: pctNum(a, b) }
      })
      .sort((x, y) => Math.abs(y.diff) - Math.abs(x.diff))
      .slice(0, 6)
  }, [catsA, catsB])

  if (!rows.length) return null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {rows.map((row) => {
        const isUp   = row.diff >= 0
        const color  = getCatColor(row.cat)
        const pctStr = pct(row.a, row.b)
        return (
          <div key={row.cat} style={{
            display: 'flex', alignItems: 'center', gap: 10,
            padding: '7px 10px',
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border-primary)',
            borderLeft: '3px solid ' + color,
            borderRadius: 'var(--radius-md)',
          }}>
            <span style={{ flex: 1, fontSize: 12, fontWeight: 500,
                           color: 'var(--text-primary)' }}>
              {row.label}
            </span>
            <span style={{ fontSize: 11, color: 'var(--text-muted)',
                           minWidth: 80, textAlign: 'right' }}>
              {yearB}: {row.b} - {yearA}: {row.a}
            </span>
            <span style={{
              fontSize: 11, fontWeight: 700, minWidth: 48, textAlign: 'right',
              color: row.diff === 0 ? 'var(--text-muted)'
                   : isUp         ? '#1D9E75'
                                  : '#E24B4A',
            }}>
              {row.diff === 0 ? 'no change' : pctStr}
            </span>
          </div>
        )
      })}
    </div>
  )
}

// -- main export ------------------------------------------------------------

export default function YearComparison() {
  const [yearA, setYearA] = useState(THIS_YEAR)
  const [yearB, setYearB] = useState(THIS_YEAR - 1)

  const { data: eventsA = [], isLoading: loadA } = useYearData(yearA)
  const { data: eventsB = [], isLoading: loadB } = useYearData(yearB)

  const isLoading = loadA || loadB

  const catsA  = useMemo(() => buildCatCounts(eventsA), [eventsA])
  const catsB  = useMemo(() => buildCatCounts(eventsB), [eventsB])
  const binsA  = useMemo(() => buildMonthlyBins(eventsA, yearA), [eventsA, yearA])
  const binsB  = useMemo(() => buildMonthlyBins(eventsB, yearB), [eventsB, yearB])

  const totalA = eventsA.length
  const totalB = eventsB.length
  const diff   = totalA - totalB
  const pctStr = pct(totalA, totalB)

  const topMover = useMemo(() => {
    const allCats = new Set([...Object.keys(catsA), ...Object.keys(catsB)])
    let best = null; let bestAbs = 0
    allCats.forEach((cat) => {
      const d = Math.abs((catsA[cat] || 0) - (catsB[cat] || 0))
      if (d > bestAbs) { bestAbs = d; best = cat }
    })
    return best
  }, [catsA, catsB])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

      {/* -- Year selectors -- */}
      <div style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-primary)',
        borderRadius: 'var(--radius-lg)', padding: '14px 16px',
      }}>
        <SectionTitle>Select years to compare</SectionTitle>
        <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap', alignItems: 'center' }}>
          <YearSelector value={yearA} onChange={setYearA}
            label="Year A" color={COLOR_A} />
          <span style={{ fontSize: 14, color: 'var(--text-muted)', fontWeight: 500 }}>
            vs
          </span>
          <YearSelector value={yearB} onChange={setYearB}
            label="Year B" color={COLOR_B} />
          {yearA === yearB && (
            <span style={{ fontSize: 11, color: '#BA7517', padding: '3px 8px',
                           background: '#FAEEDA', borderRadius: 4 }}>
              Select two different years to compare
            </span>
          )}
          <div style={{ marginLeft: 'auto', fontSize: 11, color: 'var(--text-muted)' }}>
            Fetches full-year event data from NASA EONET
          </div>
        </div>
      </div>

      {isLoading ? <LoadingRow /> : (
        <>
          {/* -- Summary stat cards -- */}
          <div style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-primary)',
            borderRadius: 'var(--radius-lg)', padding: '14px 16px',
          }}>
            <SectionTitle>Summary comparison</SectionTitle>
            <div style={{ display: 'grid',
                          gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
              <StatCard
                label={String(yearA) + ' total'}
                value={totalA}
                sub={'Greater Horn of Africa'}
                color={COLOR_A}
              />
              <StatCard
                label={String(yearB) + ' total'}
                value={totalB}
                sub={'Greater Horn of Africa'}
                color={COLOR_B}
              />
              <StatCard
                label={'Year-on-year change'}
                value={diff >= 0 ? '+' + diff : String(diff)}
                sub={pctStr + ' vs ' + yearB}
                color={diff === 0 ? 'var(--text-muted)'
                     : diff > 0  ? '#E24B4A'
                                 : '#1D9E75'}
              />
              <StatCard
                label={'Biggest mover'}
                value={topMover ? getCatLabel(topMover) : '--'}
                sub={topMover ? (
                  (catsA[topMover] || 0) + ' in ' + yearA +
                  ' vs ' + (catsB[topMover] || 0) + ' in ' + yearB
                ) : ''}
                color={topMover ? getCatColor(topMover) : 'var(--text-muted)'}
              />
            </div>
          </div>

          {/* -- Category comparison -- */}
          <div style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-primary)',
            borderRadius: 'var(--radius-lg)', padding: '14px 16px',
          }}>
            <SectionTitle>
              {'Events by category -- ' + yearA + ' vs ' + yearB}
            </SectionTitle>
            {(totalA + totalB === 0) ? (
              <p style={{ fontSize: 12, color: 'var(--text-muted)', textAlign: 'center',
                          padding: '20px 0' }}>
                No events found for the selected years in the Greater Horn of Africa region.
              </p>
            ) : (
              <CategoryComparisonChart
                catsA={catsA} catsB={catsB}
                yearA={yearA} yearB={yearB}
              />
            )}
          </div>

          {/* -- Monthly timeline -- */}
          <div style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-primary)',
            borderRadius: 'var(--radius-lg)', padding: '14px 16px',
          }}>
            <SectionTitle>
              {'Monthly trend -- ' + yearA + ' (solid) vs ' + yearB + ' (dashed)'}
            </SectionTitle>
            <MonthlyTimelineChart
              binsA={binsA} binsB={binsB}
              yearA={yearA} yearB={yearB}
            />
          </div>

          {/* -- Changes table + breakdown -- */}
          <div style={{
            display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14,
          }}>
            <div style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-primary)',
              borderRadius: 'var(--radius-lg)', padding: '14px 16px',
            }}>
              <SectionTitle>Biggest category changes</SectionTitle>
              <ChangesTable
                catsA={catsA} catsB={catsB}
                yearA={yearA} yearB={yearB}
              />
            </div>

            <div style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-primary)',
              borderRadius: 'var(--radius-lg)', padding: '14px 16px',
            }}>
              <SectionTitle>Year at a glance</SectionTitle>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {[
                  { year: yearA, events: eventsA, color: COLOR_A },
                  { year: yearB, events: eventsB, color: COLOR_B },
                ].map(({ year, events, color }) => {
                  const open   = events.filter((e) => e.status === 'open').length
                  const closed = events.length - open
                  const cats   = buildCatCounts(events)
                  const top    = Object.entries(cats).sort(([,a],[,b]) => b - a)[0]
                  return (
                    <div key={year} style={{
                      padding: '10px 12px',
                      background: 'var(--bg-elevated)',
                      border: '1px solid ' + color + '44',
                      borderLeft: '3px solid ' + color,
                      borderRadius: 'var(--radius-md)',
                    }}>
                      <div style={{ fontSize: 13, fontWeight: 700,
                                    color: color, marginBottom: 6 }}>
                        {year}
                      </div>
                      <div style={{ display: 'grid',
                                    gridTemplateColumns: '1fr 1fr',
                                    gap: '4px 16px', fontSize: 12 }}>
                        <span style={{ color: 'var(--text-muted)' }}>Total</span>
                        <span style={{ color: 'var(--text-primary)',
                                       fontWeight: 600 }}>
                          {events.length}
                        </span>
                        <span style={{ color: 'var(--text-muted)' }}>Open</span>
                        <span style={{ color: '#1D9E75', fontWeight: 500 }}>
                          {open}
                        </span>
                        <span style={{ color: 'var(--text-muted)' }}>Closed</span>
                        <span style={{ color: 'var(--text-secondary)' }}>{closed}</span>
                        <span style={{ color: 'var(--text-muted)' }}>Top category</span>
                        <span style={{ color: 'var(--text-primary)',
                                       fontWeight: 500, fontSize: 11 }}>
                          {top ? getCatLabel(top[0]) + ' (' + top[1] + ')' : '--'}
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          {/* -- Note about current year -- */}
          {(yearA === THIS_YEAR || yearB === THIS_YEAR) && (
            <p style={{ fontSize: 11, color: 'var(--text-muted)', textAlign: 'center',
                        padding: '0 0 4px' }}>
              {THIS_YEAR + ' data covers 1 Jan to today. Full-year comparison available from ' + (THIS_YEAR + 1) + '.'}
            </p>
          )}
        </>
      )}
    </div>
  )
}

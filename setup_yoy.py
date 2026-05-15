"""
setup_yoy.py
------------
Adds year-over-year event comparison to the NET-EA Analytics tab.

New component: YearComparison.jsx
  - Year A / Year B selectors (default: current year vs previous year)
  - Summary stat cards: totals, % change, biggest mover
  - Category grouped bar chart (side-by-side bars per category)
  - Monthly timeline: dual-line chart showing both years
  - Biggest changes table: which categories grew/dropped most

Also patches:
  - src/api/queries.js       -- adds useYearData hook
  - src/components/AnalyticsPanel.jsx  -- adds YearComparison section

Run from eonet-east-africa project root:
    python setup_yoy.py

No new npm packages -- uses Recharts already installed.
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
# queries.js -- add useYearData (patch appended to existing file)
# =============================================================================
QUERIES_APPEND = """
// ---------------------------------------------------------------------------
// Year-over-year helpers
// ---------------------------------------------------------------------------

const EONET_BASE_YOY = 'https://eonet.gsfc.nasa.gov/api/v3'
const EA_BBOX_YOY    = '21.8,22.0,51.4,-11.7'

async function fetchYearDirect(year) {
  const curYear = new Date().getFullYear()
  const start   = year + '-01-01'
  const end     = (year === curYear)
    ? new Date().toISOString().slice(0, 10)
    : year + '-12-31'
  const params  = new URLSearchParams({
    bbox: EA_BBOX_YOY, status: 'all', limit: 500, start, end,
  })
  const res  = await fetch(EONET_BASE_YOY + '/events/geojson?' + params)
  if (!res.ok) throw new Error('EONET ' + res.status)
  const data = await res.json()
  return (data.features || []).map(convertFeature)
}

export function useYearData(year) {
  return useQuery({
    queryKey:  ['year-events', year],
    queryFn:   () => fetchYearDirect(year),
    staleTime: 60 * 60 * 1000,
    enabled:   year > 2015 && year <= new Date().getFullYear(),
    retry:     2,
  })
}
"""

# =============================================================================
# YearComparison.jsx -- full component
# =============================================================================
FILES["frontend/src/components/YearComparison.jsx"] = r"""import React, { useState, useMemo } from 'react'
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
"""

# =============================================================================
# Builder
# =============================================================================
QUERIES_HOOK_MARKER = "// ---------------------------------------------------------------------------\n// Year-over-year helpers"

def build(root: Path):
    fe = root / "frontend"
    hdr(f"Adding year-over-year comparison to NET-EA in: {root}")
    created = updated = 0

    # 1. Write YearComparison.jsx
    for rel, content in FILES.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        existed = target.exists()
        target.write_text(content, encoding="utf-8")
        (ow if existed else ok)(("update  " if existed else "create  ") + rel)
        if existed: updated += 1
        else: created += 1

    # 2. Patch queries.js -- append the useYearData hook if not already present
    qpath = fe / "src/api/queries.js"
    if qpath.exists():
        qtxt = qpath.read_text(encoding="utf-8")
        if "useYearData" not in qtxt:
            qpath.write_text(qtxt.rstrip() + "\n" + QUERIES_APPEND, encoding="utf-8")
            ow("patch   frontend/src/api/queries.js  (appended useYearData)")
            updated += 1
        else:
            ok("skip    frontend/src/api/queries.js  (useYearData already present)")
    else:
        print("  WARN  queries.js not found -- run setup_tier1.py first")

    # 3. Patch AnalyticsPanel.jsx -- add YearComparison import + usage
    ap = fe / "src/components/AnalyticsPanel.jsx"
    if ap.exists():
        txt = ap.read_text(encoding="utf-8")
        changed = False

        # Add import if missing
        if "YearComparison" not in txt:
            # Insert after the last existing import line
            lines = txt.split("\n")
            last_import = 0
            for i, line in enumerate(lines):
                if line.startswith("import "):
                    last_import = i
            lines.insert(last_import + 1,
                         "import YearComparison from './YearComparison.jsx'")
            txt     = "\n".join(lines)
            changed = True

        # Add <YearComparison /> before the closing of the grid div
        # We look for the Export card (last card) and add after it
        INJECT_BEFORE = "function Card({ title, children, style }) {"
        YOY_SECTION = """
      {/* Year-over-year comparison */}
      <Card title="Year-over-year event comparison" style={{ gridColumn: '1 / -1' }}>
        <YearComparison />
      </Card>

"""
        if "YearComparison" in txt and YOY_SECTION.strip() not in txt:
            txt = txt.replace(INJECT_BEFORE, YOY_SECTION + INJECT_BEFORE)
            changed = True

        if changed:
            ap.write_text(txt, encoding="utf-8")
            ow("patch   frontend/src/components/AnalyticsPanel.jsx")
            updated += 1
        else:
            ok("skip    AnalyticsPanel.jsx (already patched)")
    else:
        print("  WARN  AnalyticsPanel.jsx not found -- run setup_tier1.py first")

    # 4. ASCII check
    print()
    bad = []
    for f in list((fe / "src").rglob("*.jsx")) + list((fe / "src").rglob("*.js")):
        raw = f.read_bytes()
        for i, line in enumerate(raw.split(b"\n"), 1):
            if any(b > 127 for b in line):
                bad.append(f"  {f.name}:{i}")
    if bad:
        print("  WARN  Non-ASCII found (OXC will reject):")
        for b in bad: print(b)
    else:
        ok("ASCII-clean -- OXC safe")

    hdr("Done")
    print(f"  Files created : {created}")
    print(f"  Files updated : {updated}")
    print()
    print("  What was added:")
    print("    Analytics tab now has a 'Year-over-year event comparison' section")
    print("    Year A / Year B selectors (dropdowns, default: this year vs last year)")
    print("    4 summary stat cards: totals + change % + biggest mover")
    print("    Category grouped bar chart (side-by-side bars, one colour per year)")
    print("    Monthly timeline dual-line chart (solid = Year A, dashed = Year B)")
    print("    Biggest changes table (top 6 categories by absolute event count change)")
    print("    Year at a glance panel (open/closed/top category per year)")
    print()
    print("  Notes:")
    print("    Each year fetch is cached for 1 hour (historical data rarely changes)")
    print("    Current year fetches data from 1 Jan to today")
    print("    Requires live EONET access -- use mobile hotspot if office network blocks it")
    print()
    print("  No npm install needed -- restart Vite:")
    print("    cd frontend && npm run dev")
    print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Add YoY comparison to NET-EA Analytics tab")
    parser.add_argument("--path", default=".", help="Project root (default: current dir)")
    args = parser.parse_args()
    root = Path(args.path).resolve()
    if not (root / "backend").exists():
        print(f"WARNING: {root} may not be project root. Continue? [y/N] ", end="")
        if input().strip().lower() != "y":
            sys.exit(0)
    build(root)

import React, { useMemo } from 'react'
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

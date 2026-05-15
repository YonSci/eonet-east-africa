import React from 'react'
import { useSummary } from '../api/queries.js'
import { CATEGORIES } from '../store/useAppStore.js'

function getCatColor(cat) { return (CATEGORIES[cat] || {}).color || '#484f58' }

export default function StatCards() {
  const { data: s, isLoading } = useSummary()

  const total      = s?.total  ?? 0
  const open       = s?.open   ?? 0
  const closed     = s?.closed ?? 0
  const byCat      = s?.by_category || {}
  const openRate   = total > 0 ? Math.round((open / total) * 100) : 0

  const topCat     = Object.entries(byCat).sort(([,a],[,b]) => b - a)[0]
  const topCatId   = topCat ? topCat[0] : null
  const topCatN    = topCat ? topCat[1] : 0
  const topCatLabel= topCatId ? ((CATEGORIES[topCatId] || {}).label || topCatId) : '--'
  const topCatColor= topCatId ? getCatColor(topCatId) : 'var(--text-muted)'

  const cards = [
    {
      value:  isLoading ? '...' : total,
      label:  'Total events',
      sub:    'in ICPAC GHA region',
      color:  'var(--accent-blue)',
      icon:   'globe',
    },
    {
      value:  isLoading ? '...' : open,
      label:  'Open',
      sub:    openRate + '% of total',
      color:  '#1D9E75',
      icon:   'circle',
      bar:    openRate,
      barColor: '#1D9E75',
    },
    {
      value:  isLoading ? '...' : closed,
      label:  'Closed',
      sub:    (100 - openRate) + '% resolved',
      color:  'var(--text-muted)',
      icon:   'check',
    },
    {
      value:  isLoading ? '...' : (topCatId ? topCatN : '--'),
      label:  'Top category',
      sub:    topCatLabel,
      color:  topCatColor,
      icon:   'fire',
      accent: topCatColor,
    },
  ]

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)',
                  gap: 10, padding: '10px 14px 0', flexShrink: 0 }}>
      {cards.map((c, i) => (
        <div key={i} style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-primary)',
          borderTop: '2px solid ' + c.color,
          borderRadius: 'var(--radius-md)',
          padding: '10px 14px',
          position: 'relative',
          overflow: 'hidden',
        }}>
          {/* Background accent strip */}
          <div style={{
            position: 'absolute', top: 0, right: 0, bottom: 0, width: 3,
            background: c.color, opacity: 0.2,
          }} />

          <div style={{ fontSize: 24, fontWeight: 600, color: c.color,
                        lineHeight: 1, marginBottom: 4 }}>
            {c.value}
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-primary)', fontWeight: 500,
                        marginBottom: 2 }}>
            {c.label}
          </div>
          <div style={{ fontSize: 11, color: c.accent || 'var(--text-muted)' }}>
            {c.sub}
          </div>

          {/* Progress bar for open rate */}
          {c.bar != null && (
            <div style={{ marginTop: 8, height: 3,
                          background: 'var(--bg-elevated)', borderRadius: 2 }}>
              <div style={{
                height: '100%', borderRadius: 2,
                width: c.bar + '%', background: c.barColor,
                transition: 'width 0.5s',
              }} />
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

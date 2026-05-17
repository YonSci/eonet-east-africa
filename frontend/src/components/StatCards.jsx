import React from 'react'
import { useSummary } from '../api/queries.js'
import { isNetworkBlockedError } from '../api/queries.js'
import { CATEGORIES } from '../store/useAppStore.js'
import { SkeletonRect } from './SkeletonLoader.jsx'

function getCatColor(cat) { return (CATEGORIES[cat] || {}).color || '#484f58' }

export default function StatCards() {
  const { data: s, isLoading, isError, error } = useSummary()

  const total    = s?.total  ?? 0
  const open     = s?.open   ?? 0
  const closed   = s?.closed ?? 0
  const byCat    = s?.by_category || {}
  const openRate = total > 0 ? Math.round((open / total) * 100) : 0
  const topEntry = Object.entries(byCat).sort(([,a],[,b]) => b - a)[0]
  const topCatId = topEntry ? topEntry[0] : null
  const topCatN  = topEntry ? topEntry[1] : 0
  const topLabel = topCatId ? ((CATEGORIES[topCatId] || {}).label || topCatId) : '--'
  const topColor = topCatId ? getCatColor(topCatId) : 'var(--text-muted)'

  const cards = [
    { value: total,  label: 'Total events', sub: 'Greater Horn of Africa', color: '#378ADD' },
    { value: open,   label: 'Open',         sub: openRate + '% of total',  color: '#1D9E75', bar: openRate, barColor: '#1D9E75' },
    { value: closed, label: 'Closed',       sub: (100 - openRate) + '% resolved', color: 'var(--text-muted)' },
    { value: topCatN, label: 'Top category', sub: topLabel, color: topColor },
  ]

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)',
                  gap: 8, padding: '6px 14px 0', flexShrink: 0 }}>
      {isError ? (
        <div style={{ gridColumn:'1 / -1', padding:'8px 12px',
                      fontSize:11, color:'#BA7517', fontWeight:500,
                      background:'#FAEEDA', borderRadius:'var(--radius-md)',
                      border:'1px solid #BA751733' }}>
          {isNetworkBlockedError(error)
            ? 'Network blocked -- cannot reach NASA EONET. Try a mobile hotspot.'
            : 'Failed to load events. Check console for details.'}
        </div>
      ) : isLoading ? (
        Array.from({ length: 4 }).map((_, i) => (
          <div key={i} style={{ background: 'var(--bg-surface)',
                                border: '1px solid var(--border-primary)',
                                borderRadius: 'var(--radius-md)', padding: '6px 10px' }}>
            <SkeletonRect h={22} w="50%" style={{ marginBottom: 4 }} />
            <SkeletonRect h={11} w="65%" />
          </div>
        ))
      ) : (
        cards.map((c, i) => (
          <div key={i} style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-primary)',
            borderTop: '2px solid ' + c.color,
            borderRadius: 'var(--radius-md)', padding: '6px 10px',
          }}>
            <div style={{ fontSize: 20, fontWeight: 600, color: c.color, lineHeight: 1,
                          marginBottom: 2 }}>
              {c.value}
            </div>
            <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-primary)',
                          marginBottom: 1 }}>
              {c.label}
            </div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{c.sub}</div>
            {c.bar != null && (
              <div style={{ marginTop: 6, height: 2, background: 'var(--bg-elevated)',
                            borderRadius: 1 }}>
                <div style={{ height: '100%', borderRadius: 1, width: c.bar + '%',
                              background: c.barColor, transition: 'width 0.5s' }} />
              </div>
            )}
          </div>
        ))
      )}
    </div>
  )
}

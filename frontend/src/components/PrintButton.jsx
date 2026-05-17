import React from 'react'
import useAppStore from '../store/useAppStore.js'
import { useEvents } from '../api/queries.js'

export default function PrintButton() {
  const { activeStatus, lookbackDays, dateMode, startDate, endDate, activeCategories } = useAppStore()
  const { data: events = [] } = useEvents()

  function handlePrint() {
    const el = document.getElementById('print-header-inject')
    if (el) {
      const dateStr  = dateMode === 'range'
        ? startDate + ' to ' + endDate
        : 'Last ' + lookbackDays + ' days'
      const cats     = activeCategories.length === 10
        ? 'All categories'
        : activeCategories.join(', ')
      el.innerHTML =
        '<div class="print-title">NHMT-EA -- Natural Hazard Monitoring & Tracking for East Africa</div>' +
        '<div class="print-subtitle">Yonas M. | Y.Mersha@cgiar.org | Climate Modelling and AI Expert</div>' +
        '<div class="print-meta">' +
          'Generated: ' + new Date().toLocaleString() + '<br/>' +
          'Period: ' + dateStr + '<br/>' +
          'Status: ' + activeStatus + '<br/>' +
          'Events: ' + events.length + '<br/>' +
          'Categories: ' + cats +
        '</div>'
    }
    window.print()
  }

  return (
    <button
      onClick={handlePrint}
      title="Print / Export PDF"
      className="no-print"
      style={{
        display: 'flex', alignItems: 'center', gap: 5,
        fontSize: 12, padding: '4px 10px', borderRadius: 6,
        border: '1px solid var(--border-primary)',
        background: 'transparent', color: 'var(--text-secondary)',
        cursor: 'pointer',
      }}
    >
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
           stroke="currentColor" strokeWidth="2" strokeLinecap="round"
           strokeLinejoin="round">
        <polyline points="6 9 6 2 18 2 18 9"/>
        <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/>
        <rect x="6" y="14" width="12" height="8"/>
      </svg>
      Export PDF
    </button>
  )
}

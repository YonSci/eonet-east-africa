import React, { useState, useEffect, useRef } from 'react'
import TopNav         from './components/TopNav.jsx'
import FilterSidebar  from './components/FilterSidebar.jsx'
import StatCards      from './components/StatCards.jsx'
import MapPanel       from './components/MapPanel.jsx'
import EventList      from './components/EventList.jsx'
import AnalyticsPanel from './components/AnalyticsPanel.jsx'
import AboutPanel     from './components/AboutPanel.jsx'
import ToastContainer from './components/ToastContainer.jsx'
import PrintButton    from './components/PrintButton.jsx'
import useAppStore, { ALL_CATS, readURLFilters, writeURLFilters } from './store/useAppStore.js'
import { useEvents }  from './api/queries.js'

const TABS = [
  { id: 'map',       label: 'Map view'  },
  { id: 'analytics', label: 'Analytics' },
  { id: 'about',     label: 'About'     },
]

function EventWatcher() {
  const { data: events } = useEvents()
  const addToast = useAppStore((s) => s.addToast)
  const prevIdsRef = useRef(null)

  useEffect(() => {
    if (!events || events.length === 0) return
    const currentIds = new Set(events.map((e) => e.id))
    if (prevIdsRef.current !== null && prevIdsRef.current.size > 0) {
      const newEvs = events.filter((e) => !prevIdsRef.current.has(e.id))
      if (newEvs.length > 0) {
        const names = newEvs.slice(0, 2).map((e) => e.title).join('; ')
        addToast(
          newEvs.length + ' new event' + (newEvs.length > 1 ? 's' : '') + ': ' + names,
          'info'
        )
      }
    }
    prevIdsRef.current = currentIds
  }, [events, addToast])

  return null
}

export default function App() {
  const {
    sidebarOpen, activeCategories, activeStatus,
    lookbackDays, dateMode, startDate, endDate,
    setStatus, setDays, setAllCategories, setDateMode, setStartDate, setEndDate,
  } = useAppStore()

  const [activeTab, setActiveTab] = useState('map')

  // -- Read URL filters on mount --
  useEffect(() => {
    const f = readURLFilters()
    if (f.status)    setStatus(f.status)
    if (f.days)      setDays(f.days)
    if (f.cats && f.cats.length > 0) setAllCategories(f.cats)
    if (f.dateMode)  setDateMode(f.dateMode)
    if (f.startDate) setStartDate(f.startDate)
    if (f.endDate)   setEndDate(f.endDate)
  }, [])

  // -- Write URL whenever filters change --
  useEffect(() => {
    writeURLFilters({
      activeCategories, activeStatus, lookbackDays,
      dateMode, startDate, endDate,
    })
  }, [activeCategories, activeStatus, lookbackDays, dateMode, startDate, endDate])

  const showSidebar   = sidebarOpen && activeTab !== 'about'
  const showStatCards = activeTab !== 'about'

  return (
    <div style={{ display: 'flex', flexDirection: 'column',
                  height: '100vh', overflow: 'hidden' }}>
      <ToastContainer />
      <EventWatcher />

      {/* Print header -- hidden on screen, visible on print */}
      <div id="print-header-inject" className="print-only print-header" />

      <TopNav />

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {showSidebar && <FilterSidebar />}

        <main style={{ flex: 1, display: 'flex', flexDirection: 'column',
                       overflow: 'hidden', minWidth: 0 }}>

          {showStatCards && <StatCards />}

          {/* Tab bar */}
          <div className="tab-bar-row no-print" style={{
            display: 'flex', alignItems: 'center', gap: 2,
            padding: '8px 14px 0',
            borderBottom: '1px solid var(--border-primary)',
            background: 'var(--bg-base)', flexShrink: 0,
          }}>
            {TABS.map((tab) => {
              const active = activeTab === tab.id
              return (
                <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={{
                  padding: '6px 14px', fontSize: 13, fontWeight: active ? 600 : 400,
                  color:  active ? 'var(--text-primary)' : 'var(--text-secondary)',
                  background: 'transparent', border: 'none',
                  borderBottom: '2px solid',
                  borderBottomColor: active ? '#1D9E75' : 'transparent',
                  cursor: 'pointer', marginBottom: -1,
                }}>
                  {tab.label}
                </button>
              )
            })}
            <div style={{ flex: 1 }} />

            {/* Share URL button */}
            <button
              onClick={() => {
                navigator.clipboard.writeText(window.location.href)
                  .then(() => useAppStore.getState().addToast('Link copied to clipboard', 'info'))
                  .catch(() => {})
              }}
              className="no-print"
              title="Copy shareable link"
              style={{
                fontSize: 12, padding: '4px 10px', borderRadius: 6,
                border: '1px solid var(--border-primary)',
                background: 'transparent', color: 'var(--text-secondary)',
                cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 5,
              }}
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" strokeWidth="2" strokeLinecap="round"
                   strokeLinejoin="round">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
              </svg>
              Share
            </button>

            <PrintButton />
          </div>

          {activeTab === 'map' && (
            <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
              <MapPanel />
              <EventList />
            </div>
          )}

          {activeTab === 'analytics' && <AnalyticsPanel />}
          {activeTab === 'about'     && <AboutPanel />}
        </main>
      </div>
    </div>
  )
}

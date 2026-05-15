import React, { useState } from 'react'
import TopNav         from './components/TopNav.jsx'
import FilterSidebar  from './components/FilterSidebar.jsx'
import StatCards      from './components/StatCards.jsx'
import MapPanel       from './components/MapPanel.jsx'
import EventList      from './components/EventList.jsx'
import AnalyticsPanel from './components/AnalyticsPanel.jsx'
import AboutPanel     from './components/AboutPanel.jsx'
import useAppStore    from './store/useAppStore.js'

const TABS = [
  { id: 'map',       label: 'Map view'  },
  { id: 'analytics', label: 'Analytics' },
  { id: 'about',     label: 'About'     },
]

export default function App() {
  const { sidebarOpen } = useAppStore()
  const [activeTab, setActiveTab] = useState('map')

  // Sidebar and stat cards are only shown on map and analytics tabs
  const showSidebar  = sidebarOpen && activeTab !== 'about'
  const showStatCards = activeTab !== 'about'

  return (
    <div style={{ display: 'flex', flexDirection: 'column',
                  height: '100vh', overflow: 'hidden' }}>
      <TopNav />

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {showSidebar && <FilterSidebar />}

        <main style={{ flex: 1, display: 'flex', flexDirection: 'column',
                       overflow: 'hidden', minWidth: 0 }}>

          {showStatCards && <StatCards />}

          {/* Tab bar */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 2,
            padding: '8px 14px 0',
            borderBottom: '1px solid var(--border-primary)',
            background: 'var(--bg-base)',
            flexShrink: 0,
          }}>
            {TABS.map((tab) => {
              const active = activeTab === tab.id
              return (
                <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={{
                  padding: '6px 14px', fontSize: 13,
                  fontWeight: active ? 600 : 400,
                  color:  active ? 'var(--text-primary)' : 'var(--text-secondary)',
                  background: 'transparent', border: 'none',
                  borderBottom: '2px solid',
                  borderBottomColor: active ? '#1D9E75' : 'transparent',
                  cursor: 'pointer', transition: 'all 0.15s', marginBottom: -1,
                }}>
                  {tab.label}
                </button>
              )
            })}
            <div style={{ flex: 1 }} />
            {activeTab !== 'about' && (
              <span style={{ fontSize: 11, color: 'var(--text-muted)', paddingBottom: 6 }}>
                Greater Horn of Africa
              </span>
            )}
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

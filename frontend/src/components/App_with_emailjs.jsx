import React, { useState, useEffect, useRef } from 'react'
import TopNav         from './components/TopNav.jsx'
import FilterSidebar  from './components/FilterSidebar.jsx'
import StatCards      from './components/StatCards.jsx'
import MapPanel       from './components/MapPanel.jsx'
import EventList      from './components/EventList.jsx'
import CategoryBar    from './components/CategoryBar.jsx'
import AnalyticsPanel from './components/AnalyticsPanel.jsx'
import AboutPanel     from './components/AboutPanel.jsx'
import ToastContainer from './components/ToastContainer.jsx'
import PrintButton    from './components/PrintButton.jsx'
import OfflineBanner  from './components/OfflineBanner.jsx'
import useAppStore, {
  ALL_CATS, readURLFilters, writeURLFilters,
} from './store/useAppStore.js'
import { useEvents } from './api/queries.js'

const TABS = [
  { id: 'map',       label: 'Map view'  },
  { id: 'analytics', label: 'Analytics' },
  { id: 'about',     label: 'About'     },
]

function useIsMobile() {
  const [isMobile, setIsMobile] = useState(
    typeof window !== 'undefined' && window.innerWidth < 768
  )
  useEffect(() => {
    function handle() { setIsMobile(window.innerWidth < 768) }
    window.addEventListener('resize', handle)
    return () => window.removeEventListener('resize', handle)
  }, [])
  return isMobile
}


const SUBS_KEY = 'nhmt-ea-alert-subscriptions'

function matchesSub(ev, sub) {
  if (sub.categories && sub.categories.length > 0) {
    if (!sub.categories.includes(ev.category)) return false
  }
  if (sub.countries && sub.countries.length > 0) {
    const bbox = {
      DJ:{minLat:10,maxLat:13,minLon:41,maxLon:44},ER:{minLat:12,maxLat:18,minLon:36,maxLon:44},
      ET:{minLat:3,maxLat:15,minLon:33,maxLon:48},KE:{minLat:-5,maxLat:5,minLon:33,maxLon:42},
      RW:{minLat:-3,maxLat:0,minLon:28,maxLon:31},SO:{minLat:-2,maxLat:12,minLon:40,maxLon:52},
      SS:{minLat:3,maxLat:12,minLon:24,maxLon:36},SD:{minLat:9,maxLat:22,minLon:21,maxLon:38},
      TZ:{minLat:-12,maxLat:0,minLon:29,maxLon:41},UG:{minLat:-2,maxLat:4,minLon:29,maxLon:35},
      BI:{minLat:-5,maxLat:-2,minLon:28,maxLon:31},
    }
    const coords = ev.coords
    if (!coords) return false
    const lon = coords[0]; const lat = coords[1]
    const inCountry = sub.countries.some((iso) => {
      const b = bbox[iso]
      return b && lon >= b.minLon && lon <= b.maxLon && lat >= b.minLat && lat <= b.maxLat
    })
    if (!inCountry) return false
  }
  return true
}

function fireNotifications(newEvs) {
  if (!('Notification' in window) || Notification.permission !== 'granted') return
  try {
    const subs = JSON.parse(localStorage.getItem(SUBS_KEY) || '[]')
    if (!subs.length) return
    subs.forEach((sub) => {
      const matched = newEvs.filter((ev) => matchesSub(ev, sub))
      if (!matched.length) return
      const title = 'NHMT-EA: ' + matched.length + ' new event' + (matched.length > 1 ? 's' : '') + ' detected'
      const body  = matched.slice(0, 3).map((e) => e.title).join('\n') +
        (matched.length > 3 ? '\n...and ' + (matched.length - 3) + ' more' : '')
      new Notification(title, { body, icon: '/favicon.svg', tag: 'net-ea-alert' })
    })
  } catch {}
}

function EventWatcher() {
  const { data: events } = useEvents()
  const addToast         = useAppStore((s) => s.addToast)
  const prevIdsRef       = useRef(null)
  useEffect(() => {
    if (!events || events.length === 0) return
    const currentIds = new Set(events.map((e) => e.id))
    if (prevIdsRef.current !== null && prevIdsRef.current.size > 0) {
      const newEvs = events.filter((e) => !prevIdsRef.current.has(e.id))
      if (newEvs.length > 0) {
        const names = newEvs.slice(0, 2).map((e) => e.title).join('; ')
        addToast(newEvs.length + ' new event' +
          (newEvs.length > 1 ? 's' : '') + ': ' + names, 'info')
        // Email alerts via EmailJS for matching subscribers
        ;(async () => {
          try {
            const { sendAlertEmail } = await import('./api/emailService.js')
            const subs = JSON.parse(localStorage.getItem('nhmt-ea-alert-subscriptions') || '[]')
            for (const sub of subs) {
              const matched = newEvs.filter((ev) =>
                (!sub.categories || !sub.categories.length ||
                  sub.categories.includes(ev.category)))
              if (matched.length > 0) {
                await sendAlertEmail({
                  email: sub.email, newEvents: matched,
                  categories: sub.categories || [], countries: sub.countries || [],
                })
              }
            }
          } catch {}
        })()
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
    setStatus, setDays, setAllCategories,
    setDateMode, setStartDate, setEndDate, toggleSidebar,
  } = useAppStore()

  const [activeTab,      setActiveTab]      = useState('map')
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const isMobile = useIsMobile()

  // Read URL filters on mount
  useEffect(() => {
    const f = readURLFilters()
    if (f.status)    setStatus(f.status)
    if (f.days)      setDays(f.days)
    if (f.cats && f.cats.length > 0) setAllCategories(f.cats)
    if (f.dateMode)  setDateMode(f.dateMode)
    if (f.startDate) setStartDate(f.startDate)
    if (f.endDate)   setEndDate(f.endDate)
  }, [])

  // Write URL when filters change
  useEffect(() => {
    writeURLFilters({ activeCategories, activeStatus, lookbackDays,
                      dateMode, startDate, endDate })
  }, [activeCategories, activeStatus, lookbackDays, dateMode, startDate, endDate])

  // Close mobile menu when tab changes
  useEffect(() => { setMobileMenuOpen(false) }, [activeTab])

  // Click outside to close mobile sidebar
  useEffect(() => {
    if (!isMobile || !mobileMenuOpen) return
    function handle(e) {
      if (!e.target.closest('.filter-sidebar') &&
          !e.target.closest('.menu-btn')) setMobileMenuOpen(false)
    }
    document.addEventListener('mousedown', handle)
    return () => document.removeEventListener('mousedown', handle)
  }, [isMobile, mobileMenuOpen])

  const showSidebar   = activeTab !== 'about'
  const showStatCards = activeTab !== 'about'
  const sidebarClass  = 'filter-sidebar' +
    (isMobile && mobileMenuOpen ? ' mobile-open' : '')

  return (
    /*
     * Root: full viewport height, no overflow -- children manage their own scroll.
     * The key fix: every layer uses display:flex + flex:1 + minHeight:0.
     * minHeight:0 overrides the default min-height:auto that prevents flex children
     * from shrinking below their content size, which was causing the white-space gap.
     */
    <div style={{ display:'flex', flexDirection:'column',
                  height:'100vh', overflow:'hidden' }}>
      <ToastContainer />
      <EventWatcher />
      <div id="print-header-inject" className="print-only print-header" />

      <TopNav isMobile={isMobile} onMenuClick={() => setMobileMenuOpen((v) => !v)} />
      <OfflineBanner />

      {/* Mobile sidebar backdrop */}
      {isMobile && mobileMenuOpen && (
        <div onClick={() => setMobileMenuOpen(false)} style={{
          position:'fixed', inset:0, background:'rgba(0,0,0,0.4)', zIndex:2999,
        }} />
      )}

      {/* Body: sidebar + main -- fills all remaining height */}
      <div style={{ display:'flex', flex:1, minHeight:0, overflow:'hidden' }}>

        {/* Sidebar -- height constrained so inner scroll works */}
        {showSidebar && (
          <aside
            className={sidebarClass}
            style={{
              width: 'var(--sidebar-w)',
              display: 'flex',
              flexDirection: 'column',
              height: '100%',      /* explicit height so overflow:auto triggers */
              minHeight: 0,
              flexShrink: 0,
              background: 'var(--bg-surface)',
              borderRight: '1px solid var(--border-primary)',
              overflow: 'hidden',
            }}
          >
            {isMobile && (
              <div style={{ padding:'12px 14px',
                            borderBottom:'1px solid var(--border-primary)',
                            display:'flex', justifyContent:'space-between',
                            alignItems:'center', flexShrink:0 }}>
                <span style={{ fontSize:12, fontWeight:600,
                               color:'var(--text-secondary)' }}>Filters</span>
                <button onClick={() => setMobileMenuOpen(false)}
                  style={{ background:'none', border:'none', cursor:'pointer',
                           fontSize:18, color:'var(--text-muted)' }}>
                  x
                </button>
              </div>
            )}
            {/* FilterSidebar handles its own internal scroll */}
            <FilterSidebar />
          </aside>
        )}

        {/* Main content */}
        <main style={{ flex:1, display:'flex', flexDirection:'column',
                       minHeight:0, overflow:'hidden' }}>

          {showStatCards && <StatCards />}

          {/* Tab bar */}
          <div className="tab-bar-row no-print" style={{
            display:'flex', alignItems:'center', gap:2,
            padding:'8px 14px 0',
            borderBottom:'1px solid var(--border-primary)',
            background:'var(--bg-base)', flexShrink:0,
          }}>
            {TABS.map((tab) => {
              const active = activeTab === tab.id
              return (
                <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={{
                  padding:'6px 14px', fontSize:13,
                  fontWeight: active ? 600 : 400,
                  color: active ? 'var(--text-primary)' : 'var(--text-secondary)',
                  background:'transparent', border:'none',
                  borderBottom:'2px solid',
                  borderBottomColor: active ? '#1D9E75' : 'transparent',
                  cursor:'pointer', marginBottom:-1, whiteSpace:'nowrap',
                }}>
                  {tab.label}
                </button>
              )
            })}
            <div style={{ flex:1 }} />
            {!isMobile && (
              <>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(window.location.href)
                      .then(() => useAppStore.getState().addToast('Link copied', 'info'))
                      .catch(() => {})
                  }}
                  className="no-print"
                  title="Copy shareable link"
                  style={{ fontSize:12, padding:'4px 10px', borderRadius:6,
                           border:'1px solid var(--border-primary)',
                           background:'transparent', color:'var(--text-secondary)',
                           cursor:'pointer', display:'flex', alignItems:'center', gap:5 }}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                    <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
                  </svg>
                  Share
                </button>
                <PrintButton />
              </>
            )}
          </div>

          {/* Map tab */}
          {activeTab === 'map' && (
            /*
             * This column fills ALL remaining height after the tab bar.
             * Map grows to fill, CategoryBar is fixed-height at the bottom.
             */
            <div style={{
              flex: 1, minHeight: 0,
              display: 'flex',
              flexDirection: isMobile ? 'column' : 'row',
              overflow: 'hidden',
            }}>
              {/* Left: map + category bar stacked vertically */}
              <div style={{ flex:1, minWidth:0, minHeight:0,
                            display:'flex', flexDirection:'column', overflow:'hidden' }}>
                {/* Map fills all available space in this column */}
                <MapPanel />
                {/* Category bar uses the white space below the map */}
                <CategoryBar />
              </div>

              {/* Right: event list panel -- full height */}
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

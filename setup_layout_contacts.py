"""
setup_layout_contacts.py
------------------------
Fixes four things visible in the screenshot:

  1. Sidebar scroll   -- sidebar wrapper gets height:0 + flex:1 so
                         the inner overflowY:auto triggers correctly
  2. Events panel     -- right panel gets explicit height constraints
  3. White space      -- CategoryBar strip below the map fills the gap
  4. Contacts         -- email on Yonas, Dr. Teferi Demissie added

Run from the eonet-east-africa project root:
    python setup_layout_contacts.py
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
# CategoryBar.jsx  -- horizontal event-count strip below the map
# =============================================================================
FILES["frontend/src/components/CategoryBar.jsx"] = """import React from 'react'
import { CATEGORIES } from '../store/useAppStore.js'
import { useEvents } from '../api/queries.js'
import useAppStore from '../store/useAppStore.js'

export default function CategoryBar() {
  const { activeCategories, activeStatus, setAllCategories, toggleCategory } = useAppStore()
  const { data: rawEvents = [], isLoading } = useEvents()

  // Count events per category (respecting status filter)
  const counts = {}
  rawEvents.forEach((ev) => {
    if (activeStatus === 'open'   && ev.status !== 'open')   return
    if (activeStatus === 'closed' && ev.status !== 'closed') return
    counts[ev.category] = (counts[ev.category] || 0) + 1
  })

  const total   = Object.values(counts).reduce((a, b) => a + b, 0)
  const entries = Object.entries(CATEGORIES)
    .map(([id, meta]) => ({ id, ...meta, count: counts[id] || 0 }))
    .filter((c) => c.count > 0)
    .sort((a, b) => b.count - a.count)

  if (isLoading || !entries.length) return null

  return (
    <div style={{
      flexShrink: 0,
      background: 'var(--bg-surface)',
      borderTop: '1px solid var(--border-primary)',
      padding: '8px 14px',
      display: 'flex',
      alignItems: 'center',
      gap: 0,
      overflow: 'hidden',
    }}>
      {/* Proportional colour bar */}
      <div style={{
        display: 'flex',
        height: 6,
        borderRadius: 3,
        overflow: 'hidden',
        width: 120,
        flexShrink: 0,
        marginRight: 12,
      }}>
        {entries.map((c) => (
          <div
            key={c.id}
            title={c.label + ': ' + c.count}
            style={{
              width: ((c.count / total) * 100) + '%',
              background: c.color,
              transition: 'width 0.4s',
            }}
          />
        ))}
      </div>

      {/* Category pills */}
      <div style={{
        display: 'flex',
        gap: 6,
        flexWrap: 'nowrap',
        overflowX: 'auto',
        flex: 1,
        scrollbarWidth: 'none',
        msOverflowStyle: 'none',
      }}>
        {entries.map((c) => {
          const active = activeCategories.includes(c.id)
          return (
            <button
              key={c.id}
              onClick={() => toggleCategory(c.id)}
              title={active ? 'Click to hide ' + c.label : 'Click to show ' + c.label}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 5,
                padding: '3px 8px',
                borderRadius: 100,
                border: '1px solid',
                borderColor: active ? c.color + '66' : 'var(--border-muted)',
                background:  active ? c.color + '15' : 'transparent',
                cursor: 'pointer',
                flexShrink: 0,
                transition: 'all 0.12s',
              }}
            >
              <span style={{
                width: 6, height: 6, borderRadius: '50%',
                background: active ? c.color : 'var(--text-faint)',
                flexShrink: 0,
              }} />
              <span style={{
                fontSize: 11, fontWeight: active ? 600 : 400,
                color: active ? 'var(--text-primary)' : 'var(--text-muted)',
                whiteSpace: 'nowrap',
              }}>
                {c.label}
              </span>
              <span style={{
                fontSize: 10,
                color: active ? c.color : 'var(--text-faint)',
                fontWeight: 600,
              }}>
                {c.count}
              </span>
            </button>
          )
        })}
      </div>

      {/* Total count */}
      <div style={{
        fontSize: 11,
        color: 'var(--text-muted)',
        flexShrink: 0,
        marginLeft: 10,
        paddingLeft: 10,
        borderLeft: '1px solid var(--border-primary)',
      }}>
        {total} shown
      </div>
    </div>
  )
}
"""

# =============================================================================
# App.jsx  -- fix layout + add CategoryBar below map
# =============================================================================
FILES["frontend/src/App.jsx"] = """import React, { useState, useEffect, useRef } from 'react'
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
"""

# =============================================================================
# FilterSidebar.jsx  -- set height:100% + overflowY:auto on scroll container
# (patch only the aside style -- the sidebar now lives in App.jsx's <aside>)
# We update FilterSidebar to be the scrolling inner container itself
# =============================================================================
OLD_SIDEBAR_ASIDE = """    <aside className="no-print filter-sidebar" style={{
      width:'var(--sidebar-w)', background:'var(--bg-surface)',
      borderRight:'1px solid var(--border-primary)',
      display:'flex', flexDirection:'column',
      overflow:'hidden', flexShrink:0,
    }}>
      <div style={{ overflowY:'auto', flex:1, padding:'14px 12px' }}>"""

NEW_SIDEBAR_ASIDE = """    <div className="no-print" style={{
      display:'flex', flexDirection:'column',
      flex:1, minHeight:0, overflow:'hidden',
    }}>
      <div style={{ overflowY:'auto', flex:1, minHeight:0, padding:'14px 12px' }}>"""

OLD_SIDEBAR_CLOSE = """      </div>
    </aside>"""

NEW_SIDEBAR_CLOSE = """      </div>
    </div>"""

# =============================================================================
# EventList.jsx  -- ensure the right panel fills height properly
# =============================================================================
OLD_EVENTLIST_OUTER = """    <div style={{
      width:       panelWidth,
      flexShrink:  0,
      display:     'flex',
      flexDirection: 'column',
      background:  'var(--bg-surface)',
      borderLeft:  '1px solid var(--border-primary)',
      overflow:    'hidden',
      transition:  'width 0.2s ease',
    }}>"""

NEW_EVENTLIST_OUTER = """    <div style={{
      width:         panelWidth,
      flexShrink:    0,
      display:       'flex',
      flexDirection: 'column',
      background:    'var(--bg-surface)',
      borderLeft:    '1px solid var(--border-primary)',
      overflow:      'hidden',
      transition:    'width 0.2s ease',
      height:        '100%',   /* explicit height so inner flex:1 works */
      minHeight:     0,
    }}>"""

# =============================================================================
# AboutPanel.jsx  -- add email to Yonas, add Dr. Teferi Demissie
# =============================================================================
OLD_YONAS_EMAIL = """          <a href="mailto:Y.Mersha@cgiar.org"
             style={{ fontSize: 12, color: '#378ADD', textDecoration: 'none',
                      display: 'flex', alignItems: 'center', gap: 5 }}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" strokeWidth="2" strokeLinecap="round"
                 strokeLinejoin="round">
              <rect x="2" y="4" width="20" height="16" rx="2"/>
              <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
            </svg>
            Y.Mersha@cgiar.org
          </a>"""

NEW_YONAS_AND_TEFERI = """          <a href="mailto:Y.Mersha@cgiar.org"
             style={{ fontSize: 12, color: '#378ADD', textDecoration: 'none',
                      display: 'flex', alignItems: 'center', gap: 5 }}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" strokeWidth="2" strokeLinecap="round"
                 strokeLinejoin="round">
              <rect x="2" y="4" width="20" height="16" rx="2"/>
              <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
            </svg>
            Y.Mersha@cgiar.org
          </a>
        </div>

        {/* Dr. Teferi Demissie */}
        <div style={{
          width: 44, height: 44, borderRadius: '50%', flexShrink: 0,
          background: '#E6F1FB', border: '2px solid #378ADD',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 14, fontWeight: 700, color: '#0C447C',
        }}>
          TD
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)',
                        marginBottom: 1 }}>
            Dr. Teferi Demissie
          </div>
          <div style={{ fontSize: 12, color: '#378ADD', fontWeight: 500,
                        marginBottom: 3 }}>
            Climate and Hydrology Researcher
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>
            International Livestock Research Institute (ILRI)
          </div>
          <a href="mailto:t.demissie@cgiar.org"
             style={{ fontSize: 12, color: '#378ADD', textDecoration: 'none',
                      display: 'flex', alignItems: 'center', gap: 5 }}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" strokeWidth="2" strokeLinecap="round"
                 strokeLinejoin="round">
              <rect x="2" y="4" width="20" height="16" rx="2"/>
              <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
            </svg>
            t.demissie@cgiar.org
          </a>"""

# =============================================================================
# Builder
# =============================================================================
def apply(path: Path, old: str, new: str, label: str) -> bool:
    if not path.exists():
        print(f"  SKIP  {label} (file not found)")
        return False
    txt = path.read_text(encoding="utf-8")
    if old not in txt:
        print(f"  SKIP  {label} (marker not found in {path.name})")
        return False
    path.write_text(txt.replace(old, new, 1), encoding="utf-8")
    ow(f"patch   {label}")
    return True


def build(root: Path):
    fe = root / "frontend"
    hdr(f"Layout + scroll + contacts fix in: {root}")
    created = patched = 0

    # 1. CategoryBar (new file)
    for rel, content in FILES.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        existed = target.exists()
        target.write_text(content, encoding="utf-8")
        (ow if existed else ok)(("update  " if existed else "create  ") + rel)
        if not existed: created += 1
        else: patched += 1

    # 2. FilterSidebar inner scroll container
    sb = fe / "src/components/FilterSidebar.jsx"
    if apply(sb, OLD_SIDEBAR_ASIDE,  NEW_SIDEBAR_ASIDE,  "FilterSidebar.jsx -- scroll wrapper"):
        patched += 1
    if apply(sb, OLD_SIDEBAR_CLOSE,  NEW_SIDEBAR_CLOSE,  "FilterSidebar.jsx -- closing tag"):
        patched += 1

    # 3. EventList height fix
    el = fe / "src/components/EventList.jsx"
    if apply(el, OLD_EVENTLIST_OUTER, NEW_EVENTLIST_OUTER, "EventList.jsx -- height:100%"):
        patched += 1

    # 4. AboutPanel contacts
    ap = fe / "src/components/AboutPanel.jsx"
    if apply(ap, OLD_YONAS_EMAIL, NEW_YONAS_AND_TEFERI, "AboutPanel.jsx -- contacts"):
        patched += 1

    # 5. ASCII check
    print()
    bad = []
    for f in list((fe/"src").rglob("*.jsx")) + list((fe/"src").rglob("*.js")):
        raw = f.read_bytes()
        for i, line in enumerate(raw.split(b"\n"), 1):
            if any(b > 127 for b in line):
                bad.append(f"  {f.name}:{i}")
    if bad:
        print("  WARN  Non-ASCII:")
        for b in bad[:6]: print(b)
    else:
        ok("ASCII-clean -- OXC safe")

    # 6. Verify
    print()
    checks = [
        ("CategoryBar",          fe/"src/components/CategoryBar.jsx",   "CategoryBar created"),
        ("CategoryBar",          fe/"src/App.jsx",                      "CategoryBar in App"),
        ("minHeight: 0",         fe/"src/App.jsx",                      "minHeight:0 flex fix"),
        ("overflowY:'auto'",     fe/"src/components/FilterSidebar.jsx", "sidebar scroll"),
        ("height:        '100%'",fe/"src/components/EventList.jsx",     "EventList height"),
        ("Teferi Demissie",      fe/"src/components/AboutPanel.jsx",    "Dr. Teferi added"),
        ("t.demissie@cgiar.org", fe/"src/components/AboutPanel.jsx",    "Teferi email"),
        ("Y.Mersha@cgiar.org",   fe/"src/components/AboutPanel.jsx",    "Yonas email present"),
    ]
    all_ok = True
    for needle, path, label in checks:
        found = path.exists() and needle in path.read_text(errors="ignore")
        if not found: all_ok = False
        print(f"  {'OK' if found else 'MISSING'}  {label}")

    hdr("Done")
    print(f"  Files created : {created}")
    print(f"  Patches applied: {patched}")
    print()
    print("  Layout fixes:")
    print("    Sidebar -- height:100% + minHeight:0 on wrapper, overflowY:auto on inner div")
    print("    EventList -- height:100% so right panel fills viewport correctly")
    print("    App.jsx -- minHeight:0 on all flex containers (fixes the white-space gap)")
    print()
    print("  White space below map:")
    print("    CategoryBar strip added -- proportional colour bar + clickable category pills")
    print("    Click any pill to toggle that category (same as sidebar)")
    print("    Shows event count per category and total events shown")
    print()
    print("  Contacts in About tab:")
    print("    Yonas Mersha -- Y.Mersha@cgiar.org")
    print("    Dr. Teferi Demissie -- t.demissie@cgiar.org")
    print("    Both have blue avatar initials, title, ILRI affiliation, email link")
    print()
    print("  Restart Vite:")
    print("    cd frontend && npm run dev")
    print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Fix layout scroll + contacts")
    parser.add_argument("--path", default=".", help="Project root (default: current dir)")
    args   = parser.parse_args()
    root   = Path(args.path).resolve()
    if not (root / "backend").exists():
        print(f"WARNING: {root} may not be project root. Continue? [y/N] ", end="")
        if input().strip().lower() != "y":
            sys.exit(0)
    build(root)

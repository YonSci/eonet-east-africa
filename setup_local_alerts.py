"""
setup_local_alerts.py
---------------------
Replaces the backend-dependent email subscription with a browser-local
alert system that works without any server:

  1. AlertSubscription.jsx  -- rewrites the component:
       - Subscriptions saved to localStorage (no backend needed)
       - Browser Notification API for real-time popup alerts
       - Email list stored locally -- shown when a new event fires
       - Export subscriptions as JSON
       - Shows clear status: "Saved locally -- notifications active"

  2. App.jsx notification watcher -- when EventWatcher detects new events,
     it checks localStorage subscriptions and fires browser notifications

Run from the eonet-east-africa project root:
    python setup_local_alerts.py
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
# AlertSubscription.jsx -- fully local, no backend
# =============================================================================
FILES["frontend/src/components/AlertSubscription.jsx"] = """import React, { useState, useEffect } from 'react'
import { CATEGORIES, COUNTRY_MAP } from '../store/useAppStore.js'

const STORAGE_KEY = 'net-ea-alert-subscriptions'

function loadSubs() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]') }
  catch { return [] }
}

function saveSubs(subs) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(subs)) }
  catch {}
}

function requestNotifPermission() {
  if (!('Notification' in window)) return Promise.resolve('unsupported')
  if (Notification.permission === 'granted') return Promise.resolve('granted')
  return Notification.requestPermission()
}

function getNotifPermission() {
  if (!('Notification' in window)) return 'unsupported'
  return Notification.permission
}

export default function AlertSubscription() {
  const [email,      setEmail]      = useState('')
  const [categories, setCategories] = useState(['wildfires', 'floods'])
  const [countries,  setCountries]  = useState([])
  const [subs,       setSubs]       = useState([])
  const [status,     setStatus]     = useState(null)
  const [notifPerm,  setNotifPerm]  = useState(getNotifPermission())
  const [activeTab,  setActiveTab]  = useState('subscribe')

  useEffect(() => { setSubs(loadSubs()) }, [])

  function toggleItem(list, setList, val) {
    setList(list.includes(val)
      ? list.filter((v) => v !== val)
      : [...list, val])
  }

  async function handleSubscribe() {
    if (!email.trim() || !email.includes('@')) {
      setStatus({ ok: false, msg: 'Please enter a valid email address.' })
      return
    }
    if (!categories.length) {
      setStatus({ ok: false, msg: 'Select at least one category to alert on.' })
      return
    }

    // Request browser notification permission
    const perm = await requestNotifPermission()
    setNotifPerm(perm)

    const sub = {
      id:         'sub-' + Date.now(),
      email:      email.trim(),
      categories,
      countries,
      createdAt:  new Date().toISOString(),
      active:     true,
    }

    const existing = loadSubs()
    const updated  = [
      ...existing.filter((s) => s.email !== sub.email),
      sub,
    ]
    saveSubs(updated)
    setSubs(updated)

    setStatus({
      ok:  true,
      msg: perm === 'granted'
        ? 'Subscription saved! Browser notifications are ON -- you will see a popup when new ' +
          sub.categories.map((c) => (CATEGORIES[c] || {}).label || c).join(', ') +
          ' events are detected.'
        : 'Subscription saved locally. Enable browser notifications for popup alerts ' +
          '(your browser blocked them -- check the address bar icon).',
    })
    setEmail('')
  }

  function handleDelete(id) {
    const updated = loadSubs().filter((s) => s.id !== id)
    saveSubs(updated)
    setSubs(updated)
    setStatus({ ok: true, msg: 'Subscription removed.' })
  }

  function handleExport() {
    const blob = new Blob([JSON.stringify(loadSubs(), null, 2)],
                          { type: 'application/json' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href = url; a.download = 'net-ea-subscriptions.json'; a.click()
    URL.revokeObjectURL(url)
  }

  async function handleTestNotif() {
    const perm = await requestNotifPermission()
    setNotifPerm(perm)
    if (perm === 'granted') {
      new Notification('NET-EA Test Alert', {
        body: 'Browser notifications are working! You will see alerts like this when new events are detected.',
        icon: '/favicon.svg',
      })
      setStatus({ ok: true, msg: 'Test notification sent -- check your notifications panel.' })
    } else {
      setStatus({ ok: false, msg: 'Notifications blocked by browser. Click the lock icon in the address bar and allow notifications for this site.' })
    }
  }

  // Tab styles
  function tabStyle(id) {
    const active = activeTab === id
    return {
      fontSize: 12, padding: '5px 14px', borderRadius: 6, cursor: 'pointer',
      border: '1px solid',
      borderColor: active ? '#1D9E75' : 'var(--border-primary)',
      background:  active ? '#1D9E75' : 'transparent',
      color:       active ? '#fff'    : 'var(--text-secondary)',
      fontWeight:  active ? 600 : 400,
    }
  }

  return (
    <div style={{
      background: '#ffffff',
      border: '1.5px solid var(--border-primary)',
      borderRadius: 10,
      padding: '18px 20px',
      marginBottom: 16,
    }}>
      {/* Header */}
      <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:6 }}>
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none"
          stroke="#1D9E75" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M22 17H2a3 3 0 0 0 3-3V9a7 7 0 0 1 14 0v5a3 3 0 0 0 3 3z"/>
          <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>
        </svg>
        <span style={{ fontSize:14, fontWeight:700, color:'var(--text-primary)' }}>
          Alert subscriptions
        </span>

        {/* Notification permission badge */}
        <span style={{
          marginLeft: 'auto', fontSize:11, fontWeight:500,
          padding:'2px 8px', borderRadius:100,
          background: notifPerm === 'granted' ? '#E1F5EE' : '#FAEEDA',
          color:       notifPerm === 'granted' ? '#085041' : '#633806',
          border: '1px solid ' + (notifPerm === 'granted' ? '#1D9E7544' : '#BA751744'),
        }}>
          {notifPerm === 'granted'
            ? 'Notifications ON'
            : notifPerm === 'denied'
              ? 'Notifications blocked'
              : 'Notifications off'}
        </span>
      </div>

      <p style={{ fontSize:12, color:'var(--text-muted)', marginBottom:14, lineHeight:1.6 }}>
        Subscriptions are stored in your browser. When the dashboard detects new events
        during its 15-minute refresh, you will receive a browser notification popup.
        No server or email required.
      </p>

      {/* Tab switcher */}
      <div style={{ display:'flex', gap:6, marginBottom:16 }}>
        <button style={tabStyle('subscribe')} onClick={() => setActiveTab('subscribe')}>
          Add subscription
        </button>
        <button style={tabStyle('list')} onClick={() => setActiveTab('list')}>
          My subscriptions ({subs.length})
        </button>
        <button
          onClick={handleTestNotif}
          style={{ fontSize:12, padding:'5px 14px', borderRadius:6, cursor:'pointer',
                   border:'1px solid var(--border-primary)', background:'transparent',
                   color:'var(--text-secondary)', marginLeft:'auto' }}>
          Test notification
        </button>
      </div>

      {/* --- Subscribe tab --- */}
      {activeTab === 'subscribe' && (
        <>
          {/* Email */}
          <div style={{ marginBottom:12 }}>
            <label style={{ fontSize:12, fontWeight:600, color:'var(--text-secondary)',
                            display:'block', marginBottom:5 }}>
              Your email (stored locally for reference)
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              style={{ width:'100%', fontSize:13, padding:'7px 10px',
                       border:'1px solid var(--border-primary)', borderRadius:6,
                       background:'var(--bg-elevated)', color:'var(--text-primary)',
                       outline:'none' }}
            />
          </div>

          {/* Categories */}
          <div style={{ marginBottom:12 }}>
            <label style={{ fontSize:12, fontWeight:600, color:'var(--text-secondary)',
                            display:'block', marginBottom:6 }}>
              Alert me about
            </label>
            <div style={{ display:'flex', flexWrap:'wrap', gap:6 }}>
              {Object.entries(CATEGORIES).map(([id, meta]) => {
                const on = categories.includes(id)
                return (
                  <button key={id}
                    onClick={() => toggleItem(categories, setCategories, id)}
                    style={{ fontSize:12, padding:'4px 10px', borderRadius:100,
                             border:'1px solid',
                             borderColor: on ? meta.color + '88' : 'var(--border-primary)',
                             background:  on ? meta.color + '22' : 'transparent',
                             color:       on ? meta.color : 'var(--text-muted)',
                             cursor:'pointer', fontWeight: on ? 600 : 400 }}>
                    {meta.label}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Countries */}
          <div style={{ marginBottom:16 }}>
            <label style={{ fontSize:12, fontWeight:600, color:'var(--text-secondary)',
                            display:'block', marginBottom:6 }}>
              Filter by country (empty = all countries)
            </label>
            <div style={{ display:'flex', flexWrap:'wrap', gap:6 }}>
              {Object.entries(COUNTRY_MAP).map(([iso, name]) => {
                const on = countries.includes(iso)
                return (
                  <button key={iso}
                    onClick={() => toggleItem(countries, setCountries, iso)}
                    style={{ fontSize:12, padding:'4px 10px', borderRadius:100,
                             border:'1px solid',
                             borderColor: on ? '#378ADD88' : 'var(--border-primary)',
                             background:  on ? '#378ADD22' : 'transparent',
                             color:       on ? '#185FA5' : 'var(--text-muted)',
                             cursor:'pointer', fontWeight: on ? 600 : 400 }}>
                    {name}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Status */}
          {status && (
            <div style={{ fontSize:12, padding:'9px 12px', borderRadius:7,
                          marginBottom:12, lineHeight:1.6,
                          background: status.ok ? '#E1F5EE' : '#FCEBEB',
                          color:      status.ok ? '#085041' : '#791F1F',
                          border:'1px solid ' + (status.ok ? '#1D9E7544' : '#E24B4A44') }}>
              {status.msg}
            </div>
          )}

          <button onClick={handleSubscribe} style={{
            width:'100%', padding:'9px', borderRadius:7, fontSize:13,
            border:'none', background:'#1D9E75', color:'#fff',
            cursor:'pointer', fontWeight:600,
          }}>
            Save subscription
          </button>

          <p style={{ fontSize:11, color:'var(--text-faint)', marginTop:10, lineHeight:1.5 }}>
            Stored in browser localStorage -- no data leaves your device.
            Allow notifications when prompted to receive popup alerts.
          </p>
        </>
      )}

      {/* --- My subscriptions tab --- */}
      {activeTab === 'list' && (
        <>
          {subs.length === 0 ? (
            <p style={{ fontSize:12, color:'var(--text-muted)', textAlign:'center',
                        padding:'20px 0' }}>
              No subscriptions yet. Add one in the "Add subscription" tab.
            </p>
          ) : (
            <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
              {subs.map((s) => (
                <div key={s.id} style={{
                  padding:'10px 12px', borderRadius:7,
                  background:'var(--bg-elevated)',
                  border:'1px solid var(--border-primary)',
                  display:'flex', alignItems:'flex-start', gap:10,
                }}>
                  <div style={{ flex:1 }}>
                    <div style={{ fontSize:13, fontWeight:600,
                                  color:'var(--text-primary)', marginBottom:3 }}>
                      {s.email}
                    </div>
                    <div style={{ fontSize:11, color:'var(--text-muted)',
                                  marginBottom:4 }}>
                      Categories: {s.categories
                        .map((c) => (CATEGORIES[c] || {}).label || c).join(', ')}
                    </div>
                    {s.countries && s.countries.length > 0 && (
                      <div style={{ fontSize:11, color:'var(--text-muted)' }}>
                        Countries: {s.countries
                          .map((c) => COUNTRY_MAP[c] || c).join(', ')}
                      </div>
                    )}
                    <div style={{ fontSize:10, color:'var(--text-faint)', marginTop:3 }}>
                      Added {new Date(s.createdAt).toLocaleDateString()}
                    </div>
                  </div>
                  <button onClick={() => handleDelete(s.id)} style={{
                    fontSize:11, padding:'3px 8px', borderRadius:5,
                    border:'1px solid #E24B4A44', background:'#FCEBEB',
                    color:'#791F1F', cursor:'pointer', flexShrink:0,
                  }}>
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}

          {subs.length > 0 && (
            <button onClick={handleExport} style={{
              marginTop:12, fontSize:12, padding:'5px 12px', borderRadius:6,
              border:'1px solid var(--border-primary)', background:'transparent',
              color:'var(--text-secondary)', cursor:'pointer',
            }}>
              Export subscriptions JSON
            </button>
          )}
        </>
      )}
    </div>
  )
}
"""

# =============================================================================
# App.jsx notification watcher patch -- fire browser notifications for new events
# =============================================================================
OLD_EVENT_WATCHER = """function EventWatcher() {
  const { data: events }  = useEvents()
  const addToast          = useAppStore((s) => s.addToast)
  const prevIdsRef        = useRef(null)
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
}"""

NEW_EVENT_WATCHER = """const SUBS_KEY = 'net-ea-alert-subscriptions'

function matchesSub(ev, sub) {
  // Category filter
  if (sub.categories && sub.categories.length > 0) {
    if (!sub.categories.includes(ev.category)) return false
  }
  // Country filter
  if (sub.countries && sub.countries.length > 0) {
    const bbox = {
      DJ:{minLat:10,maxLat:13,minLon:41,maxLon:44},
      ER:{minLat:12,maxLat:18,minLon:36,maxLon:44},
      ET:{minLat:3, maxLat:15,minLon:33,maxLon:48},
      KE:{minLat:-5,maxLat:5, minLon:33,maxLon:42},
      RW:{minLat:-3,maxLat:0, minLon:28,maxLon:31},
      SO:{minLat:-2,maxLat:12,minLon:40,maxLon:52},
      SS:{minLat:3, maxLat:12,minLon:24,maxLon:36},
      SD:{minLat:9, maxLat:22,minLon:21,maxLon:38},
      TZ:{minLat:-12,maxLat:0,minLon:29,maxLon:41},
      UG:{minLat:-2,maxLat:4, minLon:29,maxLon:35},
      BI:{minLat:-5,maxLat:-2,minLon:28,maxLon:31},
    }
    const coords = ev.coords
    if (!coords) return false
    const lon = coords[0]; const lat = coords[1]
    const inCountry = sub.countries.some((iso) => {
      const b = bbox[iso]
      return b && lon >= b.minLon && lon <= b.maxLon &&
                  lat >= b.minLat && lat <= b.maxLat
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
      const title = 'NET-EA: ' + matched.length + ' new event' +
        (matched.length > 1 ? 's' : '') + ' detected'
      const body  = matched.slice(0, 3).map((e) => e.title).join('\\n') +
        (matched.length > 3 ? '\\n...and ' + (matched.length - 3) + ' more' : '')
      new Notification(title, { body, icon: '/favicon.svg', tag: 'net-ea-alert' })
    })
  } catch {}
}

function EventWatcher() {
  const { data: events }  = useEvents()
  const addToast          = useAppStore((s) => s.addToast)
  const prevIdsRef        = useRef(null)
  useEffect(() => {
    if (!events || events.length === 0) return
    const currentIds = new Set(events.map((e) => e.id))
    if (prevIdsRef.current !== null && prevIdsRef.current.size > 0) {
      const newEvs = events.filter((e) => !prevIdsRef.current.has(e.id))
      if (newEvs.length > 0) {
        const names = newEvs.slice(0, 2).map((e) => e.title).join('; ')
        addToast(newEvs.length + ' new event' +
          (newEvs.length > 1 ? 's' : '') + ': ' + names, 'info')
        // Fire browser notifications for matching subscriptions
        fireNotifications(newEvs)
      }
    }
    prevIdsRef.current = currentIds
  }, [events, addToast])
  return null
}"""


def apply(path, old, new, label):
    if not path.exists():
        print(f"  SKIP  {label} (not found)")
        return False
    txt = path.read_text(encoding="utf-8")
    if old not in txt:
        print(f"  SKIP  {label} (marker not found)")
        return False
    path.write_text(txt.replace(old, new, 1), encoding="utf-8")
    ow(f"patch   {label}")
    return True


def build(root: Path):
    fe = root / "frontend"
    hdr(f"Replacing alert subscription with browser-local system in: {root}")
    created = updated = 0

    # 1. Rewrite AlertSubscription.jsx
    for rel, content in FILES.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        existed = target.exists()
        target.write_text(content, encoding="utf-8")
        (ow if existed else ok)(("update  " if existed else "create  ") + rel)
        if existed: updated += 1
        else: created += 1

    # 2. Patch EventWatcher in App.jsx
    app = fe / "src/App.jsx"
    if apply(app, OLD_EVENT_WATCHER, NEW_EVENT_WATCHER, "App.jsx -- EventWatcher + browser notifications"):
        updated += 1

    # ASCII check
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

    # Verify
    print()
    checks = [
        ("localStorage",          fe/"src/components/AlertSubscription.jsx", "localStorage storage"),
        ("Notification.permission",fe/"src/components/AlertSubscription.jsx","browser Notification API"),
        ("Test notification",     fe/"src/components/AlertSubscription.jsx", "test button"),
        ("My subscriptions",      fe/"src/components/AlertSubscription.jsx", "subscriptions list tab"),
        ("fireNotifications",     fe/"src/App.jsx",                          "notification firing"),
        ("net-ea-alert-subscriptions", fe/"src/App.jsx",                     "storage key in watcher"),
    ]
    all_ok = True
    for needle, path, label in checks:
        found = path.exists() and needle in path.read_text(errors="ignore")
        if not found: all_ok = False
        print(f"  {'OK' if found else 'MISSING'}  {label}")

    hdr("Done")
    print(f"  Files created : {created}")
    print(f"  Files updated : {updated}")
    print()
    print("  How the new alert system works (no backend needed):")
    print()
    print("  1. User fills in email + selects categories + countries")
    print("  2. Click 'Save subscription' -- stored in browser localStorage")
    print("  3. Browser asks permission to send notifications")
    print("  4. Every 15 minutes when new events are detected, EventWatcher")
    print("     checks localStorage subscriptions and fires Notification API popups")
    print("  5. 'Test notification' button sends an immediate test popup")
    print()
    print("  Features:")
    print("    Tab 1: Add subscription -- email, categories, countries")
    print("    Tab 2: My subscriptions -- list all saved subs, delete, export JSON")
    print("    Badge: shows Notifications ON / off / blocked")
    print("    Test button: sends immediate test browser notification")
    print()
    print("  Note: browser notifications require:")
    print("    - Allow when browser prompts (or click address bar lock icon)")
    print("    - Page must be open (or a PWA installed) to receive alerts")
    print("    - Works on Chrome, Edge, Firefox -- NOT on iOS Safari")
    print()
    print("  Restart Vite:")
    print("    cd frontend && npm run dev")
    print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Browser-local alert subscriptions")
    parser.add_argument("--path", default=".")
    args   = parser.parse_args()
    root   = Path(args.path).resolve()
    if not (root / "backend").exists():
        print(f"WARNING: {root} may not be project root. Continue? [y/N] ", end="")
        if input().strip().lower() != "y":
            sys.exit(0)
    build(root)

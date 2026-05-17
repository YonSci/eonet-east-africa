import React, { useState, useEffect } from 'react'
import { CATEGORIES, COUNTRY_MAP } from '../store/useAppStore.js'
import {
  sendConfirmationEmail,
  EMAILJS_CONFIGURED,
} from '../api/emailService.js'

const STORAGE_KEY = 'nhmt-ea-alert-subscriptions'

function loadSubs() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]') }
  catch { return [] }
}
function saveSubs(subs) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(subs)) }
  catch {}
}

function requestNotifPerm() {
  if (!('Notification' in window)) return Promise.resolve('unsupported')
  if (Notification.permission === 'granted') return Promise.resolve('granted')
  return Notification.requestPermission()
}

export default function AlertSubscription() {
  const [email,      setEmail]     = useState('')
  const [categories, setCategories]= useState(['wildfires', 'floods'])
  const [countries,  setCountries] = useState([])
  const [subs,       setSubs]      = useState([])
  const [status,     setStatus]    = useState(null)
  const [loading,    setLoading]   = useState(false)
  const [notifPerm,  setNotifPerm] = useState(
    typeof Notification !== 'undefined' ? Notification.permission : 'unsupported'
  )
  const [activeTab,  setActiveTab] = useState('subscribe')

  useEffect(() => { setSubs(loadSubs()) }, [])

  function toggle(list, setList, val) {
    setList(list.includes(val) ? list.filter((v) => v !== val) : [...list, val])
  }

  async function handleSubscribe() {
    if (!email.trim() || !email.includes('@')) {
      setStatus({ ok: false, msg: 'Please enter a valid email address.' })
      return
    }
    if (!categories.length) {
      setStatus({ ok: false, msg: 'Select at least one category.' })
      return
    }

    setLoading(true)
    setStatus(null)

    // Save to localStorage
    const sub = {
      id: 'sub-' + Date.now(),
      email: email.trim(),
      categories, countries,
      createdAt: new Date().toISOString(),
    }
    const updated = [...loadSubs().filter((s) => s.email !== sub.email), sub]
    saveSubs(updated)
    setSubs(updated)

    // Request browser notification permission
    const perm = await requestNotifPerm()
    setNotifPerm(perm)

    // Send confirmation email via EmailJS
    const msgs = []
    if (EMAILJS_CONFIGURED) {
      const result = await sendConfirmationEmail({
        email: sub.email,
        categories: sub.categories,
        countries: sub.countries,
      })
      if (result.ok) {
        msgs.push('Confirmation email sent to ' + sub.email + '.')
      } else {
        msgs.push('Could not send confirmation email (' + result.reason + ').')
      }
    } else {
      msgs.push('EmailJS not configured -- no confirmation email sent.')
    }

    // Browser notifications note
    if (perm === 'granted') {
      msgs.push('Browser notifications ON -- popup alerts active.')
    } else {
      msgs.push('Browser notifications OFF -- allow them in the address bar for popup alerts.')
    }

    setStatus({ ok: true, msg: msgs.join(' ') })
    setEmail('')
    setLoading(false)
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
    const perm = await requestNotifPerm()
    setNotifPerm(perm)
    if (perm === 'granted') {
      new Notification('NHMT-EA Test Alert', {
        body: 'Notifications are working! You will see alerts like this when new events are detected.',
        icon: '/favicon.svg',
      })
      setStatus({ ok: true, msg: 'Test notification sent.' })
    } else {
      setStatus({ ok: false, msg: 'Notifications blocked. Click the lock icon in the address bar -> Allow.' })
    }
  }

  function tabStyle(id) {
    const a = activeTab === id
    return {
      fontSize: 12, padding: '5px 14px', borderRadius: 6, cursor: 'pointer',
      border: '1px solid',
      borderColor: a ? '#1D9E75' : 'var(--border-primary)',
      background:  a ? '#1D9E75' : 'transparent',
      color:       a ? '#fff'    : 'var(--text-secondary)',
      fontWeight:  a ? 600 : 400,
    }
  }

  const catLabel = (id) => (CATEGORIES[id] || {}).label || id

  return (
    <div style={{
      background: '#ffffff', border: '1.5px solid var(--border-primary)',
      borderRadius: 10, padding: '18px 20px', marginBottom: 16,
    }}>
      {/* Header */}
      <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:6 }}>
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none"
          stroke="#1D9E75" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M22 17H2a3 3 0 0 0 3-3V9a7 7 0 0 1 14 0v5a3 3 0 0 0 3 3z"/>
          <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>
        </svg>
        <span style={{ fontSize:14, fontWeight:700, color:'var(--text-primary)' }}>
          Event alert subscriptions
        </span>
        <div style={{ marginLeft:'auto', display:'flex', alignItems:'center', gap:6 }}>
          {/* EmailJS status */}
          <span style={{
            fontSize:10, fontWeight:500, padding:'2px 7px', borderRadius:100,
            background: EMAILJS_CONFIGURED ? '#E1F5EE' : '#F1EFE8',
            color:      EMAILJS_CONFIGURED ? '#085041' : '#444441',
            border: '1px solid ' + (EMAILJS_CONFIGURED ? '#1D9E7533' : '#d1d9e0'),
          }}>
            {EMAILJS_CONFIGURED ? 'Email ON' : 'Email: setup needed'}
          </span>
          {/* Notification status */}
          <span style={{
            fontSize:10, fontWeight:500, padding:'2px 7px', borderRadius:100,
            background: notifPerm === 'granted' ? '#E1F5EE' : '#FAEEDA',
            color:      notifPerm === 'granted' ? '#085041' : '#633806',
            border: '1px solid ' + (notifPerm === 'granted' ? '#1D9E7533' : '#BA751733'),
          }}>
            {notifPerm === 'granted' ? 'Popup ON' : 'Popup OFF'}
          </span>
        </div>
      </div>

      <p style={{ fontSize:12, color:'var(--text-muted)', marginBottom:14, lineHeight:1.6 }}>
        Subscribe to receive alerts when new events matching your filters are detected.
        {EMAILJS_CONFIGURED
          ? ' Email confirmation and alerts will be sent via EmailJS.'
          : ' Configure EmailJS in .env.local for email delivery (see setup guide below).'}
      </p>

      {/* Tabs */}
      <div style={{ display:'flex', gap:6, marginBottom:16, flexWrap:'wrap' }}>
        <button style={tabStyle('subscribe')} onClick={() => setActiveTab('subscribe')}>
          Subscribe
        </button>
        <button style={tabStyle('list')} onClick={() => setActiveTab('list')}>
          My subscriptions ({subs.length})
        </button>
        {!EMAILJS_CONFIGURED && (
          <button style={tabStyle('setup')} onClick={() => setActiveTab('setup')}>
            Email setup
          </button>
        )}
        <button onClick={handleTestNotif}
          style={{ fontSize:12, padding:'5px 12px', borderRadius:6, cursor:'pointer',
                   border:'1px solid var(--border-primary)', background:'transparent',
                   color:'var(--text-secondary)', marginLeft:'auto' }}>
          Test popup
        </button>
      </div>

      {/* ---- SUBSCRIBE TAB ---- */}
      {activeTab === 'subscribe' && (
        <>
          <div style={{ marginBottom:12 }}>
            <label style={{ fontSize:12, fontWeight:600, color:'var(--text-secondary)',
                            display:'block', marginBottom:5 }}>
              Email address
            </label>
            <input type="email" value={email}
              onChange={(e) => setEmail(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSubscribe()}
              placeholder="you@example.com"
              style={{ width:'100%', fontSize:13, padding:'7px 10px',
                       border:'1px solid var(--border-primary)', borderRadius:6,
                       background:'var(--bg-elevated)', color:'var(--text-primary)',
                       outline:'none' }} />
          </div>

          <div style={{ marginBottom:12 }}>
            <label style={{ fontSize:12, fontWeight:600, color:'var(--text-secondary)',
                            display:'block', marginBottom:6 }}>
              Alert me about
            </label>
            <div style={{ display:'flex', flexWrap:'wrap', gap:6 }}>
              {Object.entries(CATEGORIES).map(([id, meta]) => {
                const on = categories.includes(id)
                return (
                  <button key={id} onClick={() => toggle(categories, setCategories, id)}
                    style={{ fontSize:12, padding:'4px 10px', borderRadius:100,
                             border:'1px solid',
                             borderColor: on ? meta.color+'88' : 'var(--border-primary)',
                             background:  on ? meta.color+'22' : 'transparent',
                             color:       on ? meta.color : 'var(--text-muted)',
                             cursor:'pointer', fontWeight: on ? 600 : 400 }}>
                    {meta.label}
                  </button>
                )
              })}
            </div>
          </div>

          <div style={{ marginBottom:16 }}>
            <label style={{ fontSize:12, fontWeight:600, color:'var(--text-secondary)',
                            display:'block', marginBottom:6 }}>
              Countries (empty = all)
            </label>
            <div style={{ display:'flex', flexWrap:'wrap', gap:6 }}>
              {Object.entries(COUNTRY_MAP).map(([iso, name]) => {
                const on = countries.includes(iso)
                return (
                  <button key={iso} onClick={() => toggle(countries, setCountries, iso)}
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

          {status && (
            <div style={{ fontSize:12, padding:'9px 12px', borderRadius:7,
                          marginBottom:12, lineHeight:1.6,
                          background: status.ok ? '#E1F5EE' : '#FCEBEB',
                          color:      status.ok ? '#085041' : '#791F1F',
                          border:'1px solid '+(status.ok ? '#1D9E7544' : '#E24B4A44') }}>
              {status.msg}
            </div>
          )}

          <button onClick={handleSubscribe} disabled={loading} style={{
            width:'100%', padding:'9px', borderRadius:7, fontSize:13,
            border:'none', background:'#1D9E75', color:'#fff',
            cursor: loading ? 'wait' : 'pointer', fontWeight:600,
            opacity: loading ? 0.7 : 1,
          }}>
            {loading ? 'Saving...' : 'Save subscription'}
          </button>
        </>
      )}

      {/* ---- MY SUBSCRIPTIONS TAB ---- */}
      {activeTab === 'list' && (
        <>
          {subs.length === 0 ? (
            <p style={{ fontSize:12, color:'var(--text-muted)', textAlign:'center',
                        padding:'20px 0' }}>
              No subscriptions yet. Add one above.
            </p>
          ) : (
            <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
              {subs.map((s) => (
                <div key={s.id} style={{
                  padding:'12px 14px', borderRadius:8, background:'var(--bg-elevated)',
                  border:'1px solid var(--border-primary)',
                  display:'flex', alignItems:'flex-start', gap:10,
                }}>
                  <div style={{ flex:1 }}>
                    <div style={{ fontSize:13, fontWeight:600,
                                  color:'var(--text-primary)', marginBottom:3 }}>
                      {s.email}
                    </div>
                    <div style={{ fontSize:11, color:'var(--text-muted)', marginBottom:2 }}>
                      {s.categories.map(catLabel).join(', ')}
                    </div>
                    {s.countries && s.countries.length > 0 && (
                      <div style={{ fontSize:11, color:'var(--text-muted)' }}>
                        {s.countries.map((c) => COUNTRY_MAP[c] || c).join(', ')}
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
              marginTop:10, fontSize:12, padding:'5px 12px', borderRadius:6,
              border:'1px solid var(--border-primary)', background:'transparent',
              color:'var(--text-secondary)', cursor:'pointer',
            }}>
              Export JSON
            </button>
          )}
        </>
      )}

      {/* ---- EMAIL SETUP TAB ---- */}
      {activeTab === 'setup' && (
        <div style={{ fontSize:12, color:'var(--text-secondary)', lineHeight:1.8 }}>
          <div style={{ fontWeight:600, color:'var(--text-primary)',
                        marginBottom:10, fontSize:13 }}>
            Set up EmailJS in 5 minutes (free)
          </div>
          {[
            ['1', 'Sign up', 'Go to emailjs.com and create a free account (200 emails/month)'],
            ['2', 'Add email service', 'Dashboard -> Email Services -> Add Service -> Gmail -> Connect your Gmail'],
            ['3', 'Create confirmation template', 'Email Templates -> Create Template. Name it "NHMT-EA Confirmation". Set To Email to {{to_email}}. Subject: "You are subscribed to NHMT-EA". Add body with {{categories}} and {{countries}} variables.'],
            ['4', 'Create alert template', 'Create another template "NHMT-EA Alert". Subject: "NHMT-EA: {{event_count}} new events". Body: use {{event_list}}, {{categories}}, {{countries}}.'],
            ['5', 'Add keys to .env.local', 'Copy Public Key from Account -> API Keys. Copy Service ID and Template IDs. Paste into frontend/.env.local'],
          ].map(([n, title, desc]) => (
            <div key={n} style={{ display:'flex', gap:10, marginBottom:10,
                                  padding:'8px 10px', borderRadius:6,
                                  background:'var(--bg-elevated)' }}>
              <span style={{ fontWeight:700, color:'#1D9E75', flexShrink:0,
                             minWidth:16 }}>{n}.</span>
              <div>
                <div style={{ fontWeight:600, color:'var(--text-primary)',
                              marginBottom:2 }}>{title}</div>
                <div style={{ fontSize:11, color:'var(--text-muted)' }}>{desc}</div>
              </div>
            </div>
          ))}
          <div style={{ marginTop:12, padding:'10px 12px', borderRadius:6,
                        background:'#E1F5EE', border:'1px solid #1D9E7533',
                        fontSize:11, color:'#085041', fontFamily:'monospace' }}>
            VITE_EMAILJS_PUBLIC_KEY=your_key<br/>
            VITE_EMAILJS_SERVICE_ID=service_xxx<br/>
            VITE_EMAILJS_TEMPLATE_CONFIRM=template_xxx<br/>
            VITE_EMAILJS_TEMPLATE_ALERT=template_xxx
          </div>
          <p style={{ marginTop:8, fontSize:11, color:'var(--text-muted)' }}>
            After adding keys to .env.local, restart Vite and refresh. The
            "Email: setup needed" badge will change to "Email ON".
          </p>
        </div>
      )}
    </div>
  )
}

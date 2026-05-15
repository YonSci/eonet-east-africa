import React, { useState } from 'react'
import { CATEGORIES, COUNTRY_MAP } from '../store/useAppStore.js'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

export default function AlertSubscription() {
  const [email,      setEmail]      = useState('')
  const [categories, setCategories] = useState(['wildfires', 'floods'])
  const [countries,  setCountries]  = useState(['KE', 'ET'])
  const [status,     setStatus]     = useState(null)
  const [loading,    setLoading]    = useState(false)

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
      setStatus({ ok: false, msg: 'Select at least one event category.' })
      return
    }
    setLoading(true)
    setStatus(null)
    try {
      const res = await fetch(API_BASE + '/alerts/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), categories, countries }),
      })
      if (res.ok) {
        setStatus({ ok: true, msg: 'Subscribed! You will receive alerts when new events are detected.' })
      } else {
        const d = await res.json().catch(() => ({}))
        setStatus({ ok: false, msg: d.detail || 'Subscription failed. Is the backend running?' })
      }
    } catch {
      setStatus({
        ok: false,
        msg: 'Backend not reachable. To use email alerts, start the FastAPI backend with: uvicorn backend.main:app --reload --port 8000',
      })
    }
    setLoading(false)
  }

  async function handleUnsubscribe() {
    if (!email.trim()) return
    setLoading(true)
    try {
      await fetch(API_BASE + '/alerts/unsubscribe/' + encodeURIComponent(email.trim()),
        { method: 'DELETE' })
      setStatus({ ok: true, msg: 'Unsubscribed successfully.' })
    } catch {
      setStatus({ ok: false, msg: 'Could not reach backend.' })
    }
    setLoading(false)
  }

  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border-primary)',
      borderRadius: 'var(--radius-lg)',
      padding: '16px 18px',
      marginBottom: 16,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
          stroke="#1D9E75" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M22 17H2a3 3 0 0 0 3-3V9a7 7 0 0 1 14 0v5a3 3 0 0 0 3 3z"/>
          <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>
        </svg>
        <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
          Email alert subscriptions
        </span>
      </div>
      <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 14, lineHeight: 1.5 }}>
        Receive an email when new events matching your filters are detected during the 15-minute refresh.
        Requires the FastAPI backend to be running with SMTP configured.
      </p>

      {/* Email */}
      <div style={{ marginBottom: 12 }}>
        <label style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-secondary)',
                        display: 'block', marginBottom: 4 }}>
          Email address
        </label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          style={{
            width: '100%', fontSize: 13, padding: '6px 10px',
            border: '1px solid var(--border-primary)', borderRadius: 6,
            background: 'var(--bg-elevated)', color: 'var(--text-primary)',
            outline: 'none',
          }}
        />
      </div>

      {/* Categories */}
      <div style={{ marginBottom: 12 }}>
        <label style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-secondary)',
                        display: 'block', marginBottom: 6 }}>
          Alert on categories
        </label>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
          {Object.entries(CATEGORIES).map(([id, meta]) => {
            const on = categories.includes(id)
            return (
              <button key={id}
                onClick={() => toggleItem(categories, setCategories, id)}
                style={{
                  fontSize: 11, padding: '3px 8px', borderRadius: 100,
                  border: '1px solid',
                  borderColor: on ? meta.color + '66' : 'var(--border-primary)',
                  background: on ? meta.color + '20' : 'transparent',
                  color: on ? meta.color : 'var(--text-muted)',
                  cursor: 'pointer', fontWeight: on ? 500 : 400,
                }}>
                {meta.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* Countries */}
      <div style={{ marginBottom: 14 }}>
        <label style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-secondary)',
                        display: 'block', marginBottom: 6 }}>
          Filter by country (empty = all countries)
        </label>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
          {Object.entries(COUNTRY_MAP).map(([iso, name]) => {
            const on = countries.includes(iso)
            return (
              <button key={iso}
                onClick={() => toggleItem(countries, setCountries, iso)}
                style={{
                  fontSize: 11, padding: '3px 8px', borderRadius: 100,
                  border: '1px solid',
                  borderColor: on ? '#378ADD66' : 'var(--border-primary)',
                  background: on ? '#378ADD20' : 'transparent',
                  color: on ? '#185FA5' : 'var(--text-muted)',
                  cursor: 'pointer', fontWeight: on ? 500 : 400,
                }}>
                {name}
              </button>
            )
          })}
        </div>
      </div>

      {/* Status message */}
      {status && (
        <div style={{
          fontSize: 12, padding: '8px 10px', borderRadius: 6, marginBottom: 10,
          background: status.ok ? '#E1F5EE' : '#FCEBEB',
          color: status.ok ? '#085041' : '#791F1F',
          border: '1px solid ' + (status.ok ? '#1D9E7544' : '#E24B4A44'),
          lineHeight: 1.5,
        }}>
          {status.msg}
        </div>
      )}

      {/* Buttons */}
      <div style={{ display: 'flex', gap: 8 }}>
        <button onClick={handleSubscribe} disabled={loading} style={{
          flex: 1, padding: '7px', borderRadius: 6, fontSize: 12,
          border: 'none', background: '#1D9E75', color: '#fff',
          cursor: loading ? 'wait' : 'pointer', fontWeight: 500,
          opacity: loading ? 0.7 : 1,
        }}>
          {loading ? 'Saving...' : 'Subscribe'}
        </button>
        <button onClick={handleUnsubscribe} disabled={loading || !email} style={{
          flex: 1, padding: '7px', borderRadius: 6, fontSize: 12,
          border: '1px solid var(--border-primary)',
          background: 'transparent', color: 'var(--text-secondary)',
          cursor: loading ? 'wait' : 'pointer',
          opacity: (loading || !email) ? 0.5 : 1,
        }}>
          Unsubscribe
        </button>
      </div>

      <p style={{ fontSize: 10, color: 'var(--text-faint)', marginTop: 10, lineHeight: 1.5 }}>
        Subscriptions are stored in the backend. Configure SMTP via environment variables:
        SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS.
      </p>
    </div>
  )
}

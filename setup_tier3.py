"""
setup_tier3.py
--------------
Adds all 4 Tier 3 nice-to-have features to NET-EA:

  1. PWA + offline mode     -- installable app, service worker, offline banner
  2. Email alert subscriptions -- subscribe to new events by category/country
  3. District-level boundaries -- GADM Level-1 boundaries per selected country
  4. Saved filter presets   -- localStorage-based named filter bookmarks

Run from the eonet-east-africa project root:
    python setup_tier3.py

After running:
    cd frontend
    npm install          <-- installs vite-plugin-pwa
    npm run dev

Backend email alerts require:
    Add to .env:  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM
    Then:  uvicorn backend.main:app --reload --port 8000
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
# package.json -- add vite-plugin-pwa
# =============================================================================
FILES["frontend/package.json"] = """{
  "name": "eonet-east-africa",
  "private": true,
  "version": "3.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-leaflet": "^4.2.1",
    "leaflet": "^1.9.4",
    "react-leaflet-cluster": "^2.1.0",
    "@tanstack/react-query": "^5.56.2",
    "zustand": "^4.5.5",
    "recharts": "^2.12.7",
    "date-fns": "^3.6.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.1",
    "vite": "^5.4.8",
    "vite-plugin-pwa": "^0.20.5",
    "workbox-window": "^7.3.0"
  }
}
"""

# =============================================================================
# vite.config.js -- add VitePWA plugin
# =============================================================================
FILES["frontend/vite.config.js"] = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

function silentProxy(target) {
  return {
    target,
    changeOrigin: true,
    configure: (proxy) => { proxy.on('error', () => {}) },
  }
}

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'favicon.svg'],
      manifest: {
        name: 'NET-EA -- Natural Event Tracker for East Africa',
        short_name: 'NET-EA',
        description: 'Near real-time natural hazard monitoring for the Greater Horn of Africa',
        theme_color: '#1D9E75',
        background_color: '#f6f8fa',
        display: 'standalone',
        start_url: '/',
        scope: '/',
        icons: [
          { src: '/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icon-512.png', sizes: '512x512', type: 'image/png',
            purpose: 'any maskable' },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        runtimeCaching: [
          {
            urlPattern: ({ url }) => url.hostname === 'eonet.gsfc.nasa.gov',
            handler: 'NetworkFirst',
            options: {
              cacheName: 'eonet-api',
              networkTimeoutSeconds: 10,
              expiration: { maxEntries: 10, maxAgeSeconds: 86400 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            urlPattern: ({ url }) => url.hostname.includes('cartocdn.com'),
            handler: 'CacheFirst',
            options: {
              cacheName: 'map-tiles',
              expiration: { maxEntries: 500, maxAgeSeconds: 7 * 86400 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            urlPattern: ({ url }) => url.hostname.includes('gibs.earthdata.nasa.gov'),
            handler: 'NetworkFirst',
            options: {
              cacheName: 'gibs-tiles',
              networkTimeoutSeconds: 8,
              expiration: { maxEntries: 100, maxAgeSeconds: 86400 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
        ],
      },
    }),
  ],
  base: '/',
  server: {
    port: 5173,
    proxy: {
      '/events':  silentProxy('http://localhost:8000'),
      '/summary': silentProxy('http://localhost:8000'),
      '/status':  silentProxy('http://localhost:8000'),
      '/alerts':  silentProxy('http://localhost:8000'),
    },
  },
  build: { outDir: 'dist', sourcemap: false },
})
"""

# =============================================================================
# public/favicon.svg -- simple satellite SVG icon
# =============================================================================
FILES["frontend/public/favicon.svg"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect width="100" height="100" rx="20" fill="#1D9E75"/>
  <text y="72" x="50" text-anchor="middle" font-size="60" fill="white">N</text>
</svg>
"""

# =============================================================================
# OfflineBanner.jsx -- shows when network is unavailable
# =============================================================================
FILES["frontend/src/components/OfflineBanner.jsx"] = """import React, { useState, useEffect } from 'react'

export default function OfflineBanner() {
  const [isOnline, setIsOnline]       = useState(
    typeof navigator !== 'undefined' ? navigator.onLine : true
  )
  const [justCameBack, setJustCameBack] = useState(false)

  useEffect(() => {
    function handleOnline() {
      setIsOnline(true)
      setJustCameBack(true)
      setTimeout(() => setJustCameBack(false), 3000)
    }
    function handleOffline() { setIsOnline(false) }
    window.addEventListener('online',  handleOnline)
    window.addEventListener('offline', handleOffline)
    return () => {
      window.removeEventListener('online',  handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  if (isOnline && !justCameBack) return null

  return (
    <div style={{
      position: 'fixed',
      top: 'var(--topnav-h)',
      left: 0, right: 0,
      zIndex: 10000,
      padding: '7px 16px',
      textAlign: 'center',
      fontSize: 12, fontWeight: 500,
      background: isOnline ? '#1D9E75' : '#BA7517',
      color: '#fff',
      transition: 'background 0.3s',
    }}>
      {isOnline
        ? 'Back online -- refreshing event data...'
        : 'You are offline -- showing last cached data. Real-time updates paused.'}
    </div>
  )
}
"""

# =============================================================================
# SavedFilters.jsx -- localStorage-based named filter presets
# =============================================================================
FILES["frontend/src/components/SavedFilters.jsx"] = """import React, { useState, useEffect, useCallback } from 'react'
import useAppStore, { ALL_CATS } from '../store/useAppStore.js'

const STORAGE_KEY = 'net-ea-filter-presets'

function loadPresets() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
  } catch { return [] }
}

function savePresetsToStorage(presets) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(presets)) } catch {}
}

// Default starter presets for East Africa
const DEFAULT_PRESETS = [
  {
    id: 'default-1',
    name: 'Active events (open)',
    savedAt: '2025-01-01T00:00:00Z',
    filters: {
      activeCategories: ALL_CATS,
      activeStatus: 'open',
      lookbackDays: 30,
      dateMode: 'lookback',
      startDate: '', endDate: '',
    },
  },
  {
    id: 'default-2',
    name: 'Wildfires + Floods (90d)',
    savedAt: '2025-01-01T00:00:00Z',
    filters: {
      activeCategories: ['wildfires', 'floods'],
      activeStatus: 'all',
      lookbackDays: 90,
      dateMode: 'lookback',
      startDate: '', endDate: '',
    },
  },
  {
    id: 'default-3',
    name: 'Seismic + Volcanic (1yr)',
    savedAt: '2025-01-01T00:00:00Z',
    filters: {
      activeCategories: ['earthquakes', 'volcanoes', 'landslides'],
      activeStatus: 'all',
      lookbackDays: 365,
      dateMode: 'lookback',
      startDate: '', endDate: '',
    },
  },
]

export default function SavedFilters() {
  const {
    activeCategories, activeStatus, lookbackDays,
    dateMode, startDate, endDate,
    setAllCategories, setStatus, setDays,
    setDateMode, setStartDate, setEndDate,
  } = useAppStore()

  const [presets,   setPresets]   = useState([])
  const [naming,    setNaming]    = useState(false)
  const [newName,   setNewName]   = useState('')
  const [saved,     setSaved]     = useState(false)

  useEffect(() => {
    const stored = loadPresets()
    setPresets(stored.length ? stored : DEFAULT_PRESETS)
  }, [])

  const applyPreset = useCallback((p) => {
    const f = p.filters
    setAllCategories(f.activeCategories)
    setStatus(f.activeStatus)
    setDays(f.lookbackDays)
    setDateMode(f.dateMode)
    setStartDate(f.startDate || '')
    setEndDate(f.endDate || '')
  }, [setAllCategories, setStatus, setDays, setDateMode, setStartDate, setEndDate])

  function handleSave() {
    if (!newName.trim()) return
    const preset = {
      id: 'preset-' + Date.now(),
      name: newName.trim(),
      savedAt: new Date().toISOString(),
      filters: {
        activeCategories, activeStatus, lookbackDays,
        dateMode, startDate, endDate,
      },
    }
    const next = [...presets, preset]
    setPresets(next)
    savePresetsToStorage(next)
    setNaming(false)
    setNewName('')
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  function deletePreset(id) {
    const next = presets.filter((p) => p.id !== id)
    setPresets(next)
    savePresetsToStorage(next)
  }

  return (
    <div style={{ marginBottom: 18 }}>
      <p style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.08em',
                  textTransform: 'uppercase', color: 'var(--text-muted)',
                  marginBottom: 8 }}>
        Saved filters
      </p>

      {presets.map((p) => (
        <div key={p.id} style={{
          display: 'flex', alignItems: 'center', gap: 4,
          marginBottom: 5,
        }}>
          <button
            onClick={() => applyPreset(p)}
            title={'Load: ' + p.name}
            style={{
              flex: 1, textAlign: 'left', fontSize: 12,
              padding: '5px 8px', borderRadius: 5, cursor: 'pointer',
              border: '1px solid var(--border-primary)',
              background: 'var(--bg-elevated)',
              color: 'var(--text-secondary)',
              overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
            }}>
            {p.name}
          </button>
          {!p.id.startsWith('default-') && (
            <button
              onClick={() => deletePreset(p.id)}
              title="Delete preset"
              style={{
                background: 'none', border: 'none', cursor: 'pointer',
                color: 'var(--text-faint)', fontSize: 14, lineHeight: 1,
                padding: '3px 5px', borderRadius: 4,
              }}>
              x
            </button>
          )}
        </div>
      ))}

      {naming ? (
        <div style={{ marginTop: 6 }}>
          <input
            autoFocus
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') handleSave()
                                if (e.key === 'Escape') setNaming(false) }}
            placeholder="Preset name..."
            style={{
              width: '100%', fontSize: 12, padding: '5px 8px',
              border: '1px solid #1D9E75', borderRadius: 5, marginBottom: 5,
              background: 'var(--bg-elevated)', color: 'var(--text-primary)',
              outline: 'none',
            }}
          />
          <div style={{ display: 'flex', gap: 5 }}>
            <button onClick={handleSave} style={{
              flex: 1, padding: '4px', borderRadius: 5, fontSize: 11,
              border: 'none', background: '#1D9E75', color: '#fff',
              cursor: 'pointer', fontWeight: 500,
            }}>Save</button>
            <button onClick={() => setNaming(false)} style={{
              flex: 1, padding: '4px', borderRadius: 5, fontSize: 11,
              border: '1px solid var(--border-primary)',
              background: 'transparent', color: 'var(--text-secondary)',
              cursor: 'pointer',
            }}>Cancel</button>
          </div>
        </div>
      ) : (
        <button
          onClick={() => setNaming(true)}
          style={{
            width: '100%', marginTop: 4, padding: '5px 8px',
            fontSize: 12, borderRadius: 5, cursor: 'pointer',
            border: '1px dashed var(--border-primary)',
            background: 'transparent', color: 'var(--text-muted)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 5,
          }}>
          {saved ? 'Saved!' : '+ Save current filters'}
        </button>
      )}
    </div>
  )
}
"""

# =============================================================================
# AlertSubscription.jsx -- email alert subscription form
# =============================================================================
FILES["frontend/src/components/AlertSubscription.jsx"] = """import React, { useState } from 'react'
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
"""

# =============================================================================
# DistrictLayer.jsx -- GADM Level-1 boundaries per selected country
# =============================================================================
FILES["frontend/src/components/DistrictLayer.jsx"] = """import React, { useState, useEffect, useCallback } from 'react'
import { GeoJSON, useMap } from 'react-leaflet'

// ISO2 -> ISO3 mapping for GADM URLs
const ISO3 = {
  DJ:'DJI', ER:'ERI', ET:'ETH', KE:'KEN',
  RW:'RWA', SO:'SOM', SS:'SSD', SD:'SDN',
  TZ:'TZA', UG:'UGA', BI:'BDI',
}

const GADM_BASE = 'https://geodata.ucdavis.edu/gadm/gadm4.1/json'

// Cache fetched GeoJSON in memory to avoid repeated network calls
const geoCache = {}

async function fetchDistricts(iso2) {
  if (geoCache[iso2]) return geoCache[iso2]
  const iso3 = ISO3[iso2]
  if (!iso3) return null
  const url = GADM_BASE + '/gadm41_' + iso3 + '_1.json'
  const res  = await fetch(url, { signal: AbortSignal.timeout(15000) })
  if (!res.ok) throw new Error('HTTP ' + res.status)
  const data = await res.json()
  geoCache[iso2] = data
  return data
}

const DISTRICT_STYLE = {
  color:       '#7F77DD',
  weight:      0.8,
  fillColor:   '#7F77DD',
  fillOpacity: 0.04,
  dashArray:   '3 4',
}

export function DistrictLayer({ iso2, lightMode }) {
  const [geo,     setGeo]     = useState(null)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState(null)

  useEffect(() => {
    if (!iso2) { setGeo(null); setError(null); return }
    setLoading(true)
    setError(null)
    fetchDistricts(iso2)
      .then((data) => { setGeo(data); setLoading(false) })
      .catch((err) => {
        setError('Could not load district boundaries: ' + err.message)
        setLoading(false)
      })
  }, [iso2])

  if (!geo) return null

  const style = {
    ...DISTRICT_STYLE,
    color: lightMode ? '#534AB7' : '#7F77DD',
  }

  return (
    <GeoJSON
      key={'districts-' + iso2}
      data={geo}
      style={() => style}
    />
  )
}

// Control panel for the district toggle (rendered outside MapContainer)
export function DistrictControl({ iso2, lightMode }) {
  const [distOn, setDistOn] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error,   setError]  = useState(null)
  const [geo,     setGeo]    = useState(null)

  useEffect(() => {
    if (!distOn || !iso2) return
    if (geoCache[iso2]) { setGeo(geoCache[iso2]); return }
    setLoading(true)
    setError(null)
    fetchDistricts(iso2)
      .then((data) => { setGeo(data); setLoading(false) })
      .catch((err) => {
        setError('Load failed')
        setLoading(false)
      })
  }, [distOn, iso2])

  useEffect(() => {
    if (!iso2) { setDistOn(false); setGeo(null) }
  }, [iso2])

  return { distOn, setDistOn, geo, loading, error }
}
"""

# =============================================================================
# backend/eonet_api/alerts.py -- email subscription + sending
# =============================================================================
FILES["backend/eonet_api/alerts.py"] = """\"\"\"
alerts.py
---------
Email alert subscription management for NET-EA.

Endpoints:
  POST   /alerts/subscribe          -- create or update a subscription
  DELETE /alerts/unsubscribe/{email} -- remove a subscription
  GET    /alerts/subscriptions       -- list all subscriptions (admin)

Email sending is triggered from main.py on each EONET refresh
when new events are detected that match a subscriber's filters.

Configure via environment variables:
  SMTP_HOST  (default: smtp.gmail.com)
  SMTP_PORT  (default: 587)
  SMTP_USER  -- your Gmail / SMTP username
  SMTP_PASS  -- app password (not your account password)
  SMTP_FROM  -- sender address shown in emails

Gmail setup:
  1. Enable 2-factor authentication
  2. Create an App Password at myaccount.google.com/apppasswords
  3. Set SMTP_USER=you@gmail.com SMTP_PASS=<app_password>
\"\"\"

from __future__ import annotations

import json
import logging
import os
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

log = logging.getLogger("alerts")
router = APIRouter(prefix="/alerts", tags=["alerts"])

# -- Storage ------------------------------------------------------------------
SUBS_FILE = Path(__file__).parents[2] / "data" / "subscriptions.json"

def load_subs() -> list[dict]:
    if not SUBS_FILE.exists():
        return []
    try:
        return json.loads(SUBS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

def save_subs(subs: list[dict]) -> None:
    SUBS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SUBS_FILE.write_text(json.dumps(subs, indent=2), encoding="utf-8")

# -- Models -------------------------------------------------------------------
class SubscriptionIn(BaseModel):
    email:      str
    categories: list[str] = []
    countries:  list[str] = []   # ISO2 codes; empty = all countries

# -- Endpoints ----------------------------------------------------------------
@router.post("/subscribe")
def subscribe(sub: SubscriptionIn):
    if "@" not in sub.email:
        raise HTTPException(400, "Invalid email address")
    subs = [s for s in load_subs() if s["email"] != sub.email]
    subs.append({
        "email":      sub.email,
        "categories": sub.categories,
        "countries":  sub.countries,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    save_subs(subs)
    log.info("Subscribed: %s  categories=%s  countries=%s",
             sub.email, sub.categories, sub.countries)
    return {"message": "Subscribed successfully", "email": sub.email}


@router.delete("/unsubscribe/{email}")
def unsubscribe(email: str):
    subs = [s for s in load_subs() if s["email"] != email]
    save_subs(subs)
    log.info("Unsubscribed: %s", email)
    return {"message": "Unsubscribed", "email": email}


@router.get("/subscriptions")
def list_subscriptions():
    return load_subs()


# -- Email sending ------------------------------------------------------------
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@net-ea.org")

COUNTRY_NAMES = {
    "DJ":"Djibouti", "ER":"Eritrea",     "ET":"Ethiopia",
    "KE":"Kenya",    "RW":"Rwanda",      "SO":"Somalia",
    "SS":"South Sudan","SD":"Sudan",     "TZ":"Tanzania",
    "UG":"Uganda",   "BI":"Burundi",
}

COUNTRY_BBOX = {
    "SD":{"minLat":9,"maxLat":22,"minLon":21,"maxLon":38},
    "SS":{"minLat":3,"maxLat":12,"minLon":24,"maxLon":36},
    "ET":{"minLat":3,"maxLat":15,"minLon":33,"maxLon":48},
    "ER":{"minLat":12,"maxLat":18,"minLon":36,"maxLon":44},
    "DJ":{"minLat":10,"maxLat":13,"minLon":41,"maxLon":44},
    "SO":{"minLat":-2,"maxLat":12,"minLon":40,"maxLon":52},
    "KE":{"minLat":-5,"maxLat":5,"minLon":33,"maxLon":42},
    "UG":{"minLat":-2,"maxLat":4,"minLon":29,"maxLon":35},
    "TZ":{"minLat":-12,"maxLat":0,"minLon":29,"maxLon":41},
    "RW":{"minLat":-3,"maxLat":0,"minLon":28,"maxLon":31},
    "BI":{"minLat":-5,"maxLat":-2,"minLon":28,"maxLon":31},
}


def _event_country(ev) -> Optional[str]:
    coords = ev.primary_coords
    if not coords:
        return None
    lon, lat = coords[0], coords[1]
    for iso, b in COUNTRY_BBOX.items():
        if b["minLon"] <= lon <= b["maxLon"] and b["minLat"] <= lat <= b["maxLat"]:
            return iso
    return None


def _event_matches(ev, sub: dict) -> bool:
    # Returns True if a new event should alert this subscriber.
    if sub.get("categories") and ev.primary_category not in sub["categories"]:
        return False
    if sub.get("countries"):
        country = _event_country(ev)
        if country not in sub["countries"]:
            return False
    return True


def _build_email(new_events: list, subscriber: dict) -> str:
    # Build a plain-text email body.
    lines = [
        "NET-EA -- Natural Event Tracker for East Africa",
        "",
        f"New events detected ({len(new_events)}):",
        "",
    ]
    for ev in new_events[:10]:
        country = COUNTRY_NAMES.get(_event_country(ev) or "", "")
        date    = (getattr(ev, "latest_date", "") or "")[:10]
        lines.append(f"  - [{ev.primary_category}] {ev.title}")
        if country:
            lines.append(f"    Country: {country}")
        if date:
            lines.append(f"    Date: {date}")
        if ev.link:
            lines.append(f"    Link: {ev.link}")
        lines.append("")

    lines += [
        "---",
        "You are receiving this because you subscribed at NET-EA.",
        "To unsubscribe, visit the Alerts section of the dashboard.",
    ]
    return "\n".join(lines)


def send_alerts(new_events: list) -> None:
    # Called from main.py after each EONET refresh.
    # Sends emails to subscribers whose filters match.
    # Silently skips if SMTP is not configured.
    if not SMTP_USER or not SMTP_PASS:
        log.debug("SMTP not configured -- skipping alert emails")
        return

    subs = load_subs()
    if not subs:
        return

    for sub in subs:
        matched = [ev for ev in new_events if _event_matches(ev, sub)]
        if not matched:
            continue

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"NET-EA: {len(matched)} new event{'s' if len(matched) > 1 else ''} detected"
        msg["From"]    = SMTP_FROM
        msg["To"]      = sub["email"]

        body = _build_email(matched, sub)
        msg.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                server.ehlo()
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(SMTP_FROM, [sub["email"]], msg.as_string())
            log.info("Alert sent to %s (%d events)", sub["email"], len(matched))
        except Exception as exc:
            log.warning("Failed to send alert to %s: %s", sub["email"], exc)
"""

# =============================================================================
# backend/main.py -- updated to include alerts router + send alerts on refresh
# =============================================================================
FILES["backend/main.py"] = """\"\"\"
main.py
FastAPI application entry point for NET-EA backend.

Run:
    uvicorn backend.main:app --reload --port 8000
\"\"\"
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.eonet_client import eonet
from backend.eonet_api.events import router as events_router, status_router
from backend.eonet_api.alerts import router as alerts_router, send_alerts

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("main")

scheduler = AsyncIOScheduler()


async def _refresh_cache():
    log.info("Scheduled refresh starting...")
    prev_ids = {e.id for e in (eonet._cache.events if eonet._cache else [])}
    await eonet.get_ea_events(force_refresh=True)
    info = eonet.get_cache_info()
    log.info("Refreshed -- %d events, %d new", info["event_count"], info["new_since_last"])

    # Send email alerts for new events
    if eonet._cache and info["new_since_last"] > 0:
        new_events = [e for e in eonet._cache.events if e.id not in prev_ids]
        if new_events:
            send_alerts(new_events)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting NET-EA backend -- bbox: %s", settings.bbox_str)
    try:
        await eonet.get_ea_events(force_refresh=True)
        log.info("Cache warmed -- %d events", eonet.get_cache_info()["event_count"])
    except Exception as exc:
        log.error("Initial fetch failed: %s", exc)

    scheduler.add_job(_refresh_cache, "interval", seconds=settings.REFRESH_INTERVAL,
                      id="eonet_refresh", max_instances=1, misfire_grace_time=60)
    scheduler.start()
    log.info("Scheduler started -- refresh every %ds", settings.REFRESH_INTERVAL)
    yield
    scheduler.shutdown(wait=False)
    log.info("Scheduler stopped.")


app = FastAPI(
    title="NET-EA Dashboard API",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS,
                   allow_methods=["GET", "POST", "DELETE"], allow_headers=["*"])

app.include_router(events_router)
app.include_router(status_router)
app.include_router(alerts_router)


@app.get("/", tags=["meta"])
async def root():
    return {"service": "NET-EA Dashboard API", "version": "3.0.0",
            "docs": "/docs", "bbox": settings.bbox_str,
            "cache": eonet.get_cache_info()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.BACKEND_HOST,
                port=settings.BACKEND_PORT, reload=True)
"""

# =============================================================================
# .env.example -- add SMTP variables
# =============================================================================
ENV_SMTP_APPEND = """
# -- Email alerts (optional) -----------------------------------------------
# Required only for email alert subscriptions feature.
# Gmail: enable 2FA then create an App Password at myaccount.google.com/apppasswords
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password_here
SMTP_FROM=noreply@net-ea.org
"""

# =============================================================================
# FilterSidebar.jsx -- add SavedFilters section (patch)
# =============================================================================
SIDEBAR_SAVED_IMPORT = "import SavedFilters from './SavedFilters.jsx'\n"
SIDEBAR_INSERT_MARKER = "        <Section label=\"Data source\">"
SIDEBAR_SAVED_SECTION = """        <SavedFilters />

"""

# =============================================================================
# App.jsx -- add OfflineBanner (patch)
# =============================================================================
APP_OFFLINE_IMPORT = "import OfflineBanner from './components/OfflineBanner.jsx'\n"
APP_OFFLINE_USAGE  = "      <OfflineBanner />\n"
APP_TOAST_MARKER   = "      <ToastContainer />\n"

# =============================================================================
# AboutPanel.jsx -- add AlertSubscription section (patch)
# =============================================================================
ABOUT_ALERT_IMPORT  = "import AlertSubscription from './AlertSubscription.jsx'\n"
ABOUT_ALERT_SECTION = """      {/* Email alert subscriptions */}
      <Section title="Email alert subscriptions">
        <Para>
          Subscribe to receive email notifications when new events matching your
          selected categories and countries are detected during the 15-minute
          automatic refresh. Requires the FastAPI backend to be running with
          SMTP configured.
        </Para>
        <AlertSubscription />
      </Section>

"""
ABOUT_DISCLAIMER_MARKER = "      {/* Disclaimer */}"

# =============================================================================
# Builder
# =============================================================================
def build(root: Path):
    fe = root / "frontend"
    be = root / "backend"
    hdr(f"Adding Tier 3 features to NET-EA in: {root}")
    created = updated = 0

    # 1. Full file writes
    for rel, content in FILES.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        existed = target.exists()
        target.write_text(content, encoding="utf-8")
        (ow if existed else ok)(("update  " if existed else "create  ") + rel)
        if existed: updated += 1
        else: created += 1

    # 2. Create data directory for subscriptions
    data_dir = root / "data"
    data_dir.mkdir(exist_ok=True)
    subs_file = data_dir / "subscriptions.json"
    if not subs_file.exists():
        subs_file.write_text("[]", encoding="utf-8")
        ok("create  data/subscriptions.json")
        created += 1

    # 3. Patch .env.example with SMTP vars
    env_path = root / ".env.example"
    if env_path.exists():
        env_txt = env_path.read_text(encoding="utf-8")
        if "SMTP_HOST" not in env_txt:
            env_path.write_text(env_txt.rstrip() + "\n" + ENV_SMTP_APPEND, encoding="utf-8")
            ow("patch   .env.example (SMTP variables)")
            updated += 1

    # 4. Patch FilterSidebar -- add SavedFilters
    sb_path = fe / "src/components/FilterSidebar.jsx"
    if sb_path.exists():
        sb_txt = sb_path.read_text(encoding="utf-8")
        changed = False
        if "SavedFilters" not in sb_txt:
            # Add import after last import line
            lines = sb_txt.split("\n")
            last_import = max((i for i, l in enumerate(lines) if l.startswith("import ")), default=0)
            lines.insert(last_import + 1, SIDEBAR_SAVED_IMPORT.strip())
            sb_txt = "\n".join(lines)
            changed = True
        if SIDEBAR_INSERT_MARKER in sb_txt and "<SavedFilters" not in sb_txt:
            sb_txt = sb_txt.replace(
                SIDEBAR_INSERT_MARKER,
                SIDEBAR_SAVED_SECTION + SIDEBAR_INSERT_MARKER
            )
            changed = True
        if changed:
            sb_path.write_text(sb_txt, encoding="utf-8")
            ow("patch   frontend/src/components/FilterSidebar.jsx (SavedFilters)")
            updated += 1

    # 5. Patch App.jsx -- add OfflineBanner
    app_path = fe / "src/App.jsx"
    if app_path.exists():
        app_txt = app_path.read_text(encoding="utf-8")
        changed = False
        if "OfflineBanner" not in app_txt:
            lines = app_txt.split("\n")
            last_import = max((i for i, l in enumerate(lines) if l.startswith("import ")), default=0)
            lines.insert(last_import + 1, APP_OFFLINE_IMPORT.strip())
            app_txt = "\n".join(lines)
            changed = True
        if APP_TOAST_MARKER in app_txt and "OfflineBanner" not in app_txt.split("return")[1]:
            app_txt = app_txt.replace(APP_TOAST_MARKER,
                                      APP_TOAST_MARKER + APP_OFFLINE_USAGE)
            changed = True
        if changed:
            app_path.write_text(app_txt, encoding="utf-8")
            ow("patch   frontend/src/App.jsx (OfflineBanner)")
            updated += 1

    # 6. Patch AboutPanel -- add AlertSubscription
    about_path = fe / "src/components/AboutPanel.jsx"
    if about_path.exists():
        about_txt = about_path.read_text(encoding="utf-8")
        changed = False
        if "AlertSubscription" not in about_txt:
            lines = about_txt.split("\n")
            last_import = max((i for i, l in enumerate(lines) if l.startswith("import ")), default=0)
            lines.insert(last_import + 1, ABOUT_ALERT_IMPORT.strip())
            about_txt = "\n".join(lines)
            changed = True
        if ABOUT_DISCLAIMER_MARKER in about_txt and "<AlertSubscription" not in about_txt:
            about_txt = about_txt.replace(
                ABOUT_DISCLAIMER_MARKER,
                ABOUT_ALERT_SECTION + ABOUT_DISCLAIMER_MARKER
            )
            changed = True
        if changed:
            about_path.write_text(about_txt, encoding="utf-8")
            ow("patch   frontend/src/components/AboutPanel.jsx (AlertSubscription)")
            updated += 1

    # 7. Patch MapPanel to use DistrictLayer
    mp_path = fe / "src/components/MapPanel.jsx"
    if mp_path.exists():
        mp_txt = mp_path.read_text(encoding="utf-8")
        if "DistrictLayer" not in mp_txt:
            # Add import
            lines = mp_txt.split("\n")
            last_import = max((i for i, l in enumerate(lines) if l.startswith("import ")), default=0)
            lines.insert(last_import + 1,
                "import { DistrictLayer } from './DistrictLayer.jsx'")
            mp_txt = "\n".join(lines)

            # Add distOn state near other useState declarations
            mp_txt = mp_txt.replace(
                "  const [satOn,    setSatOn]    = useState(false)",
                "  const [satOn,    setSatOn]    = useState(false)\n"
                "  const [distOn,   setDistOn]   = useState(false)"
            )

            # Add district toggle button next to satellite button
            mp_txt = mp_txt.replace(
                "        <SatelliteControl satOn={satOn} setSatOn={setSatOn}",
                "        <button\n"
                "          onClick={() => setDistOn((v) => !v)}\n"
                "          title={selectedCountry ? 'Toggle district boundaries' : 'Select a country first'}\n"
                "          style={{\n"
                "            fontSize:11, padding:'4px 10px', borderRadius:6,\n"
                "            border:'1px solid',\n"
                "            borderColor: distOn ? '#7F77DD' : 'var(--border-primary)',\n"
                "            background: distOn ? 'rgba(127,119,221,0.15)' : 'rgba(255,255,255,0.92)',\n"
                "            color: distOn ? '#534AB7' : 'var(--text-secondary)',\n"
                "            cursor: selectedCountry ? 'pointer' : 'not-allowed',\n"
                "            opacity: selectedCountry ? 1 : 0.5,\n"
                "            fontWeight: distOn ? 600 : 400,\n"
                "            boxShadow:'0 1px 4px rgba(0,0,0,0.12)',\n"
                "          }}>\n"
                "          Districts\n"
                "        </button>\n"
                "        <SatelliteControl satOn={satOn} setSatOn={setSatOn}"
            )

            # Add DistrictLayer inside MapContainer (after CountriesLayer)
            mp_txt = mp_txt.replace(
                "        <FitRegion />",
                "        {distOn && selectedCountry && (\n"
                "          <DistrictLayer iso2={selectedCountry} lightMode={lightMode} />\n"
                "        )}\n"
                "        <FitRegion />"
            )

            mp_path.write_text(mp_txt, encoding="utf-8")
            ow("patch   frontend/src/components/MapPanel.jsx (DistrictLayer + Districts button)")
            updated += 1

    # 8. ASCII check
    print()
    bad = []
    for f in list((fe / "src").rglob("*.jsx")) + list((fe / "src").rglob("*.js")):
        raw = f.read_bytes()
        for i, line in enumerate(raw.split(b"\n"), 1):
            if any(b > 127 for b in line):
                bad.append(f"  {f.name}:{i}")
    if bad:
        print("  WARN  Non-ASCII found (OXC will reject):")
        for b in bad[:10]: print(b)
    else:
        ok("ASCII-clean -- OXC safe")

    hdr("Done")
    print(f"  Files created : {created}")
    print(f"  Files updated : {updated}")
    print()
    print("  4 Tier 3 features implemented:")
    print()
    print("  [1] PWA + offline mode")
    print("      vite.config.js: VitePWA with NetworkFirst for EONET API calls")
    print("      Caches last EONET response -- viewable offline for 24h")
    print("      Map tiles cached for 7 days (CartoDB + GIBS)")
    print("      OfflineBanner shows amber bar when network lost")
    print("      'Install' button appears in browser address bar after build")
    print()
    print("  [2] Email alert subscriptions")
    print("      About tab: email + category + country subscription form")
    print("      Backend: POST /alerts/subscribe, DELETE /alerts/unsubscribe/{email}")
    print("      Subscriptions stored in data/subscriptions.json")
    print("      Emails sent via SMTP on each refresh when new events detected")
    print("      Configure: add SMTP_HOST/PORT/USER/PASS to .env")
    print()
    print("  [3] District-level boundaries")
    print("      'Districts' button in map controls (requires country selected)")
    print("      Fetches GADM Level-1 boundaries from geodata.ucdavis.edu")
    print("      Renders as thin dashed purple lines within selected country")
    print("      In-memory cache -- only fetches once per country per session")
    print()
    print("  [4] Saved filter presets")
    print("      Sidebar: save current filters with a custom name")
    print("      3 default presets pre-loaded (active events, wildfires+floods, seismic)")
    print("      Click any preset to instantly apply it")
    print("      Stored in localStorage -- persists across browser sessions")
    print()
    print("  IMPORTANT -- run npm install for vite-plugin-pwa:")
    print("    cd frontend")
    print("    npm install")
    print("    npm run dev")
    print()
    print("  PWA only activates in production build:")
    print("    npm run build && npm run preview")
    print("    (Service worker does not run in dev mode)")
    print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Add Tier 3 features to NET-EA")
    parser.add_argument("--path", default=".", help="Project root (default: current dir)")
    args = parser.parse_args()
    root = Path(args.path).resolve()
    if not (root / "backend").exists():
        print(f"WARNING: {root} may not be project root. Continue? [y/N] ", end="")
        if input().strip().lower() != "y":
            sys.exit(0)
    build(root)

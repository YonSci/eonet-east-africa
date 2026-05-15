import React, { useState, useEffect, useCallback } from 'react'
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

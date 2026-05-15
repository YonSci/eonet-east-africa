import { create } from 'zustand'

export const CATEGORIES = {
  wildfires:           { label: 'Wildfires',           color: '#E8593C' },
  severeStorms:        { label: 'Severe Storms',        color: '#378ADD' },
  floods:              { label: 'Floods',               color: '#1D9E75' },
  drought:             { label: 'Drought',              color: '#BA7517' },
  volcanoes:           { label: 'Volcanoes',            color: '#E24B4A' },
  dustHaze:            { label: 'Dust and Haze',        color: '#888780' },
  earthquakes:         { label: 'Earthquakes',          color: '#7F77DD' },
  landslides:          { label: 'Landslides',           color: '#639922' },
  temperatureExtremes: { label: 'Temperature Extremes', color: '#E85D24' },
  waterColor:          { label: 'Water Color',          color: '#1D6FA5' },
}

export const ALL_CATS = Object.keys(CATEGORIES)

// -- URL read / write helpers --
export function readURLFilters() {
  const p = new URLSearchParams(window.location.search)
  return {
    days:      p.has('days')   ? parseInt(p.get('days'), 10) || 90 : null,
    status:    p.has('status') ? p.get('status') : null,
    cats:      p.has('cats')   ? p.get('cats').split(',').filter((c) => ALL_CATS.includes(c)) : null,
    dateMode:  p.has('mode')   ? p.get('mode') : null,
    startDate: p.has('start')  ? p.get('start') : null,
    endDate:   p.has('end')    ? p.get('end') : null,
  }
}

export function writeURLFilters(state) {
  const p = new URLSearchParams()
  if (state.dateMode === 'range') {
    p.set('mode', 'range')
    if (state.startDate) p.set('start', state.startDate)
    if (state.endDate)   p.set('end',   state.endDate)
  } else {
    if (state.lookbackDays !== 90) p.set('days', String(state.lookbackDays))
  }
  if (state.activeStatus !== 'all') p.set('status', state.activeStatus)
  const catStr = state.activeCategories.join(',')
  if (catStr !== ALL_CATS.join(',')) p.set('cats', catStr)
  const str = p.toString()
  window.history.replaceState({}, '', str ? '?' + str : window.location.pathname)
}

let toastSeq = 0

const useAppStore = create((set) => ({
  activeCategories: ALL_CATS,
  activeStatus:     'all',
  lookbackDays:     90,
  dateMode:         'lookback',   // 'lookback' | 'range'
  startDate:        '',
  endDate:          '',
  selectedEventId:  null,
  lightMode:        true,
  sidebarOpen:      true,
  toasts:           [],

  toggleCategory:   (cat) => set((s) => ({
    activeCategories: s.activeCategories.includes(cat)
      ? s.activeCategories.filter((c) => c !== cat)
      : [...s.activeCategories, cat],
  })),
  setAllCategories: (cats) => set({ activeCategories: cats }),
  setStatus:        (v)    => set({ activeStatus: v }),
  setDays:          (v)    => set({ lookbackDays: v }),
  setDateMode:      (v)    => set({ dateMode: v }),
  setStartDate:     (v)    => set({ startDate: v }),
  setEndDate:       (v)    => set({ endDate: v }),
  selectEvent:      (id)   => set({ selectedEventId: id }),
  toggleLight: () => set((s) => {
    const next = !s.lightMode
    document.documentElement.classList.toggle('light', next)
    return { lightMode: next }
  }),
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),

  addToast: (msg, type) => set((s) => ({
    toasts: [
      ...s.toasts,
      { id: String(++toastSeq), msg, type: type || 'info', ts: Date.now() },
    ],
  })),
  removeToast: (id) => set((s) => ({
    toasts: s.toasts.filter((t) => t.id !== id),
  })),
}))

if (typeof document !== 'undefined') {
  document.documentElement.classList.add('light')
}

export default useAppStore

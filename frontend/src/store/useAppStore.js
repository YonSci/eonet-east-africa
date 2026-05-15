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

const useAppStore = create((set) => ({
  activeCategories: ALL_CATS,
  activeStatus:     'all',
  lookbackDays:     90,
  selectedEventId:  null,
  lightMode:        true,
  sidebarOpen:      true,

  toggleCategory:   (cat)  => set((s) => ({
    activeCategories: s.activeCategories.includes(cat)
      ? s.activeCategories.filter((c) => c !== cat)
      : [...s.activeCategories, cat],
  })),
  setAllCategories: (cats) => set({ activeCategories: cats }),
  setStatus:        (v)    => set({ activeStatus: v }),
  setDays:          (v)    => set({ lookbackDays: v }),
  selectEvent:      (id)   => set({ selectedEventId: id }),
  toggleLight: () => set((s) => {
    const next = !s.lightMode
    document.documentElement.classList.toggle('light', next)
    return { lightMode: next }
  }),
  toggleSidebar:  () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
}))

if (typeof document !== 'undefined') {
  document.documentElement.classList.add('light')
}

export default useAppStore

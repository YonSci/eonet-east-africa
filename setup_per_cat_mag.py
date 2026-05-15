"""
setup_per_cat_mag.py
--------------------
Two changes:

  1. Replace single magnitude slider with one slider per active
     magnitude-capable category. Each slider has its own unit,
     range, and description. Filters are independent per category.

  2. Remove ICPAC from all visible text (internal variable names like
     ICPAC_CENTER are fine -- only displayed strings are removed).

Run from the eonet-east-africa project root:
    python setup_per_cat_mag.py
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

# =============================================================================
# Magnitude metadata per category
# =============================================================================
MAG_META = {
    "earthquakes":         {"label": "Richter",      "unit": "M",    "max": 9,   "step": 0.5, "dec": 1,
                            "desc": "Below M3.0 minor, M4.5+ widely felt, M6.0+ damaging"},
    "severeStorms":        {"label": "Wind (knots)",  "unit": "kts",  "max": 200, "step": 5,   "dec": 0,
                            "desc": "Tropical storm: 34-64 kts. Cat 1: 64 kts. Cat 5: 137+ kts"},
    "floods":              {"label": "Depth (metres)","unit": "m",    "max": 10,  "step": 0.5, "dec": 1,
                            "desc": "Reported water depth in metres above normal level"},
    "temperatureExtremes": {"label": "Temperature",  "unit": "C",    "max": 50,  "step": 1,   "dec": 0,
                            "desc": "Recorded temperature in Celsius"},
}

# =============================================================================
# 1.  useAppStore.js  -- replace single magFilter with magFilters object
# =============================================================================

OLD_STORE_MAG = """  magFilter:        0,      // minimum magnitude value (0 = show all)"""

NEW_STORE_MAG = """  // Per-category magnitude minimum filters (0 = show all)
  magFilters: {
    earthquakes:         0,
    severeStorms:        0,
    floods:              0,
    temperatureExtremes: 0,
  },"""

OLD_STORE_SET_MAG = """  setMagFilter:     (v)    => set({ magFilter: v }),"""

NEW_STORE_SET_MAG = """  setMagFilter: (cat, v) => set((s) => ({
    magFilters: { ...s.magFilters, [cat]: v },
  })),
  clearMagFilters: () => set({ magFilters: {
    earthquakes: 0, severeStorms: 0, floods: 0, temperatureExtremes: 0,
  }}),"""

# =============================================================================
# 2.  FilterSidebar.jsx  -- one slider per active mag category
# =============================================================================

# Replace the full magnitude derived-values block
OLD_MAG_DERIVED = """  // Magnitude slider -- only show when magnitude-capable cats are active
  const hasMagCat = activeCategories.some((c) => MAG_CATS.includes(c))

  // Only use MAG_CATS events for the slider range (excludes wildfire FRP in MW
  // which can reach 10000+ and makes the slider useless for other categories)
  const magEvents = rawEvents.filter(
    (ev) => ev.magnitude != null && MAG_CATS.includes(ev.category)
  )

  // Per-category magnitude metadata
  const activeMagCats = activeCategories.filter((c) => MAG_CATS.includes(c))
  const magMeta = useMemo(() => {
    const onlyEq   = activeMagCats.every((c) => c === 'earthquakes')
    const onlySt   = activeMagCats.every((c) => c === 'severeStorms')
    const onlyFl   = activeMagCats.every((c) => c === 'floods')
    const onlyTmp  = activeMagCats.every((c) => c === 'temperatureExtremes')
    if (onlyEq)  return { label:'Richter', max:9,   step:0.5, dec:1,
      desc:'Filters earthquakes by Richter magnitude. Below M3.0 are minor; M4.5+ are felt widely.' }
    if (onlySt)  return { label:'kts (knots)', max:200, step:5,   dec:0,
      desc:'Filters severe storms by maximum wind speed in knots. Tropical storms: 34-64 kts. Hurricanes: 64+ kts.' }
    if (onlyFl)  return { label:'m (meters)', max:10,  step:0.5, dec:1,
      desc:'Filters floods by reported water depth in meters.' }
    if (onlyTmp) return { label:'deg C', max:50,  step:1,   dec:0,
      desc:'Filters temperature extreme events by recorded temperature in Celsius.' }
    return { label:'mixed units', max:100, step:1, dec:1,
      desc:'Multiple magnitude types active (Richter / kts / m / C). Use category filters to isolate one type for precise magnitude filtering.' }
  }, [activeMagCats])

  const magSliderMax  = useMemo(() => {
    if (!magEvents.length) return magMeta.max
    const dataMax = Math.ceil(Math.max(...magEvents.map((e) => e.magnitude.value || 0)))
    return Math.max(dataMax, magMeta.max)
  }, [magEvents, magMeta])

  const magUnitLabel  = magMeta.label
  const magStep       = magMeta.step
  const magDecimals   = magMeta.dec
  const magUnitDesc   = magFilter > 0
    ? 'Hiding events below ' + magFilter.toFixed(magMeta.dec) + ' ' + magMeta.label +
      '. Events without magnitude are always shown.'
    : magMeta.desc"""

NEW_MAG_DERIVED = """  // Per-category magnitude sliders
  const hasMagCat     = activeCategories.some((c) => MAG_CATS.includes(c))
  const activeMagCats = activeCategories.filter((c) => MAG_CATS.includes(c))

  // Max magnitude per category derived from fetched events (excludes wildfire FRP)
  const catMaxMag = useMemo(() => {
    const result = {}
    ;(rawEvents || []).filter((ev) => ev.magnitude != null && MAG_CATS.includes(ev.category))
      .forEach((ev) => {
        const v = ev.magnitude.value || 0
        if (!result[ev.category] || v > result[ev.category]) result[ev.category] = v
      })
    return result
  }, [rawEvents])"""

# Replace the magnitude Section in the JSX
OLD_MAG_SECTION = """        {/* -- Magnitude filter (only when relevant categories active) -- */}
        {hasMagCat && (
          <Section label={'Minimum magnitude -- ' + magUnitLabel}>
            <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:6 }}>
              <input type="range" min="0" max={magSliderMax} step={magStep}
                value={magFilter}
                onChange={(e) => setMagFilter(parseFloat(e.target.value))}
                style={{ flex:1, accentColor:'#7F77DD' }} />
              <span style={{ fontSize:13, fontWeight:600,
                             minWidth:42, textAlign:'right', color:'#7F77DD' }}>
                {magFilter > 0 ? magFilter.toFixed(magDecimals) : 'off'}
              </span>
            </div>
            <div style={{ fontSize:11, color:'var(--text-muted)', lineHeight:1.5 }}>
              {magUnitDesc}
            </div>
            {magFilter > 0 && (
              <button onClick={() => setMagFilter(0)}
                style={{ marginTop:6, fontSize:11, padding:'3px 8px', borderRadius:4,
                         border:'1px solid var(--border-primary)', background:'transparent',
                         color:'var(--text-secondary)', cursor:'pointer' }}>
                Clear
              </button>
            )}
          </Section>
        )}"""

NEW_MAG_SECTION = """        {/* -- Per-category magnitude filters -- */}
        {hasMagCat && activeMagCats.map((cat) => {
          const META = {
            earthquakes:         { label:'Richter',       unit:'M',   max:9,   step:0.5, dec:1,
              desc:'M3.0 minor, M4.5+ widely felt, M6.0+ damaging' },
            severeStorms:        { label:'Wind speed',     unit:'kts', max:200, step:5,   dec:0,
              desc:'Storm: 34-64 kts. Cat 1: 64 kts. Cat 5: 137+ kts' },
            floods:              { label:'Water depth',    unit:'m',   max:10,  step:0.5, dec:1,
              desc:'Reported water depth above normal level (metres)' },
            temperatureExtremes: { label:'Temperature',   unit:'C',   max:50,  step:1,   dec:0,
              desc:'Recorded temperature in degrees Celsius' },
          }
          const meta    = META[cat] || { label:cat, unit:'', max:100, step:1, dec:1, desc:'' }
          const dataMax = catMaxMag[cat] ? Math.ceil(catMaxMag[cat]) : 0
          const sliderMax = Math.max(dataMax, meta.max)
          const val     = magFilters[cat] || 0
          const catColor = (CATEGORIES[cat] || {}).color || '#7F77DD'
          return (
            <div key={cat} style={{ marginBottom:16 }}>
              <div style={{ display:'flex', alignItems:'center', gap:6, marginBottom:5 }}>
                <span style={{ width:8, height:8, borderRadius:'50%',
                               background:catColor, flexShrink:0 }} />
                <span style={{ fontSize:11, fontWeight:600,
                               color:'var(--text-secondary)', flex:1 }}>
                  {(CATEGORIES[cat] || {}).label || cat}
                </span>
                <span style={{ fontSize:10, color:'var(--text-muted)' }}>
                  {meta.label}
                </span>
              </div>
              <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:4 }}>
                <input
                  type="range"
                  min="0"
                  max={sliderMax}
                  step={meta.step}
                  value={val}
                  onChange={(e) => setMagFilter(cat, parseFloat(e.target.value))}
                  style={{ flex:1, accentColor:catColor }}
                />
                <span style={{ fontSize:12, fontWeight:600, minWidth:44,
                               textAlign:'right', color:catColor,
                               fontFamily:'var(--font-mono, monospace)' }}>
                  {val > 0
                    ? (cat === 'earthquakes' ? 'M' : '') + val.toFixed(meta.dec) + (cat === 'earthquakes' ? '' : ' ' + meta.unit)
                    : 'off'}
                </span>
              </div>
              <div style={{ fontSize:10, color:'var(--text-muted)', lineHeight:1.5 }}>
                {val > 0
                  ? 'Hiding ' + (CATEGORIES[cat]||{}).label + ' below ' + val.toFixed(meta.dec) + ' ' + meta.unit + '. Events without magnitude always shown.'
                  : meta.desc}
              </div>
            </div>
          )
        })}
        {hasMagCat && Object.values(magFilters).some((v) => v > 0) && (
          <button
            onClick={clearMagFilters}
            style={{ fontSize:11, padding:'3px 10px', borderRadius:4, marginBottom:14,
                     border:'1px solid var(--border-primary)', background:'transparent',
                     color:'var(--text-secondary)', cursor:'pointer' }}>
            Clear all magnitude filters
          </button>
        )}"""

# Replace destructuring to include magFilters + clearMagFilters
OLD_SIDEBAR_DESTRUCTURE = """  const {
    activeCategories, toggleCategory, setAllCategories,
    activeStatus,     setStatus,
    lookbackDays,     setDays,
    dateMode,         setDateMode,
    startDate,        setStartDate,
    endDate,          setEndDate,
    selectedCountry,  setSelectedCountry,
    magFilter,        setMagFilter,
  } = useAppStore()"""

NEW_SIDEBAR_DESTRUCTURE = """  const {
    activeCategories, toggleCategory, setAllCategories,
    activeStatus,     setStatus,
    lookbackDays,     setDays,
    dateMode,         setDateMode,
    startDate,        setStartDate,
    endDate,          setEndDate,
    selectedCountry,  setSelectedCountry,
    magFilters,       setMagFilter,  clearMagFilters,
  } = useAppStore()"""

# =============================================================================
# 3.  MapPanel.jsx  -- use magFilters object for event filtering
# =============================================================================
OLD_MAP_MAG_FILTER = """    if (magFilter > 0 && ev.magnitude && ev.magnitude.value < magFilter) return false"""

NEW_MAP_MAG_FILTER = """    if (ev.magnitude && magFilters) {
      const minMag = magFilters[ev.category] || 0
      if (minMag > 0 && ev.magnitude.value < minMag) return false
    }"""

OLD_MAP_DESTRUCTURE = """  const {
    activeCategories, activeStatus, selectedEventId, selectEvent,
    lightMode, selectedCountry, setSelectedCountry, magFilter,
  } = useAppStore()"""

NEW_MAP_DESTRUCTURE = """  const {
    activeCategories, activeStatus, selectedEventId, selectEvent,
    lightMode, selectedCountry, setSelectedCountry, magFilters,
  } = useAppStore()"""

# =============================================================================
# 4.  ICPAC visible text removal from MapPanel (badge text only)
# =============================================================================
OLD_MAP_BADGE = "          Greater Horn of Africa"
NEW_MAP_BADGE = "          Greater Horn of Africa"   # already clean -- no ICPAC in badge

# =============================================================================
# Builder
# =============================================================================
def apply(path: Path, old: str, new: str, label: str) -> bool:
    if not path.exists():
        print(f"  SKIP  {label} (file not found)")
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
    hdr(f"Per-category magnitude sliders in: {root}")
    patched = 0

    # 1. useAppStore.js
    store = fe / "src/store/useAppStore.js"
    if apply(store, OLD_STORE_MAG,     NEW_STORE_MAG,     "useAppStore.js -- magFilters object"):
        patched += 1
    if apply(store, OLD_STORE_SET_MAG, NEW_STORE_SET_MAG, "useAppStore.js -- setMagFilter(cat,v)"):
        patched += 1

    # 2. FilterSidebar.jsx
    sb = fe / "src/components/FilterSidebar.jsx"
    if apply(sb, OLD_SIDEBAR_DESTRUCTURE, NEW_SIDEBAR_DESTRUCTURE,
             "FilterSidebar.jsx -- destructure magFilters"):
        patched += 1
    if apply(sb, OLD_MAG_DERIVED, NEW_MAG_DERIVED, "FilterSidebar.jsx -- derived values"):
        patched += 1
    if apply(sb, OLD_MAG_SECTION, NEW_MAG_SECTION, "FilterSidebar.jsx -- per-cat sliders"):
        patched += 1

    # 3. MapPanel.jsx
    mp = fe / "src/components/MapPanel.jsx"
    if apply(mp, OLD_MAP_DESTRUCTURE, NEW_MAP_DESTRUCTURE, "MapPanel.jsx -- destructure"):
        patched += 1
    if apply(mp, OLD_MAP_MAG_FILTER,  NEW_MAP_MAG_FILTER,  "MapPanel.jsx -- per-cat filter"):
        patched += 1

    # 4. Remove ICPAC from all visible text (not variable names)
    visible_icpac = [
        (fe/"src/components/MapPanel.jsx",
         "ICPAC Greater Horn of Africa", "Greater Horn of Africa"),
        (fe/"src/components/FilterSidebar.jsx",
         "ICPAC", ""),
    ]
    for path, old_txt, new_txt in visible_icpac:
        if path.exists():
            txt = path.read_text(encoding="utf-8")
            if old_txt in txt:
                path.write_text(txt.replace(old_txt, new_txt), encoding="utf-8")
                ow(f"patch   {path.name} -- remove visible ICPAC text")
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
        print("  WARN  Non-ASCII (OXC will reject):")
        for b in bad[:6]: print(b)
    else:
        ok("ASCII-clean -- OXC safe")

    # 6. Verification
    print()
    checks = [
        ("magFilters",       fe/"src/store/useAppStore.js",          "magFilters in store"),
        ("clearMagFilters",  fe/"src/store/useAppStore.js",          "clearMagFilters action"),
        ("magFilters[cat]",  fe/"src/components/FilterSidebar.jsx",  "per-cat slider in sidebar"),
        ("magFilters[cat]",  fe/"src/components/FilterSidebar.jsx",  "per-cat filter label"),
        ("magFilters[ev.category]", fe/"src/components/MapPanel.jsx","per-cat filter in map"),
        ("clearMagFilters",  fe/"src/components/FilterSidebar.jsx",  "clear all button"),
    ]
    all_ok = True
    for needle, path, label in checks:
        found = path.exists() and needle in path.read_text(errors="ignore")
        if not found: all_ok = False
        print(f"  {'OK' if found else 'MISSING'}  {label}")

    hdr("Done")
    print(f"  Patches applied: {patched}")
    print()
    print("  Per-category magnitude sliders:")
    print("    Each active mag-capable category now gets its own slider")
    print("    Earthquakes:  Richter scale  0 - 9    (step 0.5)")
    print("    Severe storms: Wind speed   0 - 200 kts (step 5)")
    print("    Floods:        Water depth  0 - 10 m   (step 0.5)")
    print("    Temperature:   Degrees C    0 - 50 C   (step 1)")
    print("    Each slider is colour-coded to its category")
    print("    'Clear all magnitude filters' button resets all sliders")
    print("    Filters are independent -- set M4.0+ earthquakes AND 60+ kts storms")
    print()
    print("  ICPAC visible text: removed from all displayed strings")
    print("  (Internal variable names ICPAC_CENTER/ICPAC_ISO2 kept -- not shown to users)")
    print()
    print("  Restart Vite:")
    print("    cd frontend && npm run dev")
    print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Per-category magnitude sliders")
    parser.add_argument("--path", default=".", help="Project root (default: current dir)")
    args   = parser.parse_args()
    root   = Path(args.path).resolve()
    if not (root / "backend").exists():
        print(f"WARNING: {root} may not be project root. Continue? [y/N] ", end="")
        if input().strip().lower() != "y":
            sys.exit(0)
    build(root)

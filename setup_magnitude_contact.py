"""
setup_magnitude_contact.py
--------------------------
Two targeted fixes:

  1. Magnitude display
     - Show unit-aware label on slider (Richter / kts / m / C)
     - Exclude wildfire FRP from slider max (FRP in MW is valid data
       but not a useful filter dimension -- fires go 0-10000+ MW)
     - Explain what each unit means in the sidebar tooltip
     - Show formatted magnitude with unit in popups and event list

  2. Developer contact card (AboutPanel.jsx)
     - Full name: Yonas Mersha
     - Title: Hydro-Climate Modelling and AI Expert
     - Organisation: International Livestock Research Institute (ILRI)
     - Email: Y.Mersha@cgiar.org

Run from the eonet-east-africa project root:
    python setup_magnitude_contact.py
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
# 1.  FilterSidebar.jsx -- magnitude section rewrite
# =============================================================================

# What to replace inside FilterSidebar
OLD_MAG_SECTION = """        {/* -- Magnitude filter (only when relevant) -- */}
        {hasMagCat && (
          <Section label="Minimum magnitude">
            <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:6 }}>
              <input type="range" min="0" max={maxMag} step="0.5"
                value={magFilter}
                onChange={(e) => setMagFilter(parseFloat(e.target.value))}
                style={{ flex:1, accentColor:'#7F77DD' }} />
              <span style={{ fontSize:13, fontWeight:600, minWidth:30,
                             textAlign:'right', color:'#7F77DD' }}>
                {magFilter > 0 ? magFilter.toFixed(1) : 'off'}
              </span>
            </div>
            <div style={{ fontSize:11, color:'var(--text-muted)', lineHeight:1.5 }}>
              {magFilter > 0
                ? 'Hiding events with magnitude below ' + magFilter.toFixed(1) + '. Events without magnitude data are always shown.'
                : 'Slide right to hide low-magnitude events. Applies to earthquakes, storms, and floods.'}
            </div>
            {magFilter > 0 && (
              <button onClick={() => setMagFilter(0)}
                style={{ marginTop:6, fontSize:11, padding:'3px 8px', borderRadius:4,
                         border:'1px solid var(--border-primary)', background:'transparent',
                         color:'var(--text-secondary)', cursor:'pointer' }}>
                Clear magnitude filter
              </button>
            )}
          </Section>
        )}"""

NEW_MAG_SECTION = """        {/* -- Magnitude filter (only when relevant categories active) -- */}
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

# What to replace in the useMemo / derived values block
OLD_MAG_DERIVED = """  // Magnitude slider -- only show when magnitude-capable cats are active
  const hasMagCat = activeCategories.some((c) => MAG_CATS.includes(c))
  const magEvents = rawEvents.filter((ev) => ev.magnitude != null)
  const maxMag    = useMemo(() => {
    if (!magEvents.length) return 10
    return Math.ceil(Math.max(...magEvents.map((e) => e.magnitude.value || 0)))
  }, [magEvents])"""

NEW_MAG_DERIVED = """  // Magnitude slider -- only show when magnitude-capable cats are active
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

# =============================================================================
# 2.  AboutPanel.jsx -- update developer card
# =============================================================================

OLD_DEV_CARD = """          <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)',
                        marginBottom: 2 }}>
            Yonas M.
          </div>
          <div style={{ fontSize: 12, color: '#1D9E75', fontWeight: 500,
                        marginBottom: 6 }}>
            Climate Modelling and AI Expert
          </div>"""

NEW_DEV_CARD = """          <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)',
                        marginBottom: 1 }}>
            Yonas Mersha
          </div>
          <div style={{ fontSize: 12, color: '#1D9E75', fontWeight: 500,
                        marginBottom: 3 }}>
            Hydro-Climate Modelling and AI Expert
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>
            International Livestock Research Institute (ILRI)
          </div>"""

OLD_FOOTER_CREDIT = "NET-EA v2.0 -- Yonas M. -- Y.Mersha@cgiar.org"
NEW_FOOTER_CREDIT = "NET-EA v3.0 -- Yonas Mersha -- Y.Mersha@cgiar.org -- ILRI"

OLD_INFO_ROW_BUILT = '"Built at"       value="East Africa Climate Services"'
NEW_INFO_ROW_BUILT = '"Built by"       value="Yonas Mersha, International Livestock Research Institute (ILRI)"\n          link="https://www.ilri.org"'

# =============================================================================
# 3.  MapPanel.jsx -- show magnitude unit in popup (already shows value+unit,
#     but add wildfire FRP explanation)
# =============================================================================

# In the popup: replace magnitude row to show unit context
OLD_POPUP_MAG = """                        {ev.magnitude && (
                          <PopupRow label="Magnitude"
                            value={ev.magnitude.value+' '+(ev.magnitude.unit||'')} />
                        )}"""

NEW_POPUP_MAG = """                        {ev.magnitude && (
                          <PopupRow label={magLabel(ev.category)}
                            value={formatMag(ev.magnitude.value, ev.magnitude.unit,
                                             ev.category)} />
                        )}"""

# Helper functions to add near the top of MapPanel (after imports)
MAP_HELPERS = """
// Magnitude label by category
function magLabel(cat) {
  const labels = {
    earthquakes:         'Magnitude',
    severeStorms:        'Wind speed',
    floods:              'Water depth',
    temperatureExtremes: 'Temperature',
    wildfires:           'Fire power (FRP)',
  }
  return labels[cat] || 'Magnitude'
}

// Format magnitude value with human-readable context
function formatMag(value, unit, cat) {
  if (value == null) return '--'
  const v = typeof value === 'number' ? value : parseFloat(value)
  if (cat === 'wildfires') {
    // FRP in MW -- wildfire intensity from MODIS/VIIRS satellite
    if (v >= 1000) return (v / 1000).toFixed(1) + ' GW FRP'
    return v.toFixed(0) + ' MW FRP'
  }
  if (cat === 'earthquakes') return 'M' + v.toFixed(1)
  if (cat === 'severeStorms' && (unit === 'kts' || !unit)) {
    if (v >= 137) return v.toFixed(0) + ' kts (Cat 5)'
    if (v >= 113) return v.toFixed(0) + ' kts (Cat 4)'
    if (v >= 96)  return v.toFixed(0) + ' kts (Cat 3)'
    if (v >= 83)  return v.toFixed(0) + ' kts (Cat 2)'
    if (v >= 64)  return v.toFixed(0) + ' kts (Cat 1)'
    if (v >= 34)  return v.toFixed(0) + ' kts (storm)'
    return v.toFixed(0) + ' kts'
  }
  if (cat === 'temperatureExtremes') return v.toFixed(1) + ' C'
  return v.toFixed(1) + (unit ? ' ' + unit : '')
}

"""

MAP_HELPERS_MARKER = "function todayStr()"

# =============================================================================
# Builder
# =============================================================================
def apply(path: Path, old: str, new: str, label: str) -> bool:
    if not path.exists():
        print(f"  SKIP  {label} (file not found)")
        return False
    txt = path.read_text(encoding="utf-8")
    if old not in txt:
        # Try showing where we are so the user can debug
        print(f"  SKIP  {label} (marker not found in {path.name})")
        return False
    path.write_text(txt.replace(old, new, 1), encoding="utf-8")
    ow(f"patch   {label}")
    return True


def build(root: Path):
    fe = root / "frontend"
    hdr(f"Fixing magnitude display + developer contact in: {root}")
    patched = 0

    # -- FilterSidebar --
    sb = fe / "src/components/FilterSidebar.jsx"
    if apply(sb, OLD_MAG_DERIVED, NEW_MAG_DERIVED, "FilterSidebar.jsx -- mag derived values"):
        patched += 1
    if apply(sb, OLD_MAG_SECTION, NEW_MAG_SECTION, "FilterSidebar.jsx -- mag slider UI"):
        patched += 1

    # -- AboutPanel --
    ap = fe / "src/components/AboutPanel.jsx"
    if apply(ap, OLD_DEV_CARD,        NEW_DEV_CARD,        "AboutPanel.jsx -- developer name/title"):
        patched += 1
    if apply(ap, OLD_FOOTER_CREDIT,   NEW_FOOTER_CREDIT,   "AboutPanel.jsx -- footer credit"):
        patched += 1
    if apply(ap, OLD_INFO_ROW_BUILT,  NEW_INFO_ROW_BUILT,  "AboutPanel.jsx -- built-by row"):
        patched += 1

    # -- MapPanel -- add helper functions + patch popup
    mp = fe / "src/components/MapPanel.jsx"
    if mp.exists():
        txt = mp.read_text(encoding="utf-8")
        changed = False
        if "function magLabel" not in txt and MAP_HELPERS_MARKER in txt:
            txt = txt.replace(MAP_HELPERS_MARKER, MAP_HELPERS + MAP_HELPERS_MARKER)
            changed = True
            ow("patch   MapPanel.jsx -- magLabel + formatMag helpers")
            patched += 1
        if OLD_POPUP_MAG in txt:
            txt = txt.replace(OLD_POPUP_MAG, NEW_POPUP_MAG)
            changed = True
            ow("patch   MapPanel.jsx -- popup magnitude display")
            patched += 1
        if changed:
            mp.write_text(txt, encoding="utf-8")

    # ASCII check
    print()
    bad = []
    for f in list((fe / "src").rglob("*.jsx")) + list((fe / "src").rglob("*.js")):
        raw = f.read_bytes()
        for i, line in enumerate(raw.split(b"\n"), 1):
            if any(b > 127 for b in line):
                bad.append(f"  {f.name}:{i}")
    if bad:
        print("  WARN  Non-ASCII (OXC will reject):")
        for b in bad[:6]: print(b)
    else:
        ok("ASCII-clean -- OXC safe")

    hdr("Done")
    print(f"  Patches applied: {patched}")
    print()
    print("  Magnitude fixes:")
    print("    Wildfire FRP (MW) excluded from slider max -- slider now shows")
    print("    realistic ranges: Richter 0-9, Storms 0-200 kts, Floods 0-10 m")
    print("    Slider label shows the unit: 'Minimum magnitude -- Richter'")
    print("    Slider description explains what the unit means")
    print("    Event popups now show:")
    print("      Earthquakes:  'M4.5'")
    print("      Storms:       '95 kts (Cat 2)'")
    print("      Wildfires:    '7.5 GW FRP'  (Fire Radiative Power, satellite-derived)")
    print("      Temperature:  '43.2 C'")
    print()
    print("  Contact card updated in About tab:")
    print("    Name:  Yonas Mersha")
    print("    Title: Hydro-Climate Modelling and AI Expert")
    print("    Org:   International Livestock Research Institute (ILRI)")
    print("    Email: Y.Mersha@cgiar.org")
    print()
    print("  Restart Vite:")
    print("    cd frontend && npm run dev")
    print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Fix magnitude display + developer contact")
    parser.add_argument("--path", default=".", help="Project root (default: current dir)")
    args   = parser.parse_args()
    root   = Path(args.path).resolve()
    if not (root / "backend").exists():
        print(f"WARNING: {root} may not be project root. Continue? [y/N] ", end="")
        if input().strip().lower() != "y":
            sys.exit(0)
    build(root)

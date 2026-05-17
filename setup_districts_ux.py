"""
setup_districts_ux.py
---------------------
Improves the Districts button UX so users understand they must
click a country on the map before Districts becomes active.

Changes:
  1. Districts button shows a tooltip on hover explaining the requirement
  2. Legend shows "Click a country to enable Districts" hint
  3. When a country IS selected, show its name in the Districts button
  4. Button tooltip changes from generic title to clear instruction
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


# The Districts button block to replace
OLD_DISTRICTS_BTN = """        <button
          onClick={() => setDistOn((v) => !v)}
          title={selectedCountry ? 'Toggle district boundaries' : 'Select a country first'}
          style={{
            fontSize:11, padding:'4px 10px', borderRadius:6,
            border:'1px solid',
            borderColor: distOn ? '#7F77DD' : 'var(--border-primary)',
            background: distOn ? 'rgba(127,119,221,0.15)' : 'rgba(255,255,255,0.92)',
            color: distOn ? '#534AB7' : 'var(--text-secondary)',
            cursor: selectedCountry ? 'pointer' : 'not-allowed',
            opacity: selectedCountry ? 1 : 0.5,
            fontWeight: distOn ? 600 : 400,
            boxShadow:'0 1px 4px rgba(0,0,0,0.12)',
          }}>
          Districts
        </button>"""

NEW_DISTRICTS_BTN = """        <div style={{ position:'relative' }} className="districts-btn-wrap">
          <button
            onClick={() => selectedCountry && setDistOn((v) => !v)}
            style={{
              fontSize:11, padding:'4px 10px', borderRadius:6,
              border:'1px solid',
              borderColor: distOn ? '#7F77DD' : 'var(--border-primary)',
              background: distOn
                ? 'rgba(127,119,221,0.18)'
                : selectedCountry
                  ? 'rgba(255,255,255,0.92)'
                  : 'rgba(240,240,240,0.85)',
              color: distOn ? '#534AB7'
                   : selectedCountry ? 'var(--text-secondary)'
                   : 'var(--text-faint)',
              cursor: selectedCountry ? 'pointer' : 'default',
              fontWeight: distOn ? 600 : 400,
              boxShadow:'0 1px 4px rgba(0,0,0,0.12)',
              display:'flex', alignItems:'center', gap:5,
            }}>
            {/* District icon */}
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"
              strokeLinejoin="round" style={{ opacity: selectedCountry ? 1 : 0.4 }}>
              <path d="M3 3h18v18H3z"/>
              <path d="M3 9h18M3 15h18M9 3v18M15 3v18"/>
            </svg>
            {distOn && selectedCountry
              ? 'Districts ON'
              : 'Districts'}
          </button>

          {/* Tooltip -- always visible on hover, explains requirement */}
          <div className="districts-tooltip" style={{
            position:'absolute', top:'calc(100% + 6px)', right:0,
            background:'#1a1e23', color:'#e6edf3',
            fontSize:11, lineHeight:1.5,
            padding:'7px 10px', borderRadius:6,
            whiteSpace:'nowrap', zIndex:99998,
            boxShadow:'0 4px 12px rgba(0,0,0,0.25)',
            display:'none', pointerEvents:'none',
          }}>
            {selectedCountry
              ? (distOn
                  ? 'Click to hide district boundaries'
                  : 'Click to show district boundaries for ' + (COUNTRY_MAP[selectedCountry] || selectedCountry))
              : (
                <span>
                  Click a country on the map first
                  <br/>
                  <span style={{ color:'#8b949e' }}>
                    Then Districts will activate
                  </span>
                </span>
              )}
            <div style={{
              position:'absolute', top:-5, right:14,
              width:8, height:8, background:'#1a1e23',
              transform:'rotate(45deg)',
            }} />
          </div>
        </div>"""


# CSS to add for the tooltip hover behaviour
TOOLTIP_CSS = """
/* Districts button tooltip */
.districts-btn-wrap:hover .districts-tooltip {
  display: block !important;
}
"""

# Legend update -- add country click hint when no country selected
OLD_LEGEND_CLOSE = """        <div style={{ fontSize: 10, color: 'var(--text-muted)',
                      textTransform: 'uppercase', letterSpacing: '0.06em',
                      marginBottom: 4, fontWeight: 600 }}>
          Legend
        </div>
        <LegendRow color="#1D9E75" label="Open event"   dash={false} />
        <LegendRow color="#6e7681" label="Closed event" dash={true}  />
        {selectedCountry && (
          <div style={{ marginTop:6, paddingTop:6,
                        borderTop:'1px solid var(--border-muted)',
                        fontSize:11, color:'var(--text-muted)' }}>
            Click country to deselect
          </div>
        )}"""

NEW_LEGEND_CLOSE = """        <div style={{ fontSize: 10, color: 'var(--text-muted)',
                      textTransform: 'uppercase', letterSpacing: '0.06em',
                      marginBottom: 4, fontWeight: 600 }}>
          Legend
        </div>
        <LegendRow color="#1D9E75" label="Open event"   dash={false} />
        <LegendRow color="#6e7681" label="Closed event" dash={true}  />
        {!selectedCountry ? (
          <div style={{ marginTop:6, paddingTop:6,
                        borderTop:'1px solid var(--border-muted)',
                        fontSize:10, color:'var(--text-muted)',
                        lineHeight:1.4 }}>
            Click a country to<br/>
            filter + enable Districts
          </div>
        ) : (
          <div style={{ marginTop:6, paddingTop:6,
                        borderTop:'1px solid var(--border-muted)',
                        fontSize:10, color:'var(--text-muted)' }}>
            Click country to deselect
          </div>
        )}"""


def apply(path: Path, old: str, new: str, label: str) -> bool:
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
    hdr(f"Improving Districts button UX in: {root}")

    mp  = fe / "src/components/MapPanel.jsx"
    css = fe / "src/index.css"

    # 1. Replace the Districts button with tooltip version
    apply(mp, OLD_DISTRICTS_BTN, NEW_DISTRICTS_BTN, "MapPanel.jsx -- Districts button + tooltip")

    # 2. Update legend to show country click hint
    apply(mp, OLD_LEGEND_CLOSE, NEW_LEGEND_CLOSE, "MapPanel.jsx -- legend hint")

    # 3. Add tooltip CSS to index.css
    if css.exists():
        css_txt = css.read_text(encoding="utf-8")
        if ".districts-tooltip" not in css_txt:
            css.write_text(css_txt.rstrip() + "\n" + TOOLTIP_CSS, encoding="utf-8")
            ow("patch   frontend/src/index.css -- districts tooltip CSS")

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

    hdr("Done")
    print()
    print("  Districts button behaviour:")
    print()
    print("  Before selecting a country:")
    print("    Button: greyed out, cursor default (not pointer)")
    print("    Hover tooltip: 'Click a country on the map first'")
    print("              then: 'Then Districts will activate'")
    print("    Legend: shows 'Click a country to filter + enable Districts'")
    print()
    print("  After clicking a country (e.g. Kenya):")
    print("    Button: fully active, purple border when on")
    print("    Hover tooltip: 'Click to show district boundaries for Kenya'")
    print("    Button label: 'Districts ON' when active")
    print("    Legend: shows 'Click country to deselect'")
    print()
    print("  Restart Vite:")
    print("    cd frontend && npm run dev")
    print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Improve Districts button UX")
    parser.add_argument("--path", default=".")
    args   = parser.parse_args()
    root   = Path(args.path).resolve()
    if not (root / "backend").exists():
        print(f"WARNING: {root} may not be project root. Continue? [y/N] ", end="")
        if input().strip().lower() != "y":
            sys.exit(0)
    build(root)

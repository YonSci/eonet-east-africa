"""
setup_contacts_visible.py
-------------------------
The contact cards ARE in the JSX and ARE rendering — but in light mode
their background (#f0f3f6) is nearly identical to the page background
(#f6f8fa), so they look like blank space. This script rewrites the
Credits section with high-contrast, clearly-visible contact cards.
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

# Find and replace the entire Credits section block
OLD_CREDITS_SECTION_START = '{/* Credits */}'
OLD_CREDITS_SECTION_END   = '      </Section>\n\n      {/* Email alert subscriptions */}'

NEW_CREDITS_BLOCK = """      {/* Credits and contacts -- standalone block, no Section wrapper */}
      <div style={{ marginBottom: 32 }}>
        <h2 style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)',
                     marginBottom: 16, paddingBottom: 8,
                     borderBottom: '1px solid var(--border-primary)' }}>
          Credits and contacts
        </h2>

        {/* --- Yonas Mersha card --- */}
        <div style={{
          display: 'flex', alignItems: 'flex-start', gap: 16,
          padding: '16px 18px', marginBottom: 12,
          background: '#ffffff',
          border: '1.5px solid #1D9E75',
          borderLeft: '5px solid #1D9E75',
          borderRadius: 10,
          boxShadow: '0 2px 8px rgba(29,158,117,0.10)',
        }}>
          {/* Avatar */}
          <div style={{
            width: 52, height: 52, borderRadius: '50%', flexShrink: 0,
            background: '#1D9E75',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 16, fontWeight: 700, color: '#ffffff',
            letterSpacing: '0.04em',
          }}>
            YM
          </div>
          {/* Info */}
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 16, fontWeight: 700,
                          color: '#0F2E24', marginBottom: 3 }}>
              Yonas Mersha
            </div>
            <div style={{ fontSize: 13, color: '#1D9E75', fontWeight: 600,
                          marginBottom: 4 }}>
              Hydro-Climate Modelling and AI Expert
            </div>
            <div style={{ fontSize: 12, color: '#4a5568', marginBottom: 10 }}>
              International Livestock Research Institute (ILRI)
            </div>
            <a href="mailto:Y.Mersha@cgiar.org"
               style={{
                 display: 'inline-flex', alignItems: 'center', gap: 6,
                 fontSize: 13, color: '#378ADD', fontWeight: 500,
                 textDecoration: 'none',
                 padding: '4px 10px', borderRadius: 6,
                 background: '#E6F1FB',
                 border: '1px solid #378ADD44',
               }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" strokeWidth="2" strokeLinecap="round"
                   strokeLinejoin="round">
                <rect x="2" y="4" width="20" height="16" rx="2"/>
                <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
              </svg>
              Y.Mersha@cgiar.org
            </a>
          </div>
        </div>

        {/* --- Dr. Teferi Demissie card --- */}
        <div style={{
          display: 'flex', alignItems: 'flex-start', gap: 16,
          padding: '16px 18px', marginBottom: 20,
          background: '#ffffff',
          border: '1.5px solid #378ADD',
          borderLeft: '5px solid #378ADD',
          borderRadius: 10,
          boxShadow: '0 2px 8px rgba(55,138,221,0.10)',
        }}>
          {/* Avatar */}
          <div style={{
            width: 52, height: 52, borderRadius: '50%', flexShrink: 0,
            background: '#378ADD',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 16, fontWeight: 700, color: '#ffffff',
            letterSpacing: '0.04em',
          }}>
            TD
          </div>
          {/* Info */}
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 16, fontWeight: 700,
                          color: '#0C1A2E', marginBottom: 3 }}>
              Dr. Teferi Demissie
            </div>
            <div style={{ fontSize: 13, color: '#185FA5', fontWeight: 600,
                          marginBottom: 4 }}>
              Climate and Hydrology Researcher
            </div>
            <div style={{ fontSize: 12, color: '#4a5568', marginBottom: 10 }}>
              International Livestock Research Institute (ILRI)
            </div>
            <a href="mailto:t.demissie@cgiar.org"
               style={{
                 display: 'inline-flex', alignItems: 'center', gap: 6,
                 fontSize: 13, color: '#185FA5', fontWeight: 500,
                 textDecoration: 'none',
                 padding: '4px 10px', borderRadius: 6,
                 background: '#E6F1FB',
                 border: '1px solid #378ADD44',
               }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" strokeWidth="2" strokeLinecap="round"
                   strokeLinejoin="round">
                <rect x="2" y="4" width="20" height="16" rx="2"/>
                <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
              </svg>
              t.demissie@cgiar.org
            </a>
          </div>
        </div>

        {/* Info rows */}
        <InfoRow label="Data region"    value="Greater Horn of Africa (11 countries)" />
        <InfoRow label="Data provider"  value="NASA Goddard Space Flight Center -- EONET"
          link="https://eonet.gsfc.nasa.gov" />
        <InfoRow label="Satellite data" value="NASA MODIS, VIIRS, Ocean Color instruments" />
        <InfoRow label="Hazard sources" value="USGS, GDACS, Smithsonian GVP, JTWC, FEWS NET, ReliefWeb" />
        <InfoRow label="Open source"    value="MIT License -- source code on GitHub" />
      </div>

      {/* Email alert subscriptions */}"""


def build(root: Path):
    fe = root / "frontend"
    ap = fe / "src/components/AboutPanel.jsx"
    hdr(f"Making contact cards visible in: {ap}")

    txt = ap.read_text(encoding="utf-8")

    # Find the block to replace
    start_idx = txt.find(OLD_CREDITS_SECTION_START)
    end_idx   = txt.find(OLD_CREDITS_SECTION_END)

    if start_idx == -1:
        print(f"  ERROR  Could not find start marker: {OLD_CREDITS_SECTION_START!r}")
        sys.exit(1)
    if end_idx == -1:
        print(f"  ERROR  Could not find end marker")
        sys.exit(1)

    before = txt[:start_idx]
    after  = txt[end_idx + len(OLD_CREDITS_SECTION_END):]

    new_txt = before + NEW_CREDITS_BLOCK + "\n      {/* Email alert subscriptions */}" + after
    ap.write_text(new_txt, encoding="utf-8")
    ow("rewrite  Credits section with high-contrast contact cards")

    # ASCII check
    raw = ap.read_bytes()
    bad = [(i+1) for i, line in enumerate(raw.split(b"\n")) if any(b > 127 for b in line)]
    if bad:
        print(f"  WARN  Non-ASCII: {bad[:5]}")
    else:
        ok("ASCII-clean -- OXC safe")

    # Verify
    txt2 = ap.read_text()
    checks = [
        ("Yonas Mersha",             "Yonas name present"),
        ("Dr. Teferi Demissie",      "Teferi name present"),
        ("Y.Mersha@cgiar.org",       "Yonas email"),
        ("t.demissie@cgiar.org",     "Teferi email"),
        ("boxShadow",                "visible shadow styling"),
        ("background: '#ffffff'",    "white card background"),
        ("border: '1.5px solid #1D9E75'", "green border Yonas"),
        ("border: '1.5px solid #378ADD'", "blue border Teferi"),
    ]
    print()
    all_ok = True
    for needle, label in checks:
        found = needle in txt2
        if not found: all_ok = False
        print(f"  {'OK' if found else 'MISSING'}  {label}")

    hdr("Done")
    print()
    print("  Root cause: in light mode --bg-elevated (#f0f3f6) is nearly")
    print("  identical to --bg-base (#f6f8fa) -- cards rendered invisible.")
    print()
    print("  Fix: cards now use explicit white (#ffffff) backgrounds with")
    print("  1.5px coloured borders, 5px left accent, and box shadows.")
    print("  Visible in both light and dark mode regardless of CSS vars.")
    print()
    print("  Card layout:")
    print("    [YM] Yonas Mersha")
    print("         Hydro-Climate Modelling and AI Expert")
    print("         International Livestock Research Institute (ILRI)")
    print("         [mail] Y.Mersha@cgiar.org")
    print()
    print("    [TD] Dr. Teferi Demissie")
    print("         Climate and Hydrology Researcher")
    print("         International Livestock Research Institute (ILRI)")
    print("         [mail] t.demissie@cgiar.org")
    print()
    print("  Restart Vite:")
    print("    cd frontend && npm run dev")
    print("    Go to About tab and scroll to 'Credits and contacts'")
    print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default=".")
    args   = parser.parse_args()
    root   = Path(args.path).resolve()
    if not (root / "backend").exists():
        print(f"WARNING: {root} may not be project root. Continue? [y/N] ", end="")
        if input().strip().lower() != "y":
            sys.exit(0)
    build(root)

"""
setup_credits.py
----------------
Adds developer credits and updates the short title to NET-EA.

Run from the eonet-east-africa project root:
    python setup_credits.py

Files updated:
    frontend/src/components/TopNav.jsx      -- NET-EA short title
    frontend/src/components/AboutPanel.jsx  -- developer card
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
# TopNav.jsx  -- NET-EA as short title
# =============================================================================
FILES["src/components/TopNav.jsx"] = """import React from 'react'
import useAppStore from '../store/useAppStore.js'
import { useCacheStatus } from '../api/queries.js'

export default function TopNav() {
  const { lightMode, toggleLight, toggleSidebar, dataSource, setDataSource } = useAppStore()
  const { data: cacheInfo } = useCacheStatus()
  const isMock = dataSource === 'mock'

  return (
    <header style={{
      height: 'var(--topnav-h)',
      background: 'var(--bg-surface)',
      borderBottom: '1px solid var(--border-primary)',
      display: 'flex', alignItems: 'center',
      padding: '0 16px', gap: 10, flexShrink: 0, zIndex: 100,
    }}>

      {/* Sidebar toggle */}
      <button onClick={toggleSidebar} title="Toggle sidebar" style={btnStyle}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
          <rect x="1" y="3"    width="14" height="1.5" rx="0.75"/>
          <rect x="1" y="7.25" width="14" height="1.5" rx="0.75"/>
          <rect x="1" y="11.5" width="14" height="1.5" rx="0.75"/>
        </svg>
      </button>

      {/* Satellite icon */}
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
           stroke="#1D9E75" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M13 7L17 3M17 3L21 7M17 3V13"/>
        <circle cx="9" cy="15" r="4"/>
        <path d="M3 21L7 17"/>
        <path d="M9 11L13 7"/>
      </svg>

      {/* Title block */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
          <span style={{ fontWeight: 700, fontSize: 15, color: 'var(--text-primary)',
                         letterSpacing: '-0.02em', lineHeight: 1 }}>
            NET-EA
          </span>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 400 }}>
            v2.0
          </span>
        </div>
        <span style={{ fontSize: 10, color: '#1D9E75', fontWeight: 500,
                       letterSpacing: '0.03em' }}>
          Natural Event Tracker -- East Africa
        </span>
      </div>

      <div style={{ flex: 1 }} />

      {/* Demo badge */}
      {isMock && (
        <span style={{ fontSize: 11, fontWeight: 500, padding: '2px 8px',
                       borderRadius: 100, background: '#EAF3DE', color: '#27500A',
                       border: '1px solid #97C45944' }}>
          Demo data
        </span>
      )}

      {/* Live cache info */}
      {cacheInfo && !isMock && (
        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
          {cacheInfo.event_count} events
          {cacheInfo.ttl_remaining_s != null
            ? ' -- refresh in ' + Math.ceil(cacheInfo.ttl_remaining_s / 60) + 'm'
            : ''}
        </span>
      )}

      {/* Data source toggle */}
      <button
        onClick={() => setDataSource(isMock ? 'auto' : 'mock')}
        title={isMock ? 'Switch to live API' : 'Switch to demo data'}
        style={{
          ...btnStyle, fontSize: 11, padding: '4px 10px', borderRadius: 6,
          border: '1px solid var(--border-primary)',
        }}
      >
        {isMock ? 'Connect API' : 'Demo mode'}
      </button>

      {/* Theme toggle */}
      <button onClick={toggleLight} title="Toggle theme" style={btnStyle}>
        {lightMode ? (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="4"/>
            <line x1="12" y1="2"  x2="12" y2="4"/>
            <line x1="12" y1="20" x2="12" y2="22"/>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
            <line x1="2"  y1="12" x2="4"  y2="12"/>
            <line x1="20" y1="12" x2="22" y2="12"/>
          </svg>
        ) : (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" strokeWidth="2">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
          </svg>
        )}
      </button>
    </header>
  )
}

const btnStyle = {
  background: 'transparent', border: 'none',
  color: 'var(--text-secondary)', cursor: 'pointer',
  padding: '6px', borderRadius: 6,
  display: 'flex', alignItems: 'center', fontSize: 13,
}
"""

# =============================================================================
# AboutPanel.jsx developer section patch (prepend to credits section)
# =============================================================================
DEVELOPER_CARD = """      {/* Developer card */}
      <div style={{
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border-primary)',
        borderLeft: '3px solid #1D9E75',
        borderRadius: 'var(--radius-md)',
        padding: '14px 16px',
        marginBottom: 20,
        display: 'flex', alignItems: 'flex-start', gap: 14,
      }}>
        {/* Avatar initials */}
        <div style={{
          width: 44, height: 44, borderRadius: '50%', flexShrink: 0,
          background: '#E1F5EE', border: '2px solid #1D9E75',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 14, fontWeight: 700, color: '#085041',
        }}>
          YM
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)',
                        marginBottom: 2 }}>
            Yonas M.
          </div>
          <div style={{ fontSize: 12, color: '#1D9E75', fontWeight: 500,
                        marginBottom: 6 }}>
            Climate Modelling and AI Expert
          </div>
          <a href="mailto:Y.Mersha@cgiar.org"
             style={{ fontSize: 12, color: '#378ADD', textDecoration: 'none',
                      display: 'flex', alignItems: 'center', gap: 5 }}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" strokeWidth="2" strokeLinecap="round"
                 strokeLinejoin="round">
              <rect x="2" y="4" width="20" height="16" rx="2"/>
              <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
            </svg>
            Y.Mersha@cgiar.org
          </a>
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)',
                      textAlign: 'right', flexShrink: 0 }}>
          <div style={{ marginBottom: 2 }}>NET-EA v2.0</div>
          <div>2025</div>
        </div>
      </div>

"""

# Text to insert the developer card before (the first InfoRow in Credits section)
CREDITS_INSERT_BEFORE = '        <InfoRow label="Data region"'


def build(root: Path):
    fe = root / "frontend"
    hdr(f"Applying credits + NET-EA title in: {root}")

    # 1. Full rewrite of TopNav
    target = fe / "src/components/TopNav.jsx"
    target.write_text(FILES["src/components/TopNav.jsx"], encoding="utf-8")
    ow("update  frontend/src/components/TopNav.jsx")

    # 2. Patch AboutPanel -- inject developer card before credits InfoRow
    ap = fe / "src/components/AboutPanel.jsx"
    if ap.exists():
        txt = ap.read_text(encoding="utf-8")

        # Patch title references
        txt = txt.replace('NET-EA v2.0 -- Natural Event Tracker for East Africa 2025',
                          'NET-EA v2.0 -- Yonas M. -- Y.Mersha@cgiar.org')

        # Insert developer card before the first InfoRow in the credits section
        if CREDITS_INSERT_BEFORE in txt and 'YM' not in txt:
            txt = txt.replace(
                CREDITS_INSERT_BEFORE,
                DEVELOPER_CARD + CREDITS_INSERT_BEFORE
            )

        ap.write_text(txt, encoding="utf-8")
        ow("update  frontend/src/components/AboutPanel.jsx")
    else:
        print("  SKIP  AboutPanel.jsx not found -- run setup_about.py first")

    hdr("Done")
    print()
    print("  Changes:")
    print("    TopNav: 'NET-EA v2.0' bold + 'Natural Event Tracker -- East Africa' subtitle")
    print("    About: developer card with YM avatar, name, title, email")
    print("    Footer: NET-EA v2.0 -- Yonas M. -- Y.Mersha@cgiar.org")
    print()
    print("  Restart Vite:")
    print("    cd frontend && npm run dev")
    print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Add developer credits + NET-EA title")
    parser.add_argument("--path", default=".", help="Project root (default: current dir)")
    args = parser.parse_args()
    root = Path(args.path).resolve()
    if not (root / "backend").exists():
        print(f"WARNING: {root} may not be project root. Continue? [y/N] ", end="")
        if input().strip().lower() != "y":
            sys.exit(0)
    build(root)

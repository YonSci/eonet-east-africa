"""
setup_contacts_fix.py
---------------------
Fixes the About tab contacts: both people ended up inside the same
flex container (single card). This script replaces that broken block
with two properly separated, self-contained contact cards.
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

# The exact broken block currently in the file (both contacts in one div)
OLD_CONTACTS_BLOCK = """{/* Developer card */}
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
          <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)',
                        marginBottom: 1 }}>
            Yonas Mersha
          </div>
          <div style={{ fontSize: 12, color: '#1D9E75', fontWeight: 500,
                        marginBottom: 3 }}>
            Hydro-Climate Modelling and AI Expert
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>
            International Livestock Research Institute (ILRI)
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

        {/* Dr. Teferi Demissie */}
        <div style={{
          width: 44, height: 44, borderRadius: '50%', flexShrink: 0,
          background: '#E6F1FB', border: '2px solid #378ADD',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 14, fontWeight: 700, color: '#0C447C',
        }}>
          TD
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)',
                        marginBottom: 1 }}>
            Dr. Teferi Demissie
          </div>
          <div style={{ fontSize: 12, color: '#378ADD', fontWeight: 500,
                        marginBottom: 3 }}>
            Senior Climate Scientist
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>
            International Livestock Research Institute (ILRI)
          </div>
          <a href="mailto:t.demissie@cgiar.org"
             style={{ fontSize: 12, color: '#378ADD', textDecoration: 'none',
                      display: 'flex', alignItems: 'center', gap: 5 }}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" strokeWidth="2" strokeLinecap="round"
                 strokeLinejoin="round">
              <rect x="2" y="4" width="20" height="16" rx="2"/>
              <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
            </svg>
            t.demissie@cgiar.org
          </a>
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)',
                      textAlign: 'right', flexShrink: 0 }}>
          <div style={{ marginBottom: 2 }}>NET-EA v2.0</div>
          <div>2025</div>
        </div>
      </div>"""

# Two separate, properly-structured contact cards
NEW_CONTACTS_BLOCK = """{/* Contact card -- Yonas Mersha */}
      <div style={{
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border-primary)',
        borderLeft: '3px solid #1D9E75',
        borderRadius: 'var(--radius-md)',
        padding: '14px 16px',
        marginBottom: 10,
        display: 'flex', alignItems: 'flex-start', gap: 14,
      }}>
        <div style={{
          width: 44, height: 44, borderRadius: '50%', flexShrink: 0,
          background: '#E1F5EE', border: '2px solid #1D9E75',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 14, fontWeight: 700, color: '#085041',
        }}>
          YM
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)',
                        marginBottom: 2 }}>
            Yonas Mersha
          </div>
          <div style={{ fontSize: 12, color: '#1D9E75', fontWeight: 500,
                        marginBottom: 3 }}>
            Hydro-Climate Modelling and AI Expert
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 8 }}>
            International Livestock Research Institute (ILRI)
          </div>
          <a href="mailto:Y.Mersha@cgiar.org"
             style={{ fontSize: 12, color: '#378ADD', textDecoration: 'none',
                      display: 'inline-flex', alignItems: 'center', gap: 5 }}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" strokeWidth="2" strokeLinecap="round"
                 strokeLinejoin="round">
              <rect x="2" y="4" width="20" height="16" rx="2"/>
              <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
            </svg>
            Y.Mersha@cgiar.org
          </a>
        </div>
      </div>

      {/* Contact card -- Dr. Teferi Demissie */}
      <div style={{
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border-primary)',
        borderLeft: '3px solid #378ADD',
        borderRadius: 'var(--radius-md)',
        padding: '14px 16px',
        marginBottom: 20,
        display: 'flex', alignItems: 'flex-start', gap: 14,
      }}>
        <div style={{
          width: 44, height: 44, borderRadius: '50%', flexShrink: 0,
          background: '#E6F1FB', border: '2px solid #378ADD',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 14, fontWeight: 700, color: '#0C447C',
        }}>
          TD
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)',
                        marginBottom: 2 }}>
            Dr. Teferi Demissie
          </div>
          <div style={{ fontSize: 12, color: '#378ADD', fontWeight: 500,
                        marginBottom: 3 }}>
            Senior Climate Scientist
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 8 }}>
            International Livestock Research Institute (ILRI)
          </div>
          <a href="mailto:t.demissie@cgiar.org"
             style={{ fontSize: 12, color: '#378ADD', textDecoration: 'none',
                      display: 'inline-flex', alignItems: 'center', gap: 5 }}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" strokeWidth="2" strokeLinecap="round"
                 strokeLinejoin="round">
              <rect x="2" y="4" width="20" height="16" rx="2"/>
              <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
            </svg>
            t.demissie@cgiar.org
          </a>
        </div>
      </div>"""


def build(root: Path):
    fe  = root / "frontend"
    ap  = fe / "src/components/AboutPanel.jsx"
    hdr(f"Fixing contact cards in: {ap}")

    if not ap.exists():
        print("  ERROR  AboutPanel.jsx not found")
        sys.exit(1)

    txt = ap.read_text(encoding="utf-8")

    if OLD_CONTACTS_BLOCK not in txt:
        print("  WARN  Old contacts block not found -- checking if already fixed...")
        # Check if already has two separate cards
        if "Contact card -- Yonas" in txt and "Contact card -- Dr. Teferi" in txt:
            ok("Already has two separate contact cards -- no change needed")
        else:
            print("  ERROR  Cannot find the contacts block to replace.")
            print("  The AboutPanel.jsx may be in an unexpected state.")
            print("  Please check the file manually.")
        return

    txt = txt.replace(OLD_CONTACTS_BLOCK, NEW_CONTACTS_BLOCK, 1)
    ap.write_text(txt, encoding="utf-8")
    ow("rewrite  frontend/src/components/AboutPanel.jsx -- split into 2 separate cards")

    # ASCII check
    raw = ap.read_bytes()
    bad = [(i+1) for i, line in enumerate(raw.split(b"\n")) if any(b > 127 for b in line)]
    if bad:
        print(f"  WARN  Non-ASCII on lines: {bad[:5]}")
    else:
        ok("ASCII-clean -- OXC safe")

    # Verify
    txt2 = ap.read_text()
    checks = [
        ("Contact card -- Yonas Mersha",    "Yonas card has its own div"),
        ("Contact card -- Dr. Teferi",      "Teferi card has its own div"),
        ("Y.Mersha@cgiar.org",              "Yonas email present"),
        ("t.demissie@cgiar.org",            "Teferi email present"),
        ("borderLeft: '3px solid #1D9E75'", "Yonas green left border"),
        ("borderLeft: '3px solid #378ADD'", "Teferi blue left border"),
    ]
    print()
    all_ok = True
    for needle, label in checks:
        found = needle in txt2
        if not found: all_ok = False
        print(f"  {'OK' if found else 'MISSING'}  {label}")

    hdr("Done")
    print()
    print("  Two separate contact cards in About tab:")
    print("    Yonas Mersha   -- green left border, YM avatar, Y.Mersha@cgiar.org")
    print("    Dr. Teferi Demissie -- blue left border, TD avatar, t.demissie@cgiar.org")
    print()
    print("  Restart Vite:")
    print("    cd frontend && npm run dev")
    print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Fix About tab contact cards")
    parser.add_argument("--path", default=".", help="Project root (default: current dir)")
    args   = parser.parse_args()
    root   = Path(args.path).resolve()
    if not (root / "backend").exists():
        print(f"WARNING: {root} may not be project root. Continue? [y/N] ", end="")
        if input().strip().lower() != "y":
            sys.exit(0)
    build(root)

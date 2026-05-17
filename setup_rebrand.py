"""
setup_rebrand.py
----------------
Renames NET-EA to NHMT-EA across all frontend and config files.

Old: Natural Event Tracker for East Africa (NET-EA)
New: Natural Hazard Monitoring & Tracking for East Africa (NHMT-EA)

Run from the eonet-east-africa project root:
    python setup_rebrand.py
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
# All substitutions -- ordered from most specific to most general
# to avoid double-replacement
# =============================================================================
SUBSTITUTIONS = [
    # Full title variants
    ("Natural Event Tracker for East Africa (NET-EA)",
     "Natural Hazard Monitoring & Tracking for East Africa (NHMT-EA)"),
    ("Natural Event Tracker for East Africa",
     "Natural Hazard Monitoring & Tracking for East Africa"),

    # Short code / badge
    ("NET-EA v3.0",  "NHMT-EA v3.0"),
    ("NET-EA v2.0",  "NHMT-EA v2.0"),
    ("NET-EA v1.0",  "NHMT-EA v1.0"),
    ("NET-EA v3",    "NHMT-EA v3"),
    ("NET-EA v2",    "NHMT-EA v2"),
    ("'NET-EA'",     "'NHMT-EA'"),
    ('"NET-EA"',     '"NHMT-EA"'),
    ("NET-EA --",    "NHMT-EA --"),
    ("-- NET-EA",    "-- NHMT-EA"),
    ("NET-EA:",      "NHMT-EA:"),
    (": NET-EA",     ": NHMT-EA"),
    ("NET-EA Alert", "NHMT-EA Alert"),
    ("NET-EA Test",  "NHMT-EA Test"),
    # Generic NET-EA last (catches any remaining)
    ("NET-EA",       "NHMT-EA"),

    # Storage keys (localStorage) -- must also update
    ("net-ea-alert-subscriptions", "nhmt-ea-alert-subscriptions"),
    ("net-ea-filter-presets",      "nhmt-ea-filter-presets"),

    # App name in package.json
    ('"name": "eonet-east-africa"', '"name": "nhmt-ea"'),

    # Page title
    ("NET-EA -- Natural Event Tracker for East Africa",
     "NHMT-EA -- Natural Hazard Monitoring & Tracking for East Africa"),
    ("Natural Event Tracker for East Africa",
     "Natural Hazard Monitoring & Tracking for East Africa"),

    # TopNav subtitle line
    ("Natural Event Tracker -- East Africa",
     "Natural Hazard Monitoring & Tracking -- East Africa"),
    ("Natural Event Tracker",
     "Natural Hazard Monitoring & Tracking"),

    # Description meta tag
    ("Near real-time natural hazard monitoring for the Greater Horn of Africa, powered by NASA EONET v3.",
     "Natural hazard monitoring and tracking for the Greater Horn of Africa, powered by NASA EONET v3."),

    # Manifest / PWA
    ("NET-EA -- Natural Event Tracker for East Africa",
     "NHMT-EA -- Natural Hazard Monitoring & Tracking for East Africa"),
    ("short_name: 'NET-EA'",    "short_name: 'NHMT-EA'"),
    ('"short_name": "NET-EA"',  '"short_name": "NHMT-EA"'),

    # Footer / About page credits
    ("NET-EA Natural Event Tracker for East Africa 2025",
     "NHMT-EA Natural Hazard Monitoring & Tracking for East Africa 2025"),

    # EmailJS subjects / bodies in emailService.js
    ("NET-EA Alert Subscription Confirmed",
     "NHMT-EA Alert Subscription Confirmed"),
    ("NET-EA Alert:",   "NHMT-EA Alert:"),
    ("NET-EA Team",     "NHMT-EA Team"),

    # Containerfile labels
    ("NET-EA Natural Event Tracker for East Africa -- Backend",
     "NHMT-EA Natural Hazard Monitoring & Tracking for East Africa -- Backend"),
    ("NET-EA Natural Event Tracker for East Africa -- Frontend",
     "NHMT-EA Natural Hazard Monitoring & Tracking for East Africa -- Frontend"),
    ("NET-EA Natural Event Tracker -- Frontend",
     "NHMT-EA Natural Hazard Monitoring & Tracking -- Frontend"),

    # PODMAN_DEPLOY / HETZNER_DEPLOY docs
    ("NET-EA v3.0 -- Yonas Mersha",  "NHMT-EA v3.0 -- Yonas Mersha"),
    ("NET-EA Podman",                "NHMT-EA Podman"),
    ("NET-EA Backend",               "NHMT-EA Backend"),
    ("NET-EA Frontend",              "NHMT-EA Frontend"),
    ("NET-EA Deploy",                "NHMT-EA Deploy"),
    ("NET-EA is running",            "NHMT-EA is running"),
    ("NET-EA Status",                "NHMT-EA Status"),
    ("NET-EA Podman Build",          "NHMT-EA Podman Build"),
    ("NET-EA Podman Start",          "NHMT-EA Podman Start"),
    ("NET-EA logs",                  "NHMT-EA logs"),
    ("NET-EA Server",                "NHMT-EA Server"),
    ("NET-EA Update",                "NHMT-EA Update"),
]

# File extensions to process
EXTENSIONS = {
    ".jsx", ".js", ".ts", ".tsx",
    ".json", ".html", ".css",
    ".md", ".txt", ".sh", ".yml", ".yaml",
    ".conf", ".toml", ".env", ".example",
    ".container", ".pod",
}

# Files / dirs to skip entirely
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "__pycache__"}


def should_process(path: Path) -> bool:
    # Skip binary files and excluded dirs
    for part in path.parts:
        if part in SKIP_DIRS:
            return False
    return path.suffix.lower() in EXTENSIONS or path.name in {
        "Containerfile", "Dockerfile", "Caddyfile",
        ".env.example", ".env.local", ".podmanignore", ".gitignore",
        "netlify.toml", "requirements.txt",
    }


def apply_subs(content: str) -> tuple[str, int]:
    count = 0
    for old, new in SUBSTITUTIONS:
        if old in content:
            content = content.replace(old, new)
            count += 1
    return content, count


def build(root: Path):
    hdr(f"Rebranding NET-EA -> NHMT-EA in: {root}")
    processed = changed = 0

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if not should_process(path):
            continue

        try:
            original = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        new_content, n = apply_subs(original)
        if n > 0:
            path.write_text(new_content, encoding="utf-8")
            rel = path.relative_to(root)
            ow(f"  {n:2} change{'s' if n > 1 else ' '}  {rel}")
            changed += 1
        processed += 1

    # Also rename the localStorage key in AboutPanel if present
    # (already handled by SUBSTITUTIONS but double-check)
    about = root / "frontend/src/components/AboutPanel.jsx"
    if about.exists():
        txt = about.read_text()
        if "net-ea" in txt.lower() and "nhmt-ea" not in txt.lower():
            txt = txt.replace("net-ea", "nhmt-ea")
            about.write_text(txt)
            ow("  extra    frontend/src/components/AboutPanel.jsx (lowercase net-ea)")

    # ASCII check
    print()
    bad = []
    src = root / "frontend/src"
    if src.exists():
        for f in list(src.rglob("*.jsx")) + list(src.rglob("*.js")):
            raw = f.read_bytes()
            for i, line in enumerate(raw.split(b"\n"), 1):
                if any(b > 127 for b in line):
                    bad.append(f"  {f.name}:{i}")
    if bad:
        print("  WARN  Non-ASCII (OXC will reject):")
        for b in bad[:6]: print(b)
    else:
        ok("ASCII-clean -- OXC safe")

    # Spot-check key files
    print()
    checks = [
        ("NHMT-EA",  root/"frontend/index.html",                               "index.html title"),
        ("NHMT-EA",  root/"frontend/src/components/TopNav.jsx",                "TopNav badge"),
        ("NHMT-EA",  root/"frontend/src/components/AboutPanel.jsx",            "AboutPanel"),
        ("NHMT-EA",  root/"frontend/vite.config.js",                           "vite.config manifest"),
        ("nhmt-ea",  root/"frontend/src/components/AlertSubscription.jsx",     "localStorage key"),
        ("nhmt-ea",  root/"frontend/src/components/SavedFilters.jsx",          "saved filters key"),
        ("NHMT-EA",  root/"frontend/package.json",                             "package.json"),
        ("NHMT-EA",  root/"podman/Containerfile.backend",                      "Containerfile"),
        ("NHMT-EA",  root/"PODMAN_DEPLOY.md",                                  "PODMAN docs"),
        ("NHMT-EA",  root/"HETZNER_DEPLOY.md",                                 "HETZNER docs"),
    ]
    all_ok = True
    for needle, path, label in checks:
        if not path.exists():
            print(f"  SKIP  {label} (file not found)")
            continue
        found = needle in path.read_text(errors="ignore")
        if not found:
            all_ok = False
        print(f"  {'OK' if found else 'MISSING'}  {label}")

    # Verify no NET-EA left in visible JSX strings
    print()
    remaining = []
    src = root / "frontend/src"
    if src.exists():
        for f in list(src.rglob("*.jsx")) + list(src.rglob("*.js")):
            txt = f.read_text(errors="ignore")
            for i, line in enumerate(txt.split("\n"), 1):
                if "NET-EA" in line:
                    # Allow comments and internal variable names
                    stripped = line.strip()
                    if not stripped.startswith("//") and "NHMT-EA" not in line:
                        remaining.append(f"  {f.name}:{i}  {stripped[:70]}")
    if remaining:
        print("  Remaining NET-EA references in JSX:")
        for r in remaining[:8]:
            print(r)
    else:
        ok("No remaining NET-EA in JSX/JS files")

    hdr("Done")
    print(f"  Files scanned : {processed}")
    print(f"  Files changed : {changed}")
    print()
    print("  Rebrand complete:")
    print("    NET-EA  ->  NHMT-EA")
    print("    Natural Event Tracker for East Africa")
    print("    ->  Natural Hazard Monitoring & Tracking for East Africa")
    print()
    print("  Restart Vite:")
    print("    cd frontend && npm run dev")
    print()
    print("  Rebuild for deployment:")
    print("    bash scripts/podman_build.sh")
    print("    bash scripts/server_deploy.sh")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rebrand NET-EA -> NHMT-EA")
    parser.add_argument("--path", default=".", help="Project root (default: current dir)")
    args   = parser.parse_args()
    root   = Path(args.path).resolve()
    if not (root / "backend").exists():
        print(f"WARNING: {root} may not be project root. Continue? [y/N] ", end="")
        if input().strip().lower() != "y":
            sys.exit(0)
    build(root)

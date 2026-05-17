"""
setup_line_endings.py
---------------------
Converts all shell scripts and config files from Windows CRLF (\\r\\n)
to Unix LF (\\n) line endings.

This is the root cause of all \\r errors:
  $'\\r': command not found
  set: -: invalid option

Python on Windows writes files with \\r\\n by default.
Linux/Podman requires \\n only.

Run from the eonet-east-africa project root:
    python setup_line_endings.py
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

# File types to convert
TEXT_EXTENSIONS = {
    ".sh", ".py", ".js", ".jsx", ".ts", ".tsx",
    ".json", ".html", ".css", ".md", ".txt",
    ".yml", ".yaml", ".toml", ".conf", ".cfg",
    ".env", ".example", ".local",
    ".container", ".pod",
    ".gitignore", ".podmanignore",
}

TEXT_NAMES = {
    "Containerfile", "Dockerfile", "Caddyfile",
    "Makefile", "nginx.conf", "netlify.toml",
    "requirements.txt",
}

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "__pycache__"}


def is_text_file(path: Path) -> bool:
    for part in path.parts:
        if part in SKIP_DIRS:
            return False
    return path.suffix.lower() in TEXT_EXTENSIONS or path.name in TEXT_NAMES


def convert_file(path: Path) -> bool:
    """Convert CRLF to LF. Returns True if file was changed."""
    try:
        raw = path.read_bytes()
    except Exception:
        return False

    if b"\r\n" not in raw and b"\r" not in raw:
        return False  # already LF-only

    # Replace CRLF -> LF, then lone CR -> LF
    fixed = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")

    if fixed == raw:
        return False

    path.write_bytes(fixed)
    return True


def build(root: Path):
    hdr(f"Converting CRLF -> LF in: {root}")
    converted = skipped = 0

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if not is_text_file(path):
            continue

        rel = path.relative_to(root)
        if convert_file(path):
            ow(f"fixed   {rel}")
            converted += 1
        else:
            skipped += 1

    # Make all .sh files executable
    print()
    for sh in sorted(root.rglob("*.sh")):
        sh.chmod(sh.stat().st_mode | 0o755)

    # Verify key scripts are clean
    print()
    checks = [
        root / "scripts/podman_build.sh",
        root / "scripts/podman_run.sh",
        root / "scripts/podman_stop.sh",
        root / "scripts/server_deploy.sh",
        root / "scripts/server_setup.sh",
    ]
    all_clean = True
    for p in checks:
        if not p.exists():
            continue
        raw = p.read_bytes()
        has_crlf = b"\r\n" in raw
        has_cr   = b"\r" in raw
        clean = not has_crlf and not has_cr
        if not clean:
            all_clean = False
        print(f"  {'OK' if clean else 'CRLF!'}  {p.relative_to(root)}")

    hdr("Done")
    print(f"  Files converted : {converted}")
    print(f"  Files already LF: {skipped}")
    print()
    if all_clean:
        print("  All scripts are LF-clean. Now run:")
        print()
        print("    bash scripts/podman_build.sh")
        print("    bash scripts/podman_run.sh")
        print()
        print("  Or use sh (works on all systems):")
        print()
        print("    sh scripts/podman_build.sh")
        print("    sh scripts/podman_run.sh")
    else:
        print("  WARNING: some files still have CRLF.")
        print("  Re-run this script or use dos2unix:")
        print("    sudo apt install dos2unix")
        print("    dos2unix scripts/*.sh")
    print()
    print("  Permanent fix -- add to your .gitattributes:")
    print("    * text=auto eol=lf")
    print("    *.sh text eol=lf")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert CRLF to LF in all project text files")
    parser.add_argument("--path", default=".",
                        help="Project root (default: current dir)")
    args = parser.parse_args()
    root = Path(args.path).resolve()
    if not (root / "backend").exists():
        print(f"WARNING: {root} may not be project root. Continue? [y/N] ",
              end="")
        if input().strip().lower() != "y":
            sys.exit(0)
    build(root)

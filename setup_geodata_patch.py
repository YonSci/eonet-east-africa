"""
Patches geoData.js with real country shapes
and updates DistrictLayer.jsx with a network error handler
"""
import sys
from pathlib import Path

def build(root):
    fe = root / "frontend"

    # 1. Replace geoData.js
    source_candidates = [
        root / "geoData.js",
        fe / "src/api/geoData.js",
    ]
    source_path = next((p for p in source_candidates if p.exists()), None)
    if source_path is None:
        looked = "\n  - ".join(str(p) for p in source_candidates)
        raise FileNotFoundError(
            "Could not find source geoData.js. Looked in:\n  - " + looked
        )

    src = source_path.read_bytes()
    target = fe / "src/api/geoData.js"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(src)
    print("  [+] updated  frontend/src/api/geoData.js (real country shapes)")
    print(f"      source: {source_path}")

    # 2. Patch DistrictLayer.jsx -- add error message when network blocks GADM
    dl = fe / "src/components/DistrictLayer.jsx"
    if dl.exists():
        txt = dl.read_text(encoding="utf-8")
        old = "        setError('Could not load district boundaries: ' + err.message)"
        new = ("        const isBlocked = err.name === 'AbortError' || "
               "err.message.includes('Failed') || err.message.includes('NetworkError')\n"
               "        setError(isBlocked\n"
               "          ? 'District boundaries require internet access to geodata.ucdavis.edu. '\n"
               "            + 'Try on a mobile hotspot or open network.'\n"
               "          : 'Could not load district boundaries: ' + err.message)")
        if old in txt:
            dl.write_bytes(txt.replace(old, new, 1).encode("utf-8"))
            print("  [~] patched  frontend/src/components/DistrictLayer.jsx (network error msg)")
        else:
            print("  SKIP DistrictLayer (marker not found)")

    # 3. Verify no CRLF
    for f in [target, dl]:
        if f and f.exists():
            raw = f.read_bytes()
            ok = b'\r\n' not in raw
            print(f"  {'LF-OK' if ok else 'CRLF!'} {f.name}")

    print()
    print("Done. Restart Vite: cd frontend && npm run dev")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--path", default=".")
    a = p.parse_args()
    root = Path(a.path).resolve()
    build(root)

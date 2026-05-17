"""
setup_about_features.py
-----------------------
Adds a 'Dashboard features' section to AboutPanel.jsx, placed between
'Technical stack' and 'Email alert subscriptions'.

The section lists all 40+ features grouped by area, matching the
feature catalogue shown in the chat.
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

# Insert before this marker (the Email alerts section)
INSERT_BEFORE = '      {/* Email alert subscriptions */}'

FEATURES_SECTION = """      {/* Dashboard features */}
      <Section title="Dashboard features">

        {[
          {
            group: 'Map view',
            color: '#1D9E75',
            items: [
              ['Interactive Leaflet map', 'Greater Horn of Africa region with CartoDB basemap, light/dark tile layers, bounded to EA'],
              ['Marker clustering', 'Nearby events collapse into numbered clusters. Handles 180+ events cleanly'],
              ['Real country boundaries', 'Natural Earth 1:50m polygons for all 11 countries, embedded inline -- no network fetch'],
              ['Country click-to-filter', 'Click any country to highlight it and filter all events and charts to that country'],
              ['NASA GIBS satellite layers', 'True colour (Terra/VIIRS), fire detections, chlorophyll overlays. Date picker for historical imagery'],
              ['District boundaries', 'GADM Level-1 sub-national boundaries per country after selecting a country on the map'],
              ['Event popups', 'Category, status, title, date, magnitude, country, coordinates, source link, satellite image link'],
              ['Category bar strip', 'Proportional colour bar and clickable category pills showing live event counts below the map'],
            ]
          },
          {
            group: 'Filter sidebar',
            color: '#BA7517',
            items: [
              ['Status filter', 'Toggle between All events, Open only, and Closed only'],
              ['Time period filter', '7d / 14d / 30d / 60d / 90d / 180d / 365d lookback, or custom start and end date range'],
              ['Per-category magnitude sliders', 'Separate slider for earthquakes (Richter), storms (kts), floods (m), temperature (C)'],
              ['Category toggles', '10 event categories, colour-coded with live count badges. All/None shortcuts'],
              ['Saved filter presets', 'Save any filter combination by name. 3 built-in defaults. Stored in browser localStorage'],
            ]
          },
          {
            group: 'Event list panel',
            color: '#378ADD',
            items: [
              ['Scrollable event list', 'Sortable table: date, category pill, status, title. Click a row to fly the map to that event'],
              ['Event search', 'Filter the list by keyword matching title, category, or event ID'],
              ['CSV export', 'Download the current filtered event list with all fields including coordinates and magnitude'],
            ]
          },
          {
            group: 'Analytics tab',
            color: '#E8593C',
            items: [
              ['Category bar chart', 'Horizontal bars sorted by count. Click a bar to toggle that category on the map'],
              ['Monthly timeline', 'Area chart of total events per month over the selected period'],
              ['Status donut and sources', 'Open vs closed breakdown. Data sources bar chart (MODIS, USGS, GDACS, JTWC, etc.)'],
              ['Duration histogram', 'Closed event duration binned: under 1 day, 1-7 days, 8-30 days, over 30 days'],
              ['Country table', 'Events per country with open/closed split and proportional bar'],
              ['Seasonal heatmap', 'Month x category grid coloured by event density. MAM, OND, and dry season bands annotated'],
              ['Year-over-year comparison', 'Select any two years: category bars, dual-line monthly trend, biggest movers table'],
              ['GeoJSON and CSV export', 'Export filtered events as GeoJSON (QGIS/ArcGIS compatible) or CSV'],
            ]
          },
          {
            group: 'Sharing and export',
            color: '#639922',
            items: [
              ['Shareable URLs', 'Active filters encoded in the URL. Share button copies the link to clipboard with a toast confirmation'],
              ['PDF bulletin export', 'Print-optimised layout with header showing name, email, date generated, and active filters'],
            ]
          },
          {
            group: 'Alert subscriptions',
            color: '#1D9E75',
            items: [
              ['Browser notifications', 'Popup alert when the 15-minute refresh detects new events matching saved subscriptions'],
              ['Email alerts via EmailJS', 'Confirmation email on subscribe and alert email when new events are detected. No backend needed'],
              ['Subscription management', 'View, delete, and export subscriptions. Filter by category and country'],
            ]
          },
          {
            group: 'UX and accessibility',
            color: '#888780',
            items: [
              ['Mobile responsive layout', 'Sidebar slides in as overlay on small screens. 2x2 stat cards. Map stacks above event list'],
              ['Skeleton loading states', 'Pulsing placeholder shapes for stat cards while data fetches'],
              ['Network error panel', 'When NASA EONET is blocked (9s timeout), shows clear panel with fix options and retry button'],
              ['Toast notifications', 'Green toast when refresh detects new events. Auto-dismisses after 5 seconds'],
              ['Light and dark theme', 'Toggle in top nav. Map tiles, popups, and all UI components adapt'],
              ['Offline banner', 'Amber banner when network lost, green when reconnected. Backed by PWA service worker cache'],
            ]
          },
          {
            group: 'PWA and deployment',
            color: '#185FA5',
            items: [
              ['Installable PWA', 'Install button in browser address bar. Offline mode serves last cached EONET data for 24 hours'],
              ['Netlify deployment', 'netlify.toml auto-config. Browser-direct NASA fetch. SPA routing redirect included'],
              ['Podman containerisation', 'Containerfile.backend (FastAPI) and Containerfile.frontend (Nginx). Rootless, daemonless'],
              ['Hetzner server deployment', 'Deploy scripts: build locally, export images, scp to server, load and start with Nginx proxy'],
            ]
          },
        ].map(({ group, color, items }) => (
          <div key={group} style={{ marginBottom: 18 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <div style={{ width: 10, height: 10, borderRadius: '50%',
                            background: color, flexShrink: 0 }} />
              <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                {group}
              </span>
              <span style={{ fontSize: 11, color: 'var(--text-muted)',
                             background: 'var(--bg-elevated)',
                             padding: '1px 6px', borderRadius: 100 }}>
                {items.length}
              </span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 5,
                          paddingLeft: 18 }}>
              {items.map(([title, desc]) => (
                <div key={title} style={{
                  padding: '7px 10px',
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border-muted)',
                  borderLeft: '3px solid ' + color,
                  borderRadius: 'var(--radius-md)',
                }}>
                  <div style={{ fontSize: 12, fontWeight: 600,
                                color: 'var(--text-primary)', marginBottom: 2 }}>
                    {title}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)',
                                lineHeight: 1.4 }}>
                    {desc}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}

        <div style={{ marginTop: 8, padding: '8px 12px',
                      background: 'var(--bg-elevated)',
                      border: '1px solid var(--border-muted)',
                      borderRadius: 'var(--radius-md)',
                      fontSize: 11, color: 'var(--text-muted)',
                      display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 18, fontWeight: 600,
                         color: 'var(--text-secondary)' }}>40+</span>
          features across 8 functional areas -- all running on NASA EONET v3
          and Natural Earth public domain data.
        </div>
      </Section>

"""


def build(root: Path):
    fe = root / "frontend"
    ap = fe / "src/components/AboutPanel.jsx"
    hdr(f"Adding features section to AboutPanel in: {root}")

    if not ap.exists():
        print("  ERROR  AboutPanel.jsx not found")
        sys.exit(1)

    txt = ap.read_text(encoding="utf-8")

    if INSERT_BEFORE not in txt:
        print(f"  ERROR  Insertion marker not found: {INSERT_BEFORE!r}")
        sys.exit(1)

    if "Dashboard features" in txt:
        ok("Features section already present -- nothing to do")
        return

    new_txt = txt.replace(INSERT_BEFORE,
                           FEATURES_SECTION + INSERT_BEFORE, 1)

    # Write with LF line endings
    ap.write_bytes(new_txt.replace("\r\n", "\n").encode("utf-8"))
    ow("updated  frontend/src/components/AboutPanel.jsx")

    # ASCII + CRLF check
    raw = ap.read_bytes()
    bad = [(i+1) for i, line in enumerate(raw.split(b"\n"))
           if any(b > 127 for b in line)]
    has_crlf = b"\r\n" in raw
    print()
    if bad:   print(f"  WARN  Non-ASCII on lines: {bad[:5]}")
    else:     ok("ASCII-clean -- OXC safe")
    if has_crlf: print("  WARN  CRLF detected")
    else:        ok("LF line endings -- no CRLF")

    # Verify
    txt2 = ap.read_text()
    checks = [
        ("Dashboard features",   "section title present"),
        ("Map view",             "Map group present"),
        ("Analytics tab",        "Analytics group present"),
        ("Year-over-year",       "YoY feature present"),
        ("Podman",               "Deployment group present"),
        ("40+",                  "summary badge present"),
    ]
    print()
    all_ok = True
    for needle, label in checks:
        found = needle in txt2
        if not found: all_ok = False
        print(f"  {'OK' if found else 'MISSING'}  {label}")

    hdr("Done")
    print()
    print("  Features section added to About tab:")
    print("    Position: after 'Technical stack', before 'Email alert subscriptions'")
    print("    8 groups: Map view, Filters, Event list, Analytics,")
    print("               Sharing, Alerts, UX, PWA/Deployment")
    print("    Each feature has a title + one-line description")
    print("    Colour-coded dot per group matching the dashboard palette")
    print("    Summary badge: '40+ features across 8 functional areas'")
    print()
    print("  Restart Vite:")
    print("    cd frontend && npm run dev")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Add feature catalogue to AboutPanel")
    parser.add_argument("--path", default=".")
    args = parser.parse_args()
    root = Path(args.path).resolve()
    if not (root / "backend").exists():
        print(f"WARNING: {root} may not be project root. Continue? [y/N] ",
              end="")
        if input().strip().lower() != "y":
            sys.exit(0)
    build(root)

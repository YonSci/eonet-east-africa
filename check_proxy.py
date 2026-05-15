"""
check_proxy.py
Run this to detect your Windows proxy settings and test the EONET connection.

Usage:
    python check_proxy.py
"""
import winreg
import socket
import urllib.request
import os

print("\n" + "="*55)
print("  Network & Proxy Diagnostic")
print("="*55)

# ── 1. Windows registry proxy ─────────────────────────────
print("\n[1] Windows Internet Settings (registry)")
try:
    reg = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
    )
    proxy_enable, _ = winreg.QueryValueEx(reg, "ProxyEnable")
    print(f"    ProxyEnable : {proxy_enable}  ({'ON' if proxy_enable else 'OFF'})")
    try:
        proxy_server, _ = winreg.QueryValueEx(reg, "ProxyServer")
        print(f"    ProxyServer : {proxy_server}")
    except FileNotFoundError:
        print("    ProxyServer : (not set)")
    try:
        auto_config, _ = winreg.QueryValueEx(reg, "AutoConfigURL")
        print(f"    AutoConfigURL: {auto_config}")
    except FileNotFoundError:
        print("    AutoConfigURL: (not set)")
except Exception as e:
    print(f"    Error reading registry: {e}")

# ── 2. Environment variables ──────────────────────────────
print("\n[2] Environment variable proxies")
for var in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY"]:
    val = os.environ.get(var)
    if val:
        print(f"    {var} = {val}")
    else:
        print(f"    {var} = (not set)")

# ── 3. urllib auto-detected proxies ──────────────────────
print("\n[3] urllib auto-detected proxies")
proxies = urllib.request.getproxies()
if proxies:
    for k, v in proxies.items():
        print(f"    {k} = {v}")
else:
    print("    (none detected)")

# ── 4. Raw TCP connection test ────────────────────────────
print("\n[4] Raw TCP connection to eonet.gsfc.nasa.gov:443")
try:
    sock = socket.create_connection(("eonet.gsfc.nasa.gov", 443), timeout=8)
    sock.close()
    print("    SUCCESS - port 443 is reachable")
except socket.timeout:
    print("    TIMEOUT  - port 443 blocked by firewall")
except Exception as e:
    print(f"    FAILED   - {e}")

# ── 5. Try alternate NASA port 80 ─────────────────────────
print("\n[5] Raw TCP connection to eonet.gsfc.nasa.gov:80")
try:
    sock = socket.create_connection(("eonet.gsfc.nasa.gov", 80), timeout=8)
    sock.close()
    print("    SUCCESS - port 80 is reachable")
except socket.timeout:
    print("    TIMEOUT  - port 80 also blocked")
except Exception as e:
    print(f"    FAILED   - {e}")

# ── 6. Test a known-open site ─────────────────────────────
print("\n[6] TCP connection to google.com:443 (sanity check)")
try:
    sock = socket.create_connection(("google.com", 443), timeout=8)
    sock.close()
    print("    SUCCESS - general internet works")
except Exception as e:
    print(f"    FAILED   - {e}")

print("\n" + "="*55)
print("  Paste the full output above when reporting the issue.")
print("="*55 + "\n")

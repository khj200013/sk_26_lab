import platform, subprocess, re, shutil

def _run(cmd):
    try: 
        return subprocess.check_output(cmd, shell=True, text=True)
    except Exception: 
        return ""

def scan():
    sys = platform.system().lower()
    if sys == "windows": return scan_windows()
    elif sys == "darwin": return []  # mac 제외
    else: return []  # linux 제외

def _kv(block, keys):
    for k in keys:
        m = re.search(rf"(?im)^\s*{re.escape(k)}\s*:\s*(.+)$", block)
        if m: return m.group(1).strip()
    return ""

def scan_windows():
    out = _run("netsh wlan show networks mode=bssid")
    if not out.strip(): return []
    # Split per SSID section
    blocks = re.split(r"\nSSID \d+ :", out)
    entries = []
    for blk in blocks[1:]:
        try:
            ssid = blk.splitlines()[0].strip()
            # authentication/encryption (KO/EN)
            auth = _kv(blk, ["Authentication", "인증"])
            enc = _kv(blk, ["Encryption", "암호화"])
            cap = ",".join([x for x in [auth, enc] if x])
            # each BSSID
            for b in re.split(r"\n\s*BSSID \d+\s*:", blk)[1:]:
                bssid = b.splitlines()[0].strip()
                # Signal/신호
                sig = _kv(b, ["Signal", "신호"])
                m = re.search(r"(\d+)\s*%", sig or "")
                signal_dbm = int(int(m.group(1))/2 - 100) if m else -70
                # Channel/채널
                chs = _kv(b, ["Channel", "채널"])
                chm = re.search(r"(\d+)", chs or "")
                ch = int(chm.group(1)) if chm else -1
                entries.append({
                    "ssid": ssid, "bssid": bssid, "capabilities": cap,
                    "signal": signal_dbm, "channel": ch
                })
        except Exception:
            continue
    return entries

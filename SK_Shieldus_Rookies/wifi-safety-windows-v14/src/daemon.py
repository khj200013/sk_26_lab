
import sys, time, platform, re, argparse, subprocess, os

# ---------- helper: run command with system codepage ----------
def _run(cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, shell=True, text=True)
    except Exception:
        return ""

# ---------- notifications ----------
def notify(title, message, severity='info'):
    # Prefer Windows Toast (winotify) for real popup
    try:
        from winotify import Notification, audio
        base = os.path.join(os.path.dirname(__file__), "..", "assets"); icon_path = os.path.join(base, 'icon_red.png' if severity=='danger' else ('icon_orange.png' if severity=='warn' else 'icon.png'))
        toast = Notification(app_id="Wi‑Fi Safety", title=title, msg=message, icon=icon_path, duration="short")
        toast.set_audio(audio.Default, loop=False)
        toast.show()
        return
    except Exception:
        pass
    # Fallback: win10toast
    try:
        from win10toast import ToastNotifier
        ToastNotifier().show_toast(title, message, duration=6, threaded=True)
        return
    except Exception:
        pass
    # Fallback: plyer
    try:
        from plyer import notification as plyer_notif
        plyer_notif.notify(title=title, message=message, app_name="Wi‑Fi Safety", timeout=6)
        return
    except Exception:
        pass
    # Last resort: console
    print(f"[알림] {title}: {message}")

from services.seed_loader import load_weights, load_oui, load_patterns
from services.score_engine import score_entry

def _field(text, keys):
    for k in keys:
        m = re.search(rf"(?im)^\s*{re.escape(k)}\s*:\s*(.+)$", text)
        if m:
            return m.group(1).strip()
    return ""

# ---------- current network fetchers ----------
def current_windows():
    out = _run("netsh wlan show interfaces")
    if not out.strip():
        return None
    state = _field(out, ["State", "상태"])
    if not state or not (("connect" in state.lower()) or ("연결" in state)):
        return None
    ssid   = _field(out, ["SSID"])
    bssid  = _field(out, ["BSSID"])
    auth   = _field(out, ["Authentication", "인증"])
    cipher = _field(out, ["Cipher", "암호화"])
    signal = _field(out, ["Signal", "신호"])
    channel= _field(out, ["Channel", "채널"])

    sig_pct_m = re.search(r"(\d+)\s*%", signal or "")
    if sig_pct_m:
        signal_dbm = int(int(sig_pct_m.group(1)) / 2 - 100)
    else:
        sig_dbm_m = re.search(r"(-?\d+)\s*dBm", signal or "", re.I)
        signal_dbm = int(sig_dbm_m.group(1)) if sig_dbm_m else -70

    ch_m = re.search(r"(\d+)", channel or "")
    ch = int(ch_m.group(1)) if ch_m else -1
    cap = ",".join([x for x in [auth, cipher] if x])

    return {"ssid": ssid, "bssid": bssid, "capabilities": cap, "signal": signal_dbm, "channel": ch}

def current_macos():  # not used in Windows package
    return None

def current_linux():  # not used in Windows package
    return None

def get_current():
    sysname = platform.system().lower()
    if sysname == "windows":
        return current_windows()
    return None

# ---------- main loop ----------
def main():
    ap = argparse.ArgumentParser(description="Wi‑Fi Safety Background Notifier")
    ap.add_argument("--interval", type=int, default=15, help="체크 주기(초)")
    ap.add_argument("--repeat_danger_min", type=int, default=5, help="위험 알림 반복 주기(분)")
    ap.add_argument("--repeat_warn_min", type=int, default=30, help="주의 알림 반복 주기(분)")
    ap.add_argument("--threshold", type=int, default=50, help="(구버전 옵션) 무시됨: 현재는 <50 위험, <80 주의로 동작")
    ap.add_argument("--once", action="store_true", help="한 번만 체크하고 종료")
    ap.add_argument("--debug", action="store_true", help="원시 출력 디버그")
    args = ap.parse_args()

    weights = load_weights()
    oui = load_oui()
    ssid_pats, kiosk, certified = load_patterns()

    last = None


    last_notified = {}  # key=(ssid, severity) -> epoch seconds

    while True:
        cur = get_current()
        if cur:
            result = score_entry(cur, weights, oui, ssid_pats, certified)
            summary = f"{result['ssid']} | {result['grade']} {result['score']}점 | " + " · ".join(result.get('reasons',[]))
            print("[현재] " + summary)
            key = (result["ssid"], result["grade"])
            if key != last:
                if result['score'] < 50:
                    notify('위험한 Wi‑Fi', f"{result['ssid']}: {result['grade']} {result['score']}점", severity='danger')
                elif result['score'] < 80:
                    notify('주의 Wi‑Fi', f"{result['ssid']}: {result['grade']} {result['score']}점", severity='warn')
            last = key
        else:
            print("[현재] 연결된 Wi‑Fi 없음")
            if args.debug:
                print("--- netsh wlan show interfaces ---")
                print(_run("netsh wlan show interfaces"))

        if args.once:
            break
        time.sleep(args.interval)

if __name__ == "__main__":
    main()

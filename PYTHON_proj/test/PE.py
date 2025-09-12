import os, sys, time, json, tempfile, subprocess, platform, shutil, locale
from datetime import datetime

# Windows 전용
if platform.system().lower() != "windows":
    print("This script runs on Windows only.")
    sys.exit(1)

import winreg  # stdlib

# --------------------------------------------------------------------
# 공통 경로/설정
# --------------------------------------------------------------------
OUT_DIR = os.path.join(tempfile.gettempdir(), "reglab_outputs")
STAMP   = datetime.now().strftime("%Y%m%d_%H%M%S")
CMD_OUT = os.path.join(OUT_DIR, f"cmd_{STAMP}.txt")
PS_OUT  = os.path.join(OUT_DIR, f"ps_{STAMP}.txt")
TIMEOUT = 30  # per-command seconds

# HKCU 샌드박스 루트 (여기만 조작)
SANDBOX_ROOT = r"Software\RegLab"   # relative to HKEY_CURRENT_USER
# PowerShell 스크립트 화이트리스트 루트 (PE.py 기준 상대경로 → test/powershell)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PS_SAFE_ROOT = os.path.join(BASE_DIR, "powershell")

os.makedirs(OUT_DIR, exist_ok=True)

# --------------------------------------------------------------------
# 레지스트리 유틸
# --------------------------------------------------------------------
def _open_writable(hive, subkey):
    # 없으면 생성
    return winreg.CreateKeyEx(hive, subkey, 0, winreg.KEY_ALL_ACCESS)

def ensure_key(hive, subkey, simulate):
    print(f"[REG] CREATEKEY: HKCU\\{subkey}")
    if not simulate:
        k = _open_writable(hive, subkey)
        winreg.CloseKey(k)

def set_value(hive, subkey, name, data, kind, simulate):
    preview = data if not isinstance(data, (bytes, bytearray)) else f"bytes({len(data)})"
    if isinstance(data, list):
        preview = "[" + ",".join(map(str, data)) + "]"
    print(f"[REG] SET: HKCU\\{subkey}  {name} ({kind}) = {preview}")
    if not simulate:
        k = _open_writable(hive, subkey)
        winreg.SetValueEx(k, name, 0, kind, data)
        winreg.CloseKey(k)

def get_value(hive, subkey, name):
    try:
        k = winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ)
        val, kind = winreg.QueryValueEx(k, name)
        winreg.CloseKey(k)
        return val, kind
    except FileNotFoundError:
        return None, None
    except OSError:
        return None, None

def modify_dword(hive, subkey, name, add, simulate):
    current, kind = get_value(hive, subkey, name)
    if current is None or kind != winreg.REG_DWORD:
        current = 0
    nxt = int(current) + int(add)
    print(f"[REG] MODIFY DWORD: {name} {current} -> {nxt}")
    if not simulate:
        k = _open_writable(hive, subkey)
        winreg.SetValueEx(k, name, 0, winreg.REG_DWORD, nxt)
        winreg.CloseKey(k)

def rename_value(hive, subkey, src_name, dst_name, simulate):
    val, kind = get_value(hive, subkey, src_name)
    print(f"[REG] RENAME VALUE: {src_name} -> {dst_name} ({'unknown' if kind is None else kind})")
    if not simulate and val is not None:
        k = _open_writable(hive, subkey)
        winreg.SetValueEx(k, dst_name, 0, kind, val)
        try:
            winreg.DeleteValue(k, src_name)
        except FileNotFoundError:
            pass
        winreg.CloseKey(k)

def delete_value(hive, subkey, name, simulate):
    print(f"[REG] DELETE VALUE: {name} @ HKCU\\{subkey}")
    if not simulate:
        try:
            k = _open_writable(hive, subkey)
            winreg.DeleteValue(k, name)
            winreg.CloseKey(k)
        except FileNotFoundError:
            pass

def list_subkeys(hive, subkey):
    try:
        k = winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ)
    except FileNotFoundError:
        return []
    subs = []
    i = 0
    while True:
        try:
            name = winreg.EnumKey(k, i)
            subs.append(name)
            i += 1
        except OSError:
            break
    winreg.CloseKey(k)
    return subs

def delete_key_tree(hive, subkey, simulate):
    print(f"[REG] DELETE KEY TREE: HKCU\\{subkey}")
    if not simulate:
        # 재귀적으로 하위키 삭제
        for child in list_subkeys(hive, subkey):
            delete_key_tree(hive, subkey + "\\" + child, simulate)
        try:
            winreg.DeleteKey(hive, subkey)
        except FileNotFoundError:
            pass

def append_to_multisz(hive, subkey, name, item, simulate):
    cur, kind = get_value(hive, subkey, name)
    if not (isinstance(cur, list) and kind == winreg.REG_MULTI_SZ):
        cur = []
    next_list = list(dict.fromkeys(cur + [item]))  # 중복 제거하며 append
    print(f"[REG] MULTI_SZ APPEND: {name} += \"{item}\" ({len(cur)}->{len(next_list)})")
    if not simulate:
        k = _open_writable(hive, subkey)
        winreg.SetValueEx(k, name, 0, winreg.REG_MULTI_SZ, next_list)
        winreg.CloseKey(k)

# --------------------------------------------------------------------
# 프로세스 유틸
# --------------------------------------------------------------------
def _smart_decode(b: bytes) -> str:
    if not b:
        return ""
    # BOM 우선
    if b.startswith(b'\xff\xfe'):
        try: return b.decode('utf-16le')
        except: pass
    if b.startswith(b'\xfe\xff'):
        try: return b.decode('utf-16be')
        except: pass
    if b.startswith(b'\xef\xbb\xbf'):
        try: return b.decode('utf-8-sig')
        except: pass
    # 널바이트 많으면 UTF-16 가정
    if b.count(b'\x00') > max(1, len(b)//6):
        try: return b.decode('utf-16le')
        except: pass
    # 일반 순서: utf-8 -> 로캘 -> mbcs
    for enc in ('utf-8', locale.getpreferredencoding(False), 'mbcs'):
        try:
            return b.decode(enc)
        except:
            pass
    return b.decode('utf-8', errors='replace')

def run_process(file, args, timeout=TIMEOUT):
    try:
        p = subprocess.Popen(
            [file] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        try:
            so, se = p.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            p.kill()
            so, se = p.communicate()
            se = (se or b"") + f"\n[TIMEOUT] {timeout}s exceeded.".encode()

        code = p.returncode
        so = _smart_decode(so or b"")
        se = _smart_decode(se or b"")

        return code, so, se
    except Exception as e:
        return -1, "", f"[ERROR] {type(e).__name__}: {e}"
# --------------------------------------------------------------------
# (1) Registry: 10개 이상 생성/변경/삭제 (샌드박스만)
# --------------------------------------------------------------------
def do_registry_playground(simulate=True):
    hive = winreg.HKEY_CURRENT_USER
    root = SANDBOX_ROOT
    print(f"[REG] Target root: HKCU\\{root}")

    # 안전한 샌드박스 루트 생성
    ensure_key(hive, root, simulate)

    # 1. 문자열 값
    set_value(hive, root, "StringValue", "Hello, RegLab!", winreg.REG_SZ, simulate)

    # 2. DWORD
    set_value(hive, root, "DwordValue", 42, winreg.REG_DWORD, simulate)

    # 3. QWORD
    set_value(hive, root, "QwordValue", 1234567890123456789, winreg.REG_QWORD, simulate)

    # 4. EXPAND_SZ
    set_value(hive, root, "ExpandValue", r"%TEMP%\RegLab", winreg.REG_EXPAND_SZ, simulate)

    # 5. MULTI_SZ
    set_value(hive, root, "MultiValue", ["alpha","beta","gamma"], winreg.REG_MULTI_SZ, simulate)

    # 6. BINARY
    set_value(hive, root, "BinaryValue", bytes([0xDE,0xAD,0xBE,0xEF]), winreg.REG_BINARY, simulate)

    # 7. DWORD 수정(기존 +5)
    modify_dword(hive, root, "DwordValue", 5, simulate)

    # 8. 값 이름 변경 (copy+delete)
    rename_value(hive, root, "StringValue", "StringValue_Old", simulate)

    # 9. 하위키 Child1 생성 + 값
    child1 = root + r"\Child1"
    ensure_key(hive, child1, simulate)
    set_value(hive, child1, "Note", "child key here", winreg.REG_SZ, simulate)

    # 10. 하위키 Child2 생성 + 값 -> 트리 삭제
    child2 = root + r"\Child2"
    ensure_key(hive, child2, simulate)
    set_value(hive, child2, "Flag", 1, winreg.REG_DWORD, simulate)
    delete_key_tree(hive, child2, simulate)

    # 11. 특정 값 삭제
    delete_value(hive, root, "BinaryValue", simulate)

    # 12. MultiString에 항목 추가
    append_to_multisz(hive, root, "MultiValue", "delta", simulate)

    print("[REG] 12+ operations planned/applied under HKCU\\Software\\RegLab")

def undo_sandbox():
    print(f"[REG] CLEANUP: HKCU\\{SANDBOX_ROOT}")
    delete_key_tree(winreg.HKEY_CURRENT_USER, SANDBOX_ROOT, simulate=False)

# --------------------------------------------------------------------
# (2) PowerShell 5개 실행 (화이트리스트 루트 내부만)
#     - 레지스트리 무관 작업만 예시로 선택
# --------------------------------------------------------------------
def run_powershell_batch(script_paths, out_file):
    with open(out_file, "w", encoding="utf-8", newline="") as sw:
        for path in script_paths:
            try:
                full = os.path.abspath(path)
                safe_root = os.path.abspath(PS_SAFE_ROOT)
                if not full.lower().startswith(safe_root.lower()):
                    sw.write(f"[SKIP] Outside safe root: {full}\n")
                    sw.flush()
                    continue
                if not os.path.exists(full):
                    sw.write(f"[MISS] {full}\n")
                    sw.flush()
                    continue

                # run_powershell_batch 내부의 args 생성 부분만 교체
                args = ["-NoProfile", "-NonInteractive", "-ExecutionPolicy", "RemoteSigned", "-Command",
                    # 콘솔 입/출력 UTF-8 강제 후 스크립트 실행
                    f"[Console]::InputEncoding=[Text.Encoding]::UTF8; "
                    f"[Console]::OutputEncoding=[Text.Encoding]::UTF8; "
                    f"& '{full}'"
                ]
                sw.write("="*80 + "\n")
                sw.write(f"PS> {full}\n")
                code, so, se = run_process("powershell.exe", args, TIMEOUT)
                sw.write("[STDOUT]\n")
                sw.write(so or "")
                if se and se.strip():
                    sw.write("\n[STDERR]\n")
                    sw.write(se)
                sw.write(f"\n[EXIT] {code}\n")
                sw.flush()
            except Exception as e:
                sw.write(f"[ERROR] {type(e).__name__}: {e}\n")
                sw.flush()

# --------------------------------------------------------------------
# (3) CMD 10개 정보수집 -> 텍스트 저장
# --------------------------------------------------------------------
def run_cmd_batch(commands, out_file):
    with open(out_file, "w", encoding="utf-8", newline="") as sw:
        for cmd in commands:
            sw.write("="*80 + "\n")
            sw.write(f"$ {cmd}  [{datetime.now().strftime('%H:%M:%S')}]\n")
            sw.write("-"*80 + "\n")
            code, so, se = run_process("cmd.exe", ["/c", cmd], TIMEOUT)
            sw.write("[STDOUT]\n")
            sw.write(so or "")
            if se and se.strip():
                sw.write("\n[STDERR]\n")
                sw.write(se)
            sw.write(f"\n[EXIT] {code}\n")
            sw.flush()

# --------------------------------------------------------------------
# 메인
# --------------------------------------------------------------------
def main():
    simulate = True
    undo = False
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == "--apply":
            simulate = False
        elif sys.argv[1].lower() == "--undo":
            undo = True

    print(f"[Mode] {'UNDO' if undo else ('SIMULATION' if simulate else 'APPLY')}")
    print(f"[Out ] {OUT_DIR}")

    if undo:
        undo_sandbox()
        print("[UNDO] Completed.")
        return

    # 1) Registry 10개+ (샌드박스)
    do_registry_playground(simulate=simulate)

    # 2) PowerShell 5개 (화이트리스트 내 스크립트만)
    ps_scripts = [
        os.path.join(PS_SAFE_ROOT, "file_search.ps1"),   # 예: Get-Process | Select Name,Id
        os.path.join(PS_SAFE_ROOT, "network_info.ps1"),   # 예: Get-Service | Select Name,Status
        os.path.join(PS_SAFE_ROOT, "process_control.ps1"),   # 예: Get-ScheduledTask | Select TaskName,State
        os.path.join(PS_SAFE_ROOT, "scheduled_task.ps1"),   # 예: Get-CimInstance Win32_StartupCommand
        os.path.join(PS_SAFE_ROOT, "user_info.ps1"),   # 예: Get-WmiObject Win32_PnPSignedDriver
    ]
    run_powershell_batch(ps_scripts, PS_OUT)

    # 3) CMD 10개 수집
    cmds = [
        "ipconfig /all",
        "systeminfo",
        "tasklist /v",
        "whoami /all",
        "netstat -ano",
        "wmic qfe list full",
        "driverquery /v",
        "schtasks /query /fo LIST /v",
        "sc query type= service state= all",
        "wmic os get Caption,Version,BuildNumber /value",
    ]
    run_cmd_batch(cmds, CMD_OUT)

    print("[DONE]")
    print(f"- CMD output: {CMD_OUT}")
    print(f"- PS  output: {PS_OUT}")

if __name__ == "__main__":
    main()

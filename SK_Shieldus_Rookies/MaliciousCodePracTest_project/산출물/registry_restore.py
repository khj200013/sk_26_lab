import os
import sys
import subprocess
import winreg

print("🔧 레지스트리 원복 도구를 시작합니다! 🛠️")
print("-" * 50)

def delete_registry_value(key_path, value_name, hive=winreg.HKEY_CURRENT_USER):
    """레지스트리 값 삭제"""
    try:
        key = winreg.OpenKeyEx(hive, key_path, 0, winreg.KEY_WRITE)
        winreg.DeleteValue(key, value_name)
        winreg.CloseKey(key)
        print(f"✅ 레지스트리 값 삭제 성공: '{hive}\\{key_path}'의 '{value_name}'")
        return True
    except FileNotFoundError:
        print(f"ℹ️ 레지스트리 값이 이미 없음: '{hive}\\{key_path}'의 '{value_name}'")
        return True
    except Exception as e:
        print(f"❌ 레지스트리 값 삭제 실패: '{hive}\\{key_path}'의 '{value_name}' - {e}")
        return False

def delete_registry_key(key_path, hive=winreg.HKEY_CURRENT_USER):
    """레지스트리 키 삭제"""
    try:
        winreg.DeleteKeyEx(hive, key_path)
        print(f"✅ 레지스트리 키 삭제 성공: '{hive}\\{key_path}'")
        return True
    except FileNotFoundError:
        print(f"ℹ️ 레지스트리 키가 이미 없음: '{hive}\\{key_path}'")
        return True
    except Exception as e:
        print(f"❌ 레지스트리 키 삭제 실패: '{hive}\\{key_path}' - {e}")
        return False

def restore_registry():
    """practice_PE.py에서 수정한 레지스트리들을 원복"""
    print("\n--- 레지스트리 원복 시작 ---")
    
    success_count = 0
    total_count = 0
    
    # 1. 시작 시 자동 실행 제거 (Report_Updater)
    print("\n1. 자동 실행 항목 제거 중...")
    total_count += 1
    if delete_registry_value(r"Software\Microsoft\Windows\CurrentVersion\Run", "Report_Updater"):
        success_count += 1
    
    # 2. CustomMalware 설정 키 전체 삭제
    print("\n2. CustomMalware 설정 키 삭제 중...")
    total_count += 1
    if delete_registry_key(r"Software\CustomMalware\Settings"):
        success_count += 1
    
    # 3. 방화벽 예외 설정 제거 (관리자 권한 필요)
    print("\n3. 방화벽 예외 설정 제거 중...")
    fake_malware_path = r"C:\Program Files\Common Files\malware.exe"
    firewall_key = r"SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy\StandardProfile\AuthorizedApplications\List"
    total_count += 1
    if delete_registry_value(firewall_key, fake_malware_path, winreg.HKEY_LOCAL_MACHINE):
        success_count += 1
    
    # 4. 가상 서비스 설정 제거 (관리자 권한 필요)
    print("\n4. 가상 서비스 설정 제거 중...")
    total_count += 1
    if delete_registry_key(r"SYSTEM\CurrentControlSet\Services\FakeDefenderSvc", winreg.HKEY_LOCAL_MACHINE):
        success_count += 1
    
    # 5. SystemInfo 키 전체 삭제
    print("\n5. SystemInfo 키 삭제 중...")
    total_count += 1
    if delete_registry_key(r"Software\SystemInfo"):
        success_count += 1
    
    # 6. BrowserSettings 키 전체 삭제
    print("\n6. BrowserSettings 키 삭제 중...")
    total_count += 1
    if delete_registry_key(r"Software\BrowserSettings"):
        success_count += 1
    
    # 7. NetworkConfig 키 전체 삭제
    print("\n7. NetworkConfig 키 삭제 중...")
    total_count += 1
    if delete_registry_key(r"Software\NetworkConfig"):
        success_count += 1
    
    print(f"\n--- 레지스트리 원복 완료 ---")
    print(f"✅ 성공: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 모든 레지스트리 항목이 성공적으로 원복되었습니다!")
    else:
        print("⚠️ 일부 항목 원복에 실패했습니다. 관리자 권한으로 실행해보세요.")

def cleanup_temp_files():
    """생성된 임시 파일들 정리"""
    print("\n--- 임시 파일 정리 ---")
    
    temp_dir = os.path.join(os.environ['TEMP'])
    files_to_clean = [
        'file_search.ps1',
        'user_info.ps1', 
        'network_info.ps1',
        'process_control.ps1',
        'scheduled_task.ps1',
        'ps_search_results.txt',
        'ps_user_info.txt',
        'ps_network_info.txt',
        'info.txt'
    ]
    
    cleaned_count = 0
    for filename in files_to_clean:
        file_path = os.path.join(temp_dir, filename)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"✅ 파일 삭제: {filename}")
                cleaned_count += 1
            else:
                print(f"ℹ️ 파일 없음: {filename}")
        except Exception as e:
            print(f"❌ 파일 삭제 실패: {filename} - {e}")
    
    print(f"\n총 {cleaned_count}개 파일이 정리되었습니다.")

def remove_scheduled_task():
    """작업 스케줄러에서 등록된 작업 제거"""
    print("\n--- 작업 스케줄러 정리 ---")
    
    task_name = "MalwareUpdater"
    try:
        # PowerShell 명령으로 작업 삭제
        command = f'powershell.exe -Command "Unregister-ScheduledTask -TaskName \'{task_name}\' -Confirm:$false"'
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ 작업 스케줄러 '{task_name}' 삭제 성공!")
        else:
            print(f"ℹ️ 작업 스케줄러 '{task_name}'가 이미 없거나 삭제 실패")
    except Exception as e:
        print(f"❌ 작업 스케줄러 삭제 중 오류: {e}")

def main():
    """메인 함수"""
    print("이 도구는 practice_PE.py에서 수정한 레지스트리를 원복합니다.")
    print("주의: 관리자 권한이 필요한 항목들이 있습니다.")
    
    response = input("\n계속 진행하시겠습니까? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("작업이 취소되었습니다.")
        return
    
    # 레지스트리 원복
    restore_registry()
    
    # 임시 파일 정리
    cleanup_temp_files()
    
    # 작업 스케줄러 정리
    remove_scheduled_task()
    
    print("\n" + "="*50)
    print("🎯 모든 정리 작업이 완료되었습니다!")
    print("시스템을 재부팅하면 모든 변경사항이 완전히 적용됩니다.")
    print("="*50)

if __name__ == "__main__":
    main()

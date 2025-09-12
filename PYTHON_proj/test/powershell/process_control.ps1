# PowerShell 스크립트 4: 프로세스 제어 (notepad.exe 종료 시도)
Write-Host "➡️ PowerShell 스크립트 4/5: notepad.exe 프로세스 종료 시도 중..."
try {
    $np = Get-Process -Name 'notepad' -ErrorAction SilentlyContinue
    if ($np) {
        $np | Stop-Process -Force
        Write-Host "   notepad.exe 종료 완료."
    } else {
        Write-Host "   notepad.exe 실행 중 아님."
    }
} catch {
    Write-Warning "   notepad.exe 종료 시도 실패: $_"
}

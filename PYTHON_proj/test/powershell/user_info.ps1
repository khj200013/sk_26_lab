# PowerShell 스크립트 2: 사용자 정보 수집
Write-Host "➡️ PowerShell 스크립트 2/5: 사용자 정보 수집 중..."
$Out = Join-Path $env:TEMP 'ps_user_info.txt'

try {
    whoami /all | Out-File -FilePath $Out -Encoding UTF8
    Write-Host "   whoami 정보: '$Out'에 저장됨."
} catch {
    Write-Warning "   사용자 정보 수집 중 오류 발생: $_"
}

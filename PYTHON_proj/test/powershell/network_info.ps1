# PowerShell 스크립트 3: 네트워크 정보 수집
Write-Host "➡️ PowerShell 스크립트 3/5: 네트워크 정보 수집 중..."
$Out = Join-Path $env:TEMP 'ps_network_info.txt'

try {
    Get-NetIPAddress |
        Select-Object IPAddress, InterfaceAlias, AddressFamily |
        Out-File -FilePath $Out -Encoding UTF8
    Write-Host "   네트워크 정보: '$Out'에 저장됨."
} catch {
    Write-Warning "   네트워크 정보 수집 중 오류 발생: $_"
}

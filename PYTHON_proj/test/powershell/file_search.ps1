# PowerShell 스크립트 1: 파일 검색
Write-Host "➡️ PowerShell 스크립트 1/5: 'password' 파일 검색 중..."
$Out = Join-Path $env:TEMP 'ps_search_results.txt'
$desktopPath = [Environment]::GetFolderPath('Desktop')

try {
    Get-ChildItem -Path $desktopPath -Filter '*password*' -Recurse -ErrorAction SilentlyContinue |
        Select-Object FullName, Length |
        Out-File -FilePath $Out -Encoding UTF8
    Write-Host "   검색 결과: '$Out'에 저장됨."
} catch {
    Write-Warning "   파일 검색 중 오류 발생: $_"
}

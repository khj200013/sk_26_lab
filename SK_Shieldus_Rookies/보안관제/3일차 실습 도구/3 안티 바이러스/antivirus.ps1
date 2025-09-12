# antivirus.ps1
#$OutputEncoding = [Console]::OutputEncoding
#TYPE .\antivirus.ps1 | PowerShell -noprofile -

# 시그니처 데이터베이스 로드
Write-Output ""
Write-Output ""

$oSignatures = Get-Content -Path "./database.txt"

Write-Output "===== 시그니처 목록 ====="
Write-Output $oSignatures
Write-Output "========================"
Write-Output ""

Function DoAction {
    # 현재 디렉터리의 모든 파일 검사
    Write-Output ""
    Write-Output "===== 바이러스 검사 ====="

    $oTargetFiles = Get-ChildItem -File

    foreach ($aTargetFile in $oTargetFiles) {
        $sFilePath = $aTargetFile.FullName
        $sFileName = $aTargetFile.Name

        if ($sFileName -ne "database.txt") {
            # 파일 전체 내용 읽기
            $sFileContent = Get-Content -Path $sFilePath -Raw

            # 파일의 해시 계산
            $sFileHash = Get-FileHash -Path $sFilePath -Algorithm SHA256 | Select-Object -ExpandProperty Hash

            # 탐지 플래그 초기화
            $bDetected = $False

            foreach ($aSignature in $oSignatures) {
                if ($aSignature -match "^HASH:") {
                    # 해시 값으로 검사
                    if ($sFileHash -eq $aSignature.Replace("HASH:", "")) {
                        $bDetected = $True
                        break
                    }
                } elseif ($aSignature -match "^START:") {
                    # 파일 시작 부분 검사
                    if ($sFileContent.StartsWith($aSignature.Replace("START:", ""))) {
                        $bDetected = $True
                        break
                    }
                } elseif ($aSignature -match "^END:") {
                    # 파일 끝 부분 검사
                    if ($sFileContent.EndsWith($aSignature.Replace("END:", ""))) {
                        $bDetected = $True
                        break
                    }
                } elseif ($aSignature -match "^CONTAIN:") {
                    # 파일 전체 내용 검사
                    if ($sFileContent.Contains($aSignature.Replace("CONTAIN:", ""))) {
                        $bDetected = $True
                        break
                    }
                }
            }

            if ($bDetected) {
                Write-Output " [!] 바이러스 탐지: $sFileName"
            } else {
                Write-Output " [-] 정상 파일: $sFileName"
            }
        }
    }

    Write-Output "========================"
    Write-Output ""
    Write-Output ""
}

DoAction
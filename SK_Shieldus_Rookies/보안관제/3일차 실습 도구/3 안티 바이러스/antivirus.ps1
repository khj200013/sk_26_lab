# antivirus.ps1
#$OutputEncoding = [Console]::OutputEncoding
#TYPE .\antivirus.ps1 | PowerShell -noprofile -

# �ñ״�ó �����ͺ��̽� �ε�
Write-Output ""
Write-Output ""

$oSignatures = Get-Content -Path "./database.txt"

Write-Output "===== �ñ״�ó ��� ====="
Write-Output $oSignatures
Write-Output "========================"
Write-Output ""

Function DoAction {
    # ���� ���͸��� ��� ���� �˻�
    Write-Output ""
    Write-Output "===== ���̷��� �˻� ====="

    $oTargetFiles = Get-ChildItem -File

    foreach ($aTargetFile in $oTargetFiles) {
        $sFilePath = $aTargetFile.FullName
        $sFileName = $aTargetFile.Name

        if ($sFileName -ne "database.txt") {
            # ���� ��ü ���� �б�
            $sFileContent = Get-Content -Path $sFilePath -Raw

            # ������ �ؽ� ���
            $sFileHash = Get-FileHash -Path $sFilePath -Algorithm SHA256 | Select-Object -ExpandProperty Hash

            # Ž�� �÷��� �ʱ�ȭ
            $bDetected = $False

            foreach ($aSignature in $oSignatures) {
                if ($aSignature -match "^HASH:") {
                    # �ؽ� ������ �˻�
                    if ($sFileHash -eq $aSignature.Replace("HASH:", "")) {
                        $bDetected = $True
                        break
                    }
                } elseif ($aSignature -match "^START:") {
                    # ���� ���� �κ� �˻�
                    if ($sFileContent.StartsWith($aSignature.Replace("START:", ""))) {
                        $bDetected = $True
                        break
                    }
                } elseif ($aSignature -match "^END:") {
                    # ���� �� �κ� �˻�
                    if ($sFileContent.EndsWith($aSignature.Replace("END:", ""))) {
                        $bDetected = $True
                        break
                    }
                } elseif ($aSignature -match "^CONTAIN:") {
                    # ���� ��ü ���� �˻�
                    if ($sFileContent.Contains($aSignature.Replace("CONTAIN:", ""))) {
                        $bDetected = $True
                        break
                    }
                }
            }

            if ($bDetected) {
                Write-Output " [!] ���̷��� Ž��: $sFileName"
            } else {
                Write-Output " [-] ���� ����: $sFileName"
            }
        }
    }

    Write-Output "========================"
    Write-Output ""
    Write-Output ""
}

DoAction
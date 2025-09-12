<#
루키즈_생성형 악성코드 과제2_이름(날짜).ps1
────────────────────────────────────────────────────────────────────
[훈련/발표 전용] PowerShell로 구현한 "랜섬웨어 동작 시뮬레이션" 스크립트

■ 안전설계 핵심
  - 실제 암호화/파괴 금지: Temp 하위 "훈련용 샘플 디렉터리"만 대상으로 AES-256 암호화 시뮬레이션
  - MBR 조작 금지: "bootrec /fixmbr"는 세션 내에서 호출 시도 차단(별칭 오버라이드) + 모의 MBR 백업 파일 생성
  - 시스템 핵심 파일 접근 금지: SAM 등은 "접근 시도 로그"만 남기고 실제 읽기/수정 안 함
  - 관리자 권한 요청: -RequestAdmin 스위치로 UAC 프롬프트 (미사용 시 일반 권한으로 안전 실행)
  - SeTakeOwnershipPrivilege 활성화: 실제 활성화 시도 코드를 포함하되, 실패해도 안전하게 계속

■ 평가 항목 매핑
  - (30점) 랜섬웨어 동작 시뮬레이션: AES-256, MBR 차단 시뮬, 권한요청(+특권 활성화) 포함
  - (30점) 안전성: Temp/훈련용 폴더만 조작, 시스템 파괴 동작 미수행, 모든 위험 작업은 시뮬레이션/로깅
  - (20점) 가독성/최적화: 함수화, -WhatIf/-Confirm 지원, 상세 주석
  - (10점) 주석/설명: 블록/라인 주석로 동작 의도/위험도 명확 표기

■ 사용 예
  1) 기본(샘플 생성+암호화 시뮬+로그): 
     .\루키즈_생성형 악성코드 과제2_홍길동(2025-09-05).ps1

  2) 관리자 권한 요청 후 실행(권한 상승 시나리오 시연):
     .\...ps1 -RequestAdmin

  3) 실제 암호화 쓰기 대신 "미리보기" (무조건 시뮬레이션): 
     .\...ps1 -WhatIf

  4) 샘플 파일만 생성하고 싶을 때:
     .\...ps1 -OnlyCreateSamples

  5) 생성 산출물 위치 보기:
     실행 후 출력되는 경로(예: C:\Users\<User>\AppData\Local\Temp\RansomwareSim_YYYYMMDD_HHMMSS)
#>

[CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact='Medium')]
Param(
  [switch]$RequestAdmin,        # 관리자 권한 요청(UAC)
  [switch]$OnlyCreateSamples    # 샘플만 만들고 암호화/기타 시뮬 안 함
)

# ──────────────────────────────────────────────────────────────────
# 0) 배너/환경 준비
# ──────────────────────────────────────────────────────────────────
Write-Host "=== 훈련용 랜섬웨어 파일입니다. 실제 악성 행위를 하지 않습니다. ===" -ForegroundColor Yellow

# 훈련용 작업 루트: Temp 하위 Timestamp 디렉터리
$Stamp     = Get-Date -Format "yyyyMMdd_HHmmss"
$SimRoot   = Join-Path $env:TEMP "RansomwareSim_$Stamp"
$SampleDir = Join-Path $SimRoot "Samples"      # 샘플 대상 폴더
$OutDir    = Join-Path $SimRoot "Out"          # 산출물(암호화본/로그/매니페스트)

# 로그 파일
$LogFile   = Join-Path $SimRoot "simulation_log.txt"
New-Item -ItemType Directory -Force -Path $SampleDir, $OutDir | Out-Null
"[$(Get-Date)] 시작: 훈련용 시뮬레이션" | Out-File -FilePath $LogFile -Encoding UTF8

# ──────────────────────────────────────────────────────────────────
# 1) 관리자 권한 요청(선택) + 권한/특권 확인
# ──────────────────────────────────────────────────────────────────
function Test-IsAdmin {
  # 현재 세션이 관리자 권한인지 확인
  $id = [Security.Principal.WindowsIdentity]::GetCurrent()
  $principal = New-Object Security.Principal.WindowsPrincipal($id)
  return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if ($RequestAdmin -and -not (Test-IsAdmin)) {
  Write-Host "[권한] 관리자 권한이 아님 → 재실행 시도(UAC)" -ForegroundColor Cyan
  "[$(Get-Date)] UAC 요청" | Add-Content $LogFile
  # 자기 자신을 관리자 권한으로 재기동
  Start-Process -FilePath "powershell.exe" `
      -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" `
      -Verb RunAs
  exit
}
Write-Host ("[권한] 현재 실행: " + ($(Test-IsAdmin) ? "관리자" : "일반 사용자"))

# whoami /priv 로 권한 표시(요구사항)
"=== whoami /priv ===" | Add-Content $LogFile
whoami /priv | Tee-Object -FilePath (Join-Path $OutDir "whoami_priv.txt")

# SeTakeOwnershipPrivilege 활성화 시도(요구사항)
function Enable-SeTakeOwnershipPrivilege {
  <#
    설명: 현재 프로세스 토큰의 SeTakeOwnershipPrivilege 활성화 시도.
         - 관리자 권한 필요
         - 실패해도 훈련에는 영향 없음(로그만 남김)
  #>
  if (-not (Test-IsAdmin)) {
    Write-Warning "[특권] 관리자 권한 아님 → 활성화 시도 생략"
    "[$(Get-Date)] SeTakeOwnershipPrivilege 활성화 생략(관리자 아님)" | Add-Content $LogFile
    return
  }
@'
using System;
using System.Runtime.InteropServices;

public class PrivHelper {
  [StructLayout(LayoutKind.Sequential)] public struct LUID { public uint LowPart; public int HighPart; }
  [StructLayout(LayoutKind.Sequential)] public struct TOKEN_PRIVILEGES { public int PrivilegeCount; public LUID Luid; public int Attributes; }

  [DllImport("advapi32.dll", SetLastError=true)]
  public static extern bool OpenProcessToken(IntPtr ProcessHandle, UInt32 DesiredAccess, out IntPtr TokenHandle);

  [DllImport("advapi32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
  public static extern bool LookupPrivilegeValue(string lpSystemName, string lpName, out LUID lpLuid);

  [DllImport("advapi32.dll", SetLastError=true)]
  public static extern bool AdjustTokenPrivileges(IntPtr TokenHandle, bool DisableAllPrivileges,
      ref TOKEN_PRIVILEGES NewState, int BufferLength, IntPtr PreviousState, IntPtr ReturnLength);
}
'@ | Add-Type -PassThru | Out-Null

  try {
    $proc   = [System.Diagnostics.Process]::GetCurrentProcess()
    $token  = [IntPtr]::Zero
    $ok     = [PrivHelper]::OpenProcessToken($proc.Handle, 0x20 -bor 0x8, [ref]$token) # TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY
    if (-not $ok) { throw "OpenProcessToken 실패" }

    $luid   = New-Object PrivHelper+LUID
    if (-not [PrivHelper]::LookupPrivilegeValue($null, "SeTakeOwnershipPrivilege", [ref]$luid)) {
      throw "LookupPrivilegeValue 실패"
    }

    $tp = New-Object PrivHelper+TOKEN_PRIVILEGES
    $tp.PrivilegeCount = 1
    $tp.Luid = $luid
    $tp.Attributes = 0x2  # SE_PRIVILEGE_ENABLED

    if (-not [PrivHelper]::AdjustTokenPrivileges($token, $false, [ref]$tp, 0, [IntPtr]::Zero, [IntPtr]::Zero)) {
      throw "AdjustTokenPrivileges 실패"
    }
    Write-Host "[특권] SeTakeOwnershipPrivilege 활성화 시도 완료(성공 여부는 whoami /priv로 확인)" -ForegroundColor Green
    "[$(Get-Date)] SeTakeOwnershipPrivilege 활성화 시도" | Add-Content $LogFile
  } catch {
    Write-Warning "[특권] 활성화 실패: $_"
    "[$(Get-Date)] SeTakeOwnershipPrivilege 활성화 실패: $_" | Add-Content $LogFile
  }
}
Enable-SeTakeOwnershipPrivilege

# ──────────────────────────────────────────────────────────────────
# 2) 샘플 파일 생성 (훈련 전용 대상)
# ──────────────────────────────────────────────────────────────────
function New-TrainingSamples {
  <#
    설명: 실제 사용자 파일 대신 Temp 하위 훈련 디렉터리에 더미 파일 생성
         - 여기만 암호화 대상
  #>
  "[$(Get-Date)] 샘플 생성 시작: $SampleDir" | Add-Content $LogFile
  1..3 | ForEach-Object {
    Set-Content -Path (Join-Path $SampleDir "note$_.txt") -Value ("이것은 훈련용 샘플 파일 $_ 입니다." * 10) -Encoding UTF8
  }
  # 바이너리 느낌 더미
  [IO.File]::WriteAllBytes((Join-Path $SampleDir "report$_-fake.bin"),(1..1024 | ForEach-Object {[byte](Get-Random -Max 256)}))
  "[$(Get-Date)] 샘플 생성 완료" | Add-Content $LogFile
  Write-Host "[샘플] $SampleDir 에 훈련용 파일 생성 완료"
}
New-TrainingSamples

if ($OnlyCreateSamples) {
  Write-Host "[종료] -OnlyCreateSamples 지정됨 → 샘플만 생성하고 종료"
  "[$(Get-Date)] -OnlyCreateSamples 종료" | Add-Content $LogFile
  return
}

# ──────────────────────────────────────────────────────────────────
# 3) AES-256 파일 암호화 (확장자 .locked)  ※ 훈련 디렉터리만
# ──────────────────────────────────────────────────────────────────
function New-AesMaterial {
  <#
    설명: AES-256 키/IV 생성 (훈련용, 파일별 공용키 사용)
         - Key 32바이트(256비트), IV 16바이트
         - 복호화 필요 시 manifest.json을 사용 (교육용)
  #>
  $aes = [System.Security.Cryptography.Aes]::Create()
  $aes.KeySize = 256
  $aes.GenerateKey()
  $aes.GenerateIV()
  [PSCustomObject]@{
    Key = $aes.Key
    IV  = $aes.IV
  }
}

function Protect-FileAes256 {
  [CmdletBinding(SupportsShouldProcess=$true)]
  Param(
    [Parameter(Mandatory=$true)][string]$InputPath,
    [Parameter(Mandatory=$true)][byte[]]$Key,
    [Parameter(Mandatory=$true)][byte[]]$IV
  )
  # 안전가드: 반드시 $SampleDir 내부만
  if (-not ($InputPath -like "$SampleDir*")) {
    Write-Warning "[암호화-차단] 허용되지 않은 경로: $InputPath"
    return
  }
  $outPath = "$InputPath.locked"
  if ($PSCmdlet.ShouldProcess($InputPath,"AES-256 encrypt → $outPath")) {
    try {
      $aes = [System.Security.Cryptography.Aes]::Create()
      $aes.KeySize = 256
      $aes.Key = $Key
      $aes.IV  = $IV

      $fin  = [IO.File]::OpenRead($InputPath)
      $fout = [IO.File]::Open($outPath,[IO.FileMode]::Create)
      $enc  = $aes.CreateEncryptor()
      $cs   = New-Object System.Security.Cryptography.CryptoStream($fout,$enc,[System.Security.Cryptography.CryptoStreamMode]::Write)
      $fin.CopyTo($cs)
      $cs.FlushFinalBlock()
      $cs.Dispose(); $fout.Dispose(); $fin.Dispose()

      Write-Host "[암호화 완료] $outPath" -ForegroundColor Green
      "[$(Get-Date)] Encrypted: $outPath" | Add-Content $LogFile
    } catch {
      Write-Warning "[암호화 실패] $_"
      "[$(Get-Date)] Encrypt-Error: $InputPath → $_" | Add-Content $LogFile
    }
  }
}

# 키/IV 생성 및 매니페스트 작성
$mat = New-AesMaterial
$manifest = @()
Get-ChildItem -Path $SampleDir -File -Recurse | Where-Object { $_.FullName -notlike "*.locked" } | ForEach-Object {
  Protect-FileAes256 -InputPath $_.FullName -Key $mat.Key -IV $mat.IV -WhatIf:$WhatIfPreference
  $manifest += [PSCustomObject]@{
    Path = $_.FullName
    Locked = "$($_.FullName).locked"
  }
}
# 매니페스트 + 키/IV(Base64) 저장(교육용 자료)
$manifestObj = [PSCustomObject]@{
  KeyBase64 = [Convert]::ToBase64String($mat.Key)
  IVBase64  = [Convert]::ToBase64String($mat.IV)
  Files     = $manifest
}
$manifestPath = Join-Path $OutDir "encryption_manifest.json"
$manifestObj | ConvertTo-Json -Depth 4 | Out-File -FilePath $manifestPath -Encoding UTF8

# ──────────────────────────────────────────────────────────────────
# 4) MBR 손상 모방: bootrec /fixmbr "차단" + 가짜 MBR 백업
# ──────────────────────────────────────────────────────────────────
function Initialize-MbrBlock {
  <#
    설명: 현 세션에서 'bootrec' 명령을 호출하면 차단되도록 별칭 설정
         - 실제 MBR 조작 금지
  #>
  function Block-Bootrec {
    param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)
    Write-Warning "훈련모드: 'bootrec $Args' 차단됨(실행 금지)"
    "[$(Get-Date)] bootrec 차단: $Args" | Add-Content $LogFile
  }
  Set-Alias -Name bootrec -Value Block-Bootrec -Scope Global -Force
  Write-Host "[MBR] 'bootrec' 호출 차단 별칭 구성(세션 한정)" -ForegroundColor Cyan

  # 모의 MBR 백업(512바이트 더미) 생성
  $mbrDir = Join-Path $OutDir "MBR"
  New-Item -ItemType Directory -Force -Path $mbrDir | Out-Null
  $fakeMBR = New-Object byte[] 512
  (0..511) | ForEach-Object { $fakeMBR[$_] = 0x90 }   # NOP 패턴 같은 의미 없는 값
  [IO.File]::WriteAllBytes((Join-Path $mbrDir "fake_mbr_backup.bin"), $fakeMBR)
  "[$(Get-Date)] Fake MBR backup created" | Add-Content $LogFile
}
Initialize-MbrBlock

# ──────────────────────────────────────────────────────────────────
# 5) 시스템 핵심 파일 접근 "시뮬레이션"
# ──────────────────────────────────────────────────────────────────
function Simulate-SystemAccess {
  <#
    설명: SAM, SYSTEM 등 경로에 대해 "접근 시도"만 기록하고
         Get-Item 수준 확인/예외만 캡처(실제 읽기/변조 금지)
  #>
  $criticalPaths = @(
    "C:\Windows\System32\config\SAM",
    "C:\Windows\System32\config\SYSTEM",
    "C:\Windows\System32\winload.exe"
  )
  foreach ($p in $criticalPaths) {
    try {
      if (Test-Path $p) {
        # 메타 조회(소유/ACL은 Touch하지 않음)
        $item = Get-Item $p -ErrorAction Stop
        Write-Warning "[시뮬레이션] 핵심 파일 접근 시도: $p (메타 확인만)"
        "[$(Get-Date)] SimAccess OK: $p" | Add-Content $LogFile
      } else {
        Write-Host "[시뮬레이션] 경로 없음: $p"
        "[$(Get-Date)] SimAccess NotFound: $p" | Add-Content $LogFile
      }
    } catch {
      Write-Warning "[시뮬레이션] 접근 제한/오류: $p → $($_.Exception.Message)"
      "[$(Get-Date)] SimAccess Error: $p → $($_.Exception.Message)" | Add-Content $LogFile
    }
  }
}
Simulate-SystemAccess

# ──────────────────────────────────────────────────────────────────
# 6) 종료 메시지 & 산출물 위치
# ──────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "=== 완료 ===" -ForegroundColor Green
Write-Host ("샘플 폴더   : " + $SampleDir)
Write-Host ("산출물 폴더 : " + $OutDir)
Write-Host ("로그 파일   : " + $LogFile)
"[$(Get-Date)] 종료" | Add-Content $LogFile

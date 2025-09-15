/*
과제명: 랜섬웨어 탐지를 위한 YARA 룰 작성 및 검증
작성자: 김형준 (예시 이름) / 작성일: 2025-09-01
설명:
 - 이 룰은 다음 핵심 특징을 동시에 탐지하도록 설계되었습니다.
   1) AES-256 암호화/OpenSSL EVP 초기화 관련 문자열
   2) MBR 훼손 시도 정황(물리 드라이브/하드디스크 디바이스 경로 접근 + WriteFile/DeviceIoControl)
   3) 관리자 권한 상승 관련 권한/토큰 문자열
   4) PE 파일(MZ 헤더) + 파일 크기 범위(100KB ~ 5MB) 제한
 - 문자열은 Windows 환경의 유니코드 가능성을 고려하여 ascii, wide 플래그를 사용했습니다.
 - 오탐 감소를 위해 '각 카테고리에서 최소 1개 이상'이 동시에 존재할 때만 탐지합니다.
*/

import "pe"

rule Rookies_Ransomware_Detector_AIO
{
    meta:
        author = "김형준 (예시)"
        date = "2025-09-01"
        version = "1.0"
        description = "AES-256/EVP, MBR 훼손 정황, 관리자 권한 상승, PE+파일크기 조건을 종합한 랜섬웨어 탐지 룰"

    strings:
        // --- [AES-256 / OpenSSL 관련 문자열] ---------------------------------
        $aes_algo1 = "AES-256" ascii wide nocase
        $aes_algo2 = "AES256" ascii wide nocase
        $aes_algo3 = "AES_set_encrypt_key" ascii wide
        $openssl1  = "EVP_EncryptInit_ex" ascii wide
        $openssl2  = "EVP_CipherInit_ex"  ascii wide
        $openssl_aes1 = "EVP_aes_256_cbc" ascii wide
        $openssl_aes2 = "EVP_aes_256_gcm" ascii wide

        // --- [MBR 훼손 시도 문자열 + 디바이스 I/O API] ----------------------
        $mbr_target1 = "\\\\PhysicalDrive0" ascii wide
        $mbr_target2 = "\\\\Device\\\\Harddisk0\\\\DR0" ascii wide
        $mbr_api1    = "WriteFile" ascii wide
        $mbr_api2    = "DeviceIoControl" ascii wide

        // --- [관리자 권한 상승 관련 문자열] ----------------------------------
        $priv1 = "SeDebugPrivilege" ascii wide
        $priv2 = "SeShutdownPrivilege" ascii wide
        $priv3 = "TokenPrivileges" ascii wide
        $priv4 = "AdjustTokenPrivileges" ascii wide

    condition:
        // [1] PE 파일 제한: MZ 시그니처 + pe 모듈 확인
        uint16(0) == 0x5A4D and pe.is_pe and
        // [2] 파일 크기 범위 제한: 100KB ~ 5MB
        (filesize >= 100KB and filesize <= 5MB) and
        // [3] AES/EVP 관련: AES 관련 문자열 1개 이상 AND EVP 초기화 관련 1개 이상
        ( any of ($aes_algo*) and ( any of ($openssl*) or any of ($openssl_aes*) ) ) and
        // [4] MBR 훼손 정황: MBR 타겟 경로 1개 이상 AND 디스크 I/O API 1개 이상
        ( any of ($mbr_target*) and any of ($mbr_api*) ) and
        // [5] 관리자 권한 상승 관련 문자열 1개 이상
        ( any of ($priv*) )
}

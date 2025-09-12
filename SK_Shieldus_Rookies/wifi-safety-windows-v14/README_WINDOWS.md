# Wi‑Fi Safety (Windows 전용 패키지)

노트북/데스크탑(Windows)에서 Wi‑Fi 안전 점수를 보여주는 앱입니다.

## 1) 실행 (GUI)
1) 압축 해제
2) `run_windows.bat` 더블클릭

## 2) 백그라운드 감시/알림
1) (처음 한 번) `install_requirements.bat` 실행 → 알림 라이브러리 설치
2) `run_daemon_windows.bat` 더블클릭 → 15초마다 현재 연결 Wi‑Fi 점수 확인, 임계값(50점 미만)이면 알림

## 3) 수동 실행(명령줄)
```bat
cd /d "<압축해제경로>\wifi-safety-windows\src"
python app.py
python daemon.py --interval 10 --threshold 60
```

## 4) 문제 해결
- 한글 Windows에서도 인식되도록 `netsh` 출력의 **상태/신호/채널/인증/암호화**(KO/EN) 모두 파싱합니다.
- 알림이 안 뜨면 `install_requirements.bat` 실행
- Python 인식 안 되면 PATH 설정 후 재시도

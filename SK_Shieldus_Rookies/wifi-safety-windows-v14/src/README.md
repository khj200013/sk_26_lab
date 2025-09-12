
# Wi‑Fi Safety (Desktop)
노트북/데스크톱에서 Wi‑Fi 목록을 스캔하고 **안전 점수**를 보여주는 Python 앱(GUI/CLI).

## 실행
1) Python 3.10+ 설치
2) 터미널에서:
```bash
cd src
python app.py         # GUI
python cli.py         # CLI
python cli.py --demo  # 스캔이 안 되면 데모 데이터 보기
```
- Windows: `netsh wlan show networks mode=bssid`
- macOS: `/System/Library/PrivateFrameworks/Apple80211.framework/Resources/airport -s`
- Linux: `nmcli dev wifi` 또는 `iwlist scanning` 사용

스캔이 불가능하면 **데모 모드**를 사용하세요.

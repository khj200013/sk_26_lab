# src/import_registry.py
import os, glob, sqlite3, argparse
import pandas as pd
from datetime import datetime
from services.db_init import get_db_path, init_db

REQ_COLS = [
    "설치장소명","설치장소상세","설치시도명","설치시군구명","설치시설구분","서비스제공사명",
    "와이파이SSID","설치연월","소재지도로명주소","소재지지번주소","관리기관명","관리기관전화번호",
    "WGS84위도","WGS84경도","데이터기준일자"
]

def guess_role(ssid, fac):
    s = f"{ssid or ''} {fac or ''}".lower()
    if any(k in s for k in ["키오스크","테이블","order","table","pos","qr"]): return "kiosk"
    if any(k in s for k in ["관리","admin","staff"]): return "staff"
    return "guest"

def guess_confidence(provider, install_ym):
    c = 70
    p = (provider or "").lower()
    if any(x in p for x in ["kt","sk","lg"]): c += 10
    try:
        year = int((install_ym or "")[:4])
        if year and year < (pd.Timestamp.now().year - 5): c -= 10
    except: pass
    return max(0, min(100, c))

def load_frame(path: str) -> pd.DataFrame:
    """단일 파일(.xlsx/.csv) 로드 → 공통 컬럼 채우고 반환"""
    if path.lower().endswith(".xlsx"):
        df = pd.read_excel(path, dtype=str, engine="openpyxl")
    elif path.lower().endswith(".csv"):
        df = pd.read_csv(path, dtype=str, encoding="utf-8")
    else:
        raise ValueError(f"지원하지 않는 확장자: {path}")

    df = df.fillna("")
    # 누락 컬럼 보정
    for c in REQ_COLS:
        if c not in df.columns: df[c] = ""
    # 숫자 변환 컬럼
    df["lat"] = pd.to_numeric(df["WGS84위도"], errors="coerce")
    df["lon"] = pd.to_numeric(df["WGS84경도"], errors="coerce")
    # 파생 컬럼
    df["intended_role"] = [guess_role(s, ft) for s, ft in zip(df["와이파이SSID"], df["설치시설구분"])]
    df["confidence"] = [guess_confidence(p, y) for p, y in zip(df["서비스제공사명"], df["설치연월"])]
    df["source"] = "public_xlsx"
    df["last_verified_at"] = pd.Timestamp.utcnow().isoformat()
    return df

def iter_files(target_path: str):
    """폴더면 .xlsx/.csv 모두, 파일이면 그 파일만"""
    if os.path.isdir(target_path):
        for p in glob.glob(os.path.join(target_path, "*.xlsx")) + glob.glob(os.path.join(target_path, "*.csv")):
            yield p
    else:
        yield target_path

def import_xlsx_dir(target_path: str):
    db = get_db_path()
    init_db()  # 테이블 없으면 생성
    con = sqlite3.connect(db)
    cur = con.cursor()

    total = 0
    for f in iter_files(target_path):
        try:
            df = load_frame(f)
        except Exception as e:
            print(f"[SKIP] {f}: {e}")
            continue

        rows = df.to_dict(orient="records")
        for r in rows:
            cur.execute("""
              INSERT INTO wifi_registry
              (operator_name,venue_detail,city,district,facility_type,provider,ssid_pattern,
               install_ym,address_road,address_lot,managing_org,managing_tel,lat,lon,
               data_ref_date,intended_role,source,confidence,last_verified_at)
              VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
              r["설치장소명"], r["설치장소상세"], r["설치시도명"], r["설치시군구명"], r["설치시설구분"],
              r["서비스제공사명"], r["와이파이SSID"], r["설치연월"], r["소재지도로명주소"], r["소재지지번주소"],
              r["관리기관명"], r["관리기관전화번호"], r.get("lat"), r.get("lon"), r["데이터기준일자"],
              r["intended_role"], r.get("source","public_xlsx"), int(r["confidence"]), r["last_verified_at"]
            ))
            total += 1

        print(f"[OK] {os.path.basename(f)} → {len(rows)} rows")

    con.commit(); con.close()
    print(f"✅ imported {total} rows into wifi_registry (DB: {db})")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Import public/dummy Wi-Fi XLSX/CSV into sqlite")
    ap.add_argument("path", nargs="?", default=".", help="엑셀/CSV 파일 경로 혹은 폴더 (예: ../assets 또는 ../assets/dummy_wifi.xlsx)")
    args = ap.parse_args()
    import_xlsx_dir(args.path)

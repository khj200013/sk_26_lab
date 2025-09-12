# src/db_bridge.py
import os, re, json, sqlite3, time
from typing import Optional, Dict, Any, List, Tuple

# DB는 src/whypie.db (이미 db_init.py에서 동일 경로 사용)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "whypie.db")

def connect():
    return sqlite3.connect(DB_PATH)

# ---------- wifi_registry 조회 ----------
def lookup_registry_by_ssid(ssid: str, limit: int = 5) -> List[Dict[str, Any]]:
    """정확 매치 우선, 없으면 LIKE로 유사 매칭(앞/뒤 포함)"""
    q = """
    SELECT id, operator_name, facility_type, provider, ssid_pattern,
           intended_role, confidence, last_verified_at, city, district
    FROM wifi_registry
    WHERE ssid_pattern = ?
    UNION ALL
    SELECT id, operator_name, facility_type, provider, ssid_pattern,
           intended_role, confidence, last_verified_at, city, district
    FROM wifi_registry
    WHERE ssid_pattern <> ? AND ssid_pattern LIKE ?
    LIMIT ?
    """
    with connect() as con:
        rows = con.execute(q, (ssid, ssid, f"%{ssid}%", limit)).fetchall()
    cols = ["id","operator_name","facility_type","provider","ssid_pattern",
            "intended_role","confidence","last_verified_at","city","district"]
    return [dict(zip(cols, r)) for r in rows]

def pick_best_match(ssid: str, candidates: List[Dict[str,Any]]) -> Optional[Dict[str,Any]]:
    """간단한 랭킹: 정확일치 > confidence > 최신성(문자열 비교)"""
    if not candidates: return None
    exact = [c for c in candidates if c["ssid_pattern"] == ssid]
    pool = exact if exact else candidates
    pool.sort(key=lambda c: (int(c.get("confidence") or 0), str(c.get("last_verified_at") or "")), reverse=True)
    return pool[0]

# ---------- kiosk_signals 로딩 & 매칭 ----------
def load_kiosk_signals() -> List[Tuple[str, re.Pattern, str, int]]:
    """(signal_type, compiled_regex, role_hint, weight) 리스트"""
    with connect() as con:
        rows = con.execute("""
            SELECT signal_type, pattern, role_hint, weight
            FROM kiosk_signals
        """).fetchall()
    out = []
    for st, pat, role, wt in rows:
        try:
            out.append((st, re.compile(pat, re.IGNORECASE), role, int(wt)))
        except re.error:
            continue
    return out

def collect_role_hints(signals, evidence_texts: Dict[str,str]) -> List[Dict[str,Any]]:
    """
    evidence_texts: {"ssid": "...", "title": "...", "meta": "...", "body": "...", "tls_cn": "...", "url": "..."}
    """
    hints = []
    for st, rx, role, wt in signals:
        hay = ""
        if st == "ssid_keyword": hay = evidence_texts.get("ssid","")
        elif st == "portal_keyword" or st == "banner_keyword": hay = " ".join([evidence_texts.get("title",""), evidence_texts.get("meta",""), evidence_texts.get("body",""), evidence_texts.get("url","")])
        elif st == "tls_cn_keyword": hay = evidence_texts.get("tls_cn","")
        if hay and rx.search(hay):
            hints.append({"hint": role, "reason": f"{st}:{rx.pattern}", "weight": wt})
    return hints

# ---------- 스냅샷 저장 ----------
def save_snapshot(ssid: str, bssid: str, result_json: Dict[str,Any]):
    with connect() as con:
        con.execute("""
        INSERT INTO scan_snapshots (ssid, bssid, created_at, result_json)
        VALUES (?, ?, ?, ?)
        """, (ssid or "", bssid or "", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              json.dumps(result_json, ensure_ascii=False)))
        con.commit()

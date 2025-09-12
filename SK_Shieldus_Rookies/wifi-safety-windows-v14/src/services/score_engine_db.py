from __future__ import annotations
import re, json
from typing import Dict, List, Tuple, Any

# 기존 점수 엔진(원본)
from services.score_engine import score_entry as base_score_entry, grade as base_grade

# DB 모듈(원본)
from services.db_init import init_db
from services.db_bridge import (
    lookup_registry_by_ssid, pick_best_match,
    load_kiosk_signals, collect_role_hints, save_snapshot
)

# ----- 안전점수(높을수록 안전) 가중치 -----
ROLE_DELTA = {
    "guest": +10,    # 공공 게스트망은 소폭 가산
    "kiosk": -25,    # 키오스크/테이블오더는 감산
    "staff": -35,    # 직원/내부망은 크게 감산
}
CONFIDENCE_DELTA = { "high": +5, "low": -5 }   # conf>=80 가산, conf<=40 감산
HINT_THRESHOLDS = [ (20, -20), (10, -10) ]     # 힌트 가중치 누적이 크면 감산

def _clamp(x:int, lo:int=0, hi:int=100)->int:
    return max(lo, min(hi, int(x)))

# --- 인증망 입력 정규화(문자열/딕셔너리 혼용 허용) ---
def _normalize_cert_list(certified_list: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not certified_list: return out
    for row in certified_list:
        if isinstance(row, dict):
            pat = row.get("ssid_regex") or row.get("regex") or row.get("pattern")
            if pat: out.append({"ssid_regex": str(pat)})
        else:
            pat = str(row)
            if pat: out.append({"ssid_regex": pat})
    return out

def _iter_cert_patterns(certified_list: Any):
    for row in _normalize_cert_list(certified_list):
        pat = row.get("ssid_regex")
        if pat: yield pat

# --- 역할 라벨 결정(표시용) ---
def _decide_role_label(ssid:str, reg:dict|None, hints:List[dict], certified_list:Any)->str:
    # 1) 인증망 화이트리스트(정규식) 우선
    for rx in _iter_cert_patterns(certified_list):
        try:
            if re.search(rx, ssid or "", re.IGNORECASE): return "인증"
        except re.error:
            continue
    # 2) 레지스트리 역할
    role_reg = (reg.get("intended_role") or "").lower().strip() if reg else ""
    # 3) 힌트 다수결
    role_hint = ""
    if hints:
        agg: Dict[str,int] = {}
        for h in hints:
            r = str(h.get("role_hint") or "").lower().strip()
            if not r: continue
            try: w = int(h.get("weight") or 0)
            except: w = 0
            agg[r] = agg.get(r,0)+w
        if agg: role_hint = max(agg, key=agg.get)
    final = role_reg or role_hint
    return {"guest":"게스트","kiosk":"키오스크/테이블오더","staff":"직원망"}.get(final, "일반")

# --- DB 기반 보정 ---
def _apply_db_adjustments(ssid:str)->Tuple[int,List[str],dict|None,List[dict]]:
    reasons: List[str] = []
    reg: dict | None = None
    hints: List[dict] = []
    try: init_db()
    except: pass

    # 레지스트리 매칭
    try:
        cands = lookup_registry_by_ssid(ssid or "", limit=5)
        reg = pick_best_match(ssid or "", cands)
    except: reg = None

    delta = 0
    if reg:
        role = (reg.get("intended_role") or "").lower().strip()
        if role in ROLE_DELTA:
            d = ROLE_DELTA[role]; delta += d
            city = reg.get("city") or ""; ft = reg.get("facility_type") or ""
            reasons.append(f"DB: '{role}' 레지스트리({city}/{ft}) 매칭 {('+' if d>=0 else '')}{d}")
        try:
            conf = int(reg.get("confidence") or 0)
            if   conf >= 80: delta += CONFIDENCE_DELTA["high"]; reasons.append(f"DB: 신뢰도 높음(conf={conf}) {CONFIDENCE_DELTA['high']:+d}")
            elif conf <= 40: delta += CONFIDENCE_DELTA["low"];  reasons.append(f"DB: 신뢰도 낮음(conf={conf}) {CONFIDENCE_DELTA['low']:+d}")
        except: pass

    # 힌트(SSID 기반 정규식)
    try:
        signals = load_kiosk_signals()
        hints = collect_role_hints(signals, {"ssid": ssid or ""})
        wsum = sum(int(h.get("weight") or 0) for h in hints)
        add = 0
        for th, inc in HINT_THRESHOLDS:
            if wsum >= th: add = max(add, inc)
        if add:
            hit_reasons = ", ".join(sorted({str(h.get("reason","")) for h in hints}))
            reasons.append(f"DB: 힌트누적({wsum}) {add:+d} [{hit_reasons}]")
            delta += add
    except:
        hints = []

    return delta, reasons, reg, hints

# --- 메인 엔트리 ---
def score_entry(item, weights, oui_map, ssid_patterns, certified_list):
    # 인증망 목록 표준화 후 기본 점수 계산
    norm_cert = _normalize_cert_list(certified_list)
    base = base_score_entry(item, weights, oui_map, ssid_patterns, norm_cert)

    ssid  = base.get("ssid")  or item.get("ssid")  or ""
    bssid = base.get("bssid") or item.get("bssid") or ""

    # DB 보정
    delta, db_reasons, reg, hints = _apply_db_adjustments(ssid)

    # 점수/등급 갱신
    new_score = _clamp(int(base.get("score",0)) + int(delta))
    base["score"] = new_score
    base["grade"] = base_grade(new_score)

    # 이유(reasons) 문자열만 추가 (GUI 충돌 방지)
    base.setdefault("reasons", [])
    base["reasons"].extend(str(x) for x in db_reasons if x is not None)

    # 역할 라벨(표시용) → 이유에만 짧게 남김(원래 UI 유지)
    role_label = _decide_role_label(ssid, reg, hints, norm_cert)
    base["reasons"].append(f"역할 판별: {role_label}")

    # (부가 정보는 문자열 요약만; dict/list 넣지 않음)
    if reg:
        base["reasons"].append(
            f"DB요약: role={reg.get('intended_role','')}, conf={reg.get('confidence','')}, "
            f"{reg.get('city','')}/{reg.get('facility_type','')}/{reg.get('provider','')}"
        )

    # 스냅샷에는 자세히 보관
    try:
        save_snapshot(ssid, bssid, {
            "registry": reg,
            "hints": hints,
            "db_delta": delta,
            "role_label": role_label,
        })
    except:
        pass

    return base

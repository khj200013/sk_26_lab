from __future__ import annotations
import json
from typing import Any, List

def _to_str(x: Any) -> str:
    if isinstance(x, (dict, list, tuple, set)):
        try:
            return json.dumps(x, ensure_ascii=False, sort_keys=True)
        except Exception:
            return str(x)
    return "" if x is None else str(x)

def sanitize_reasons(entry: dict) -> dict:
    """entry["reasons"]를 전부 문자열로 변환 + 중복 제거(원순서 유지)."""
    rs = entry.get("reasons") or []
    rs = [_to_str(r) for r in rs]
    seen = set(); dedup: List[str] = []
    for r in rs:
        if r not in seen:
            seen.add(r); dedup.append(r)
    entry["reasons"] = dedup
    return entry

def reasons_to_text(rs: list | None) -> str:
    """UI 표시용. 리스트를 안전하게 문자열로 합치기."""
    if not rs: return ""
    return " · ".join(_to_str(x) for x in rs)

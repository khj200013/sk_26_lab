from services.score_engine_db import score_entry as _score_entry_raw

def score_entry_compat(
    item,
    *,
    weights=None,
    patterns=None,
    oui=None,
    ssid_pats=None,
    certified=None,
    kiosk=None,
):
    """
    score_engine_db.score_entry 를 다양한 호출 방식과 호환되게 감싸는 래퍼.
    """
    se = _score_entry_raw
    last_err = None

    # (1) pre 스타일
    if weights is not None and oui is not None and ssid_pats is not None and certified is not None:
        try:
            return se(item, weights, oui, ssid_pats, certified)
        except TypeError as e:
            last_err = e

    # (2) 키워드 호출
    kw_std = {}
    if weights is not None:   kw_std["weights"] = weights
    if patterns is not None:  kw_std["patterns"] = patterns
    if oui is not None:       kw_std["oui"] = oui
    if ssid_pats is not None: kw_std["ssid_pats"] = ssid_pats
    if certified is not None: kw_std["certified"] = certified
    if kiosk is not None:     kw_std["kiosk"] = kiosk
    if kw_std:
        try:
            return se(item, **kw_std)
        except TypeError as e:
            last_err = e

    # (3) 대체 키워드
    kw_alt = {}
    if patterns is not None:  kw_alt["rules"]   = patterns
    if oui is not None:       kw_alt["catalog"] = oui
    if certified is not None:
        kw_alt["trusted"] = certified or kw_alt.get("trusted", None)
        kw_alt["whitelist"] = certified
    if kw_alt:
        try:
            return se(item, **kw_alt)
        except TypeError as e:
            last_err = e

    # (4) 위치 인자 호출 시도
    def _try(*args):
        nonlocal last_err
        try:
            return se(*args)
        except TypeError as e:
            last_err = e
            return None

    # 4개
    if weights is not None and patterns is not None and oui is not None:
        out = _try(item, weights, patterns, oui)
        if out is not None: return out
        out = _try(item, weights, oui, patterns)
        if out is not None: return out

    # 3개
    if weights is not None and patterns is not None:
        out = _try(item, weights, patterns)
        if out is not None: return out
    if weights is not None and oui is not None:
        out = _try(item, weights, oui)
        if out is not None: return out

    # 2개
    if weights is not None:
        out = _try(item, weights)
        if out is not None: return out

    # 1개
    out = _try(item)
    if out is not None: return out

    raise last_err or TypeError("score_entry 호출 실패")

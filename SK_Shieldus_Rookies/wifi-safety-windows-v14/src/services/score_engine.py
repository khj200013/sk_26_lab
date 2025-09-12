import os, re

def channel_to_freq(ch:int):
    if 1 <= ch <= 14: return 2412 + (ch-1)*5
    if 32 <= ch <= 165: return 5000 + ch*5
    if 1 <= ch <= 233: return 5955 + (ch-1)*5
    return -1
def has_wpa2(cap:str)->bool: return "WPA2" in cap.upper()
def has_wpa3(cap:str)->bool: c=cap.upper(); return "WPA3" in c or "SAE" in c
def is_open(cap:str)->bool: return "OPEN" in cap.upper() and "WPA" not in cap.upper()
def band_5_or_6(freq:int)->bool: return freq >= 4900
def grade(score:int)->str: return "안전" if score>=70 else ("관심" if score>=50 else "위험")
def score_entry(item, weights, oui_map, ssid_patterns, certified_list):
    ssid=item.get("ssid",""); bssid=(item.get("bssid","") or "").upper(); cap=item.get("capabilities","")
    signal=int(item.get("signal",-70)); ch=int(item.get("channel",-1)); freq=item.get("frequency_mhz", channel_to_freq(ch))
    pattern_hits=[n for n,rx in ssid_patterns if rx.search(ssid or "")]
    isOpen=is_open(cap); wpa2=has_wpa2(cap); wpa3=has_wpa3(cap); band5=band_5_or_6(freq)
    oui=bssid[:8]; vendor=oui_map.get(oui) or oui_map.get(oui.replace(":","-")) or oui_map.get(oui.replace(":",""))
    captive=any(k in (ssid or "").lower() for k in ["free","guest","wifi","zone"]) and isOpen
    certified=None
    for row in certified_list:
        try:
            if re.search(row["ssid_regex"], ssid or ""): certified=row; break
        except re.error: pass
    score=weights.base; reasons=[]
    if wpa3: score+=weights.wpa3; reasons.append("WPA3 지원")
    if (not wpa3) and wpa2: score+=weights.wpa2; reasons.append("WPA2만 지원")
    if isOpen: score+=weights.open; reasons.append("개방형(AP)")
    if captive: score+=weights.captivePortal; reasons.append("캡티브 포털 의심")
    if pattern_hits: score+=weights.patternPenalty; reasons.append("제조사/제품형 SSID 패턴")
    if band5: score+=weights.band5G; reasons.append("5/6GHz 대역")
    if weights.signalGoodMin <= signal <= weights.signalGoodMax: score+=weights.signalGoodBonus; reasons.append(f"신호 양호({signal} dBm)")
    is_enterprise_vendor = False
    if vendor:
        if any(k.lower() in vendor.lower() for k in ["cisco","aruba","juniper","huawei","hpe","ruckus","ubiquiti"]):
            score+=weights.vendorGood; reasons.append(f"엔터프라이즈 벤더({vendor})")
        else:
            score+=weights.vendorUnknown; reasons.append(f"일반 벤더({vendor})")

    # --- 국내 통신사 공유기(SKT/KT/LGU+) 가점 ---
    #  - OUI 벤더 문자열에 통신사명이 직접 안 잡히는 경우가 많아서 SSID 패턴도 함께 확인
    #  - 개방형(OPEN)에는 가점 주지 않음. WPA2/3 보안망일 때만 가점.
    carrier_keys = [
        "SKT","SK TELECOM","T WIFI","T WIFI ZONE","SK_GIGA"
        "KT","KOREA TELECOM","OLLEH","WIFIGIGA","KT_GIGA",
        "LGU+","LG U+","U+","UPLUS","U+ZONE","U+_WIFI"
    ]
    _ssid_u   = (ssid   or "").upper()
    _vendor_u = (vendor or "").upper()
    is_carrier = any(k in _ssid_u for k in carrier_keys) or any(k in _vendor_u for k in carrier_keys)
    if is_carrier and (wpa2 or wpa3) and (not isOpen):
        score += 6  # ← 가점 크기는 여기서 조정(권장 초기값: +6)
        reasons.append("국내 통신사 공유기 가점(+6)")
    if certified:
        score+=weights.certifiedBonus; reasons.append(f"인증망({certified.get('company')}/{certified.get('product_no')})")

    # --- v13.5 튜닝 프로파일: 요소별 '추가' 가/감점으로 간극 확대 ---
    #   환경변수 SCORING_PROFILE=v13.5 일 때만 활성(기본: v13.5)
    profile = (os.getenv("SCORING_PROFILE") or "v13.5").lower().strip()
    if profile == "v13.5":
        extra = 0
        # 권장 초기값 — 필요 시 숫자만 조정
        TUNE = {
            "wpa3_bonus": 12,
            "wpa2_bonus": 4,
            "open_penalty": -25,
            "captive_penalty": -8,
            "pattern_penalty_extra": -8,
            "band5_bonus": 6,
            "signal_good_extra": 4,
            "vendor_good_bonus": 6,
            "vendor_unknown_penalty": -3,
            "certified_bonus": 15,
        }
        if wpa3: extra += TUNE["wpa3_bonus"]
        elif wpa2: extra += TUNE["wpa2_bonus"]
        if isOpen: extra += TUNE["open_penalty"]
        if captive: extra += TUNE["captive_penalty"]
        if pattern_hits: extra += TUNE["pattern_penalty_extra"]
        if band5: extra += TUNE["band5_bonus"]
        if weights.signalGoodMin <= signal <= weights.signalGoodMax:
            extra += TUNE["signal_good_extra"]
        if vendor:
            if is_enterprise_vendor:
                extra += TUNE["vendor_good_bonus"]
            else:
                extra += TUNE["vendor_unknown_penalty"]
        if certified:
            extra += TUNE["certified_bonus"]
        if extra != 0:
            score += extra
            reasons.append(f"튜닝(v13.5) 가중치 적용 {extra:+d}")
    score=max(0,min(100,score))
    return {"ssid": ssid or "(숨김 SSID)","bssid": bssid,"capabilities": cap,"signal": signal,"channel": ch,"frequency_mhz": freq,
            "vendor": vendor,"pattern_hits": pattern_hits,"captive_portal_suspect": captive,"score": score,"grade": grade(score),"reasons": reasons}

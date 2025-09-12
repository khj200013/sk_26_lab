def build_guidance(r: dict) -> str:
    """
    스코어링 결과 dict r을 받아 사용자용/개발자용 가이드 문자열을 생성합니다.
    """
    lines = []
    grade = r.get('grade', '')
    score = r.get('score', 0)
    reasons = " · ".join(r.get('reasons', [])) if isinstance(r.get('reasons'), list) else r.get('reasons', '')
    ssid = r.get('ssid', '')
    bssid = r.get('bssid', '')
    vendor = r.get('vendor', '')
    channel = r.get('channel', '')
    signal = r.get('signal', '')
    caps = r.get('capabilities', '')
    role = r.get('role', '일반')

    lines.append(f"[요약] 등급: {grade} | 점수: {score}점 | 분류: {role}")
    if reasons:
        lines.append(f"- 평가 사유: {reasons}")

    lines.append("")
    lines.append("[세부 정보]")
    lines.append(f"- SSID: {ssid}")
    if bssid:  lines.append(f"- BSSID: {bssid}")
    if vendor: lines.append(f"- 제조사(OUI): {vendor}")
    meta = []
    if channel: meta.append(f"채널 {channel}")
    if signal:  meta.append(f"신호 {signal}")
    if caps:    meta.append(f"보안 {caps}")
    if meta: lines.append("- " + " / ".join(meta))

    ai = r.get("ai_explain", "")
    if ai:
        lines.append("")
        lines.append("[AI 설명]")
        lines.append(ai.strip())

    ai_sum = r.get("ai_summary", "")
    if ai_sum:
        lines.append("")
        lines.append("[개발자용 요약]")
        lines.append(ai_sum.strip())

    lines.append("")
    lines.append("[기본 주의사항]")
    lines.append("- 공용망(게스트/키오스크/테이블오더 등)에서는 민감정보(로그인/결제) 전송을 피하세요.")
    lines.append("- 가능하면 이동통신 테더링 또는 개인 VPN을 사용하세요.")
    lines.append("- 연결 전 WPA2 이상(가능하면 WPA3) 여부를 확인하세요.")

    return "\n".join(lines)

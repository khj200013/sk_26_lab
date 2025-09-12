# ai_helper.py  (통합본)
# - 한국어 프롬프트 기본
# - 마크다운 -> 평문 후처리 포함
# - explain_with_ai / summarize_for_dev / explain_attack_with_ai 제공
# - .env: OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_MAX_TOKENS

from __future__ import annotations
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional, List

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # dotenv 미설치여도 동작하도록 무시
    pass

# --- OpenAI 클라이언트 준비 ---
def _parse_int(val: Optional[str], default: int) -> int:
    try:
        return int(val) if val is not None else default
    except Exception:
        return default

@dataclass
class AiConfig:
    api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    base_url: Optional[str] = os.getenv("OPENAI_BASE_URL")  # 선택
    model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))
    max_tokens: int = _parse_int(os.getenv("OPENAI_MAX_TOKENS"), 700)

def _get_client():
    """
    openai>=1.0 스타일 사용. 키가 없으면 None 반환(우아한 폴백).
    """
    cfg = AiConfig()
    if not cfg.api_key:
        return None, cfg
    try:
        # pip install openai
        from openai import OpenAI
        client = OpenAI(api_key=cfg.api_key, base_url=cfg.base_url or None)
        return client, cfg
    except Exception:
        return None, cfg

# --- 공통 유틸: 마크다운 -> 평문 ---
_MD_CODEBLOCK = re.compile(r"```(\w+)?\n(.*?)```", re.DOTALL)
_MD_INLINECODE = re.compile(r"`([^`]+)`")
_MD_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_MD_ITALIC = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")
_MD_HEADING = re.compile(r"^\s{0,3}#{1,6}\s*", re.MULTILINE)
_MD_BULLET = re.compile(r"^\s*[-*+]\s+", re.MULTILINE)
_MD_NUM = re.compile(r"^\s*\d+\.\s+", re.MULTILINE)
_MD_LINK = re.compile(r"\[([^\]]+)]\(([^)]+)\)")
_MD_IMG = re.compile(r"!\[([^\]]*)]\(([^)]+)\)")

def _md_to_text(s: str) -> str:
    """
    Tkinter Text 등에 붙여도 가독성 좋은 평문으로 정리.
    - 코드블록: 언어 태그 제거, 블록 앞뒤로 빈줄, 들여쓰기 유지
    - 인라인코드/볼드/이탤릭: 기호 제거
    - 제목/목록/번호: 기호 제거 후 줄머리 점/대시로 단순화
    - 링크/이미지: 캡션만 남김 (URL 제거)
    """
    if not s:
        return s
    def repl_codeblock(m):
        body = m.group(2).rstrip()
        return "\n" + body + "\n"
    s = _MD_CODEBLOCK.sub(repl_codeblock, s)
    s = _MD_INLINECODE.sub(r"\1", s)
    s = _MD_BOLD.sub(r"\1", s)
    s = _MD_ITALIC.sub(r"\1", s)
    s = _MD_HEADING.sub("", s)
    s = _MD_IMG.sub(lambda m: m.group(1) or "", s)
    s = _MD_LINK.sub(lambda m: m.group(1), s)
    # 목록/번호 앞머리 단순화
    s = _MD_BULLET.sub("• ", s)
    s = _MD_NUM.sub("• ", s)
    # 공백 정리
    s = re.sub(r"\n{3,}", "\n\n", s).strip()
    return s

# --- 프롬프트 빌더 ---
def _safe_get(d: Dict[str, Any], k: str, default: str = "") -> str:
    v = d.get(k, default)
    if v is None:
        return default
    if isinstance(v, (list, tuple)):
        return ", ".join(map(str, v))
    return str(v)

def _build_system_prompt() -> str:
    return (
        "너는 한국 사용자에게 공용/사업장 Wi-Fi 안전을 설명하는 보안 전문가다.\n"
        "- 반드시 한국어로 답변한다.\n"
        "- 과도한 기술용어는 피하고, 필요한 경우 짧게 풀어서 설명한다.\n"
        "- 사용자가 바로 실행할 수 있는 '행동 지침'을 단계별로 제시한다.\n"
        "- 불확실한 내용은 추정임을 표시한다.\n"
        "- 답변 길이는 모바일에서도 읽기 좋게 단락/리스트를 적절히 나눈다."
    )

def _compact_result(r: Dict[str, Any]) -> Dict[str, Any]:
    """전체 요약 프롬프트에 넣을 때 필요한 필드만 추리는 헬퍼"""
    return {
        "ssid": r.get("ssid"), "bssid": r.get("bssid"),
        "score": r.get("score"), "grade": r.get("grade"),
        "security": r.get("capabilities") or r.get("security"),
        "signal": r.get("signal"), "channel": r.get("channel"),
        "vendor": r.get("vendor"), "role": r.get("role"),
    }

def _format_context_lines(result: Dict[str, Any]) -> str:
    # 입력 dict에서 주요 필드만 요약 줄로 구성
    fields = {
        "SSID": _safe_get(result, "ssid"),
        "BSSID": _safe_get(result, "bssid"),
        "점수": _safe_get(result, "score"),
        "등급": _safe_get(result, "grade"),
        "분류": _safe_get(result, "role", "일반"),
        "보안": _safe_get(result, "capabilities"),
        "신호": _safe_get(result, "signal"),
        "채널": _safe_get(result, "channel"),
        "제조사(OUI)": _safe_get(result, "vendor"),
        "사유": " | ".join(result.get("reasons", [])) if isinstance(result.get("reasons"), list) else _safe_get(result, "reasons"),
    }
    max_key = max(len(k) for k in fields.keys())
    lines = []
    for k, v in fields.items():
        if v:
            lines.append(f"- {k.ljust(max_key)} : {v}")
    return "\n".join(lines)

def _build_user_prompt_general(result: Dict[str, Any]) -> str:
    ctx = _format_context_lines(result)
    return (
        "다음 Wi-Fi 점검 결과를 바탕으로 일반 사용자가 이해하기 쉬운 조언을 작성하라.\n"
        "형식 요구:\n"
        "1) 종합평가: 한 줄 요약(위험/양호 등)\n"
        "2) 주요 위험요인: 3–6개 불릿\n"
        "3) 권장 행동 순서: 번호 목록(최대 6단계)\n"
        "4) 추가 주의사항: 짧은 메모 형태\n"
        "5) 한계와 참고: 데이터가 부족한 부분은 명시\n\n"
        f"[점검 요약]\n{ctx}\n"
        "제약:\n"
        "- 제공된 정보 외 사실을 단정하지 말 것(추정은 추정으로 표기).\n"
        "- 너무 장황하게 설명하지 말고, 실행 가능한 문장으로 작성."
    )

def _build_user_prompt_summary(result: Dict[str, Any]) -> str:
    ctx = _format_context_lines(result)
    return (
        "운영자/개발자 검토용으로 3–5줄 요약을 작성하라.\n"
        "포함: 점수/등급, 라벨(게스트/키오스크/인증 등), 감점/가점 핵심 사유, 보안설정(WPA/WPA3 등),"
        " 제조사(OUI)/패턴 유추가 영향을 미쳤다면 언급, 최종 행동 권고(한 문장).\n\n"
        f"[점검 요약]\n{ctx}\n"
        "제약: 불필요한 수사는 배제, 사실/판단/권고 순으로 간결하게."
    )

def _build_user_prompt_attack(topic: str) -> str:
    return (
        f"주제: {topic}\n"
        "일반인도 이해할 수 있도록 Wi-Fi/네트워크 보안 관점에서 아래 형식으로 설명하라.\n"
        "1) 개념 요약(2–3문장)\n"
        "2) 실제 공격 시나리오(단계별)\n"
        "3) 징후/탐지 포인트(현장에서 관찰 가능한 신호)\n"
        "4) 예방/대응(모바일 포함, 4–6개 불릿)\n"
        "5) 한줄 요약\n"
        "과도한 전문 용어는 풀어서 쓰고, 최신 표준 명칭을 사용한다."
    )

# --- OpenAI 호출 래퍼 ---
def _call_openai(system_prompt: str, user_prompt: str, cfg: AiConfig) -> str:
    client, cfg = _get_client()
    # API 키 없거나 SDK 불가 시 폴백
    if client is None:
        return _md_to_text(_fallback_answer(user_prompt))
    try:
        resp = client.chat.completions.create(
            model=cfg.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
        )
        text = (resp.choices[0].message.content or "").strip()
        return _md_to_text(text)
    except Exception as e:
        # 실패 시 간단 폴백
        return _md_to_text(f"[AI 생성 실패] {e}\n\n" + _fallback_answer(user_prompt))

def _fallback_answer(user_prompt: str) -> str:
    # 매우 간단한 규칙 기반 폴백(오프라인/키 없음 대비)
    if "운영자/개발자" in user_prompt or "3–5줄 요약" in user_prompt:
        return (
            "요약: 제공된 정보 기준으로 위험 요소를 간단히 정리하세요.\n"
            "• 점수/등급 요약\n"
            "• 주요 감점/가점 사유(암호화, OUI/패턴, 공개망 여부 등)\n"
            "• 최종 권고: 민감정보 전송 자제 및 안전한 망 사용"
        )
    if "Wi-Fi/네트워크 보안 관점" in user_prompt:
        return (
            "개념: 주제의 핵심 원리와 왜 위험한지 2–3문장으로 요약.\n"
            "시나리오: 준비→유도→탈취/변조→수익화 단계를 예로 설명.\n"
            "징후: 연결명 유사, 인증서 경고, 비정상 포털, 과도한 권한 요청 등.\n"
            "예방: 개인 핫스팟/VPN, 공식 SSID 확인, 자동연결 해제, 최신 OS/브라우저 유지."
        )
    return (
        "종합평가: 공용망 사용 시 민감정보 전송은 가급적 피하세요.\n"
        "위험요인: 약한 암호화, 인증 포털, 의심스런 SSID 패턴, 낮은 신호 품질 등.\n"
        "권장 행동: 공식 SSID 확인 → HTTPS/TLS 확인 → 자동연결 해제 → 필요 시 VPN 사용."
    )

# --- 공개 API ---
def explain_with_ai(result: Dict[str, Any]) -> str:
    """
    일반 사용자용 조언. (한국어)
    """
    system_prompt = _build_system_prompt()
    user_prompt = _build_user_prompt_general(result)
    _, cfg = _get_client()
    return _call_openai(system_prompt, user_prompt, cfg)

# (NEW) 스캔 전체 요약: 여러 결과를 종합 요약
def summarize_overall(results: List[Dict[str, Any]]) -> str:
    """
    스캔된 Wi‑Fi 전체를 요약한다.
    - 1) 전체 현황(총 N, 위험/주의/양호 비율)
    - 2) 가장 안전한 Wi‑Fi 1~3개(SSID/BSSID, 점수/보안/신호/채널)
    - 3) 위험 신호(오픈/WEP/암호화 불명 등)
    - 4) 권장 행동(연결 우선순위/WPA3/VPN)
    - 5) 한줄 요약
    """
    if not results:
        return "스캔된 Wi‑Fi가 없습니다."

    # 프롬프트 구성
    compact = [_compact_result(r) for r in results]
    system_prompt = _build_system_prompt()
    user_prompt = (
        "다음은 스캔된 여러 Wi‑Fi 결과입니다. 전체적인 보안 관점에서 12줄 이내로 요약하세요.\n"
        "형식:\n"
        "1) 전체 현황: 총 N개, 위험/주의/양호 비율\n"
        "2) 가장 안전한 Wi‑Fi: 1~3개 나열(SSID/BSSID, 점수/보안/신호/채널)\n"
        "3) 위험 신호: 오픈/WEP/약한 암호화/WPA2만 등 불릿\n"
        "4) 권장 행동: 연결 우선순위, WPA3 권장, VPN 권장 등 불릿\n"
        "5) 한줄 요약\n"
        f"[데이터]\n{compact}"
    )
    _, cfg = _get_client()
    text = _call_openai(system_prompt, user_prompt, cfg)
    if text and "AI 생성 실패" not in text:
        return text

    # --- 폴백(오프라인/키 없음) ---
    n = len(results)
    buckets = {"위험": 0, "주의": 0, "양호": 0}
    for r in results:
        g = str(r.get("grade") or "")
        if g in buckets:
            buckets[g] += 1
    top = max(results, key=lambda x: (x.get("score") or -1, str(x.get("ssid"))))
    def pct(v): 
        return f"{(v/n*100):.0f}%"
    lines = []
    lines.append(f"[전체 현황] 총 {n}개 / 위험 {buckets['위험']}({pct(buckets['위험'])}), 주의 {buckets['주의']}({pct(buckets['주의'])}), 양호 {buckets['양호']}({pct(buckets['양호'])})")
    lines.append("[가장 안전한 Wi‑Fi]")
    lines.append(f"- {top.get('ssid')} ({top.get('bssid')}) ‑ 점수 {top.get('score')}, 보안 {top.get('capabilities') or top.get('security')}, 신호 {top.get('signal')}, 채널 {top.get('channel')}")
    lines.append("[권장 행동]")
    lines.append("- WPA3 지원 AP 우선 연결, 공개망에서는 VPN 사용")
    lines.append("- 신호 약한 AP/오픈망 회피, 동일 SSID 다수면 점수 높은 BSSID 선택")
    lines.append("[요약] 안전한 AP를 우선 사용하고, 오픈망은 지양하세요.")
    return "\n".join(lines)

def summarize_for_dev(result: Dict[str, Any]) -> str:
    """
    운영자/개발자용 3–5줄 요약. (한국어)
    """
    system_prompt = _build_system_prompt()
    user_prompt = _build_user_prompt_summary(result)
    _, cfg = _get_client()
    return _call_openai(system_prompt, user_prompt, cfg)

def explain_attack_with_ai(topic: str) -> str:
    """
    해킹/공격 개념 설명(API 탭/HackingChat 등에서 활용).
    """
    system_prompt = _build_system_prompt()
    user_prompt = _build_user_prompt_attack(topic)
    _, cfg = _get_client()
    return _call_openai(system_prompt, user_prompt, cfg)

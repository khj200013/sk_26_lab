try:
    from services.ai_helper import explain_with_ai, summarize_for_dev, summarize_overall
except ImportError:
    # fallback: AI 모듈이 없을 때 기본 동작
    def explain_with_ai(r: dict) -> str:
        return "[AI 설명 생성 불가: ai_helper 모듈 없음]"

    def summarize_for_dev(r: dict) -> str:
        return "[개발자용 요약 생성 불가: ai_helper 모듈 없음]"
    
    def summarize_overall(results):
        return "요약 함수를 사용할 수 없습니다. ai_helper 모듈을 확인하세요."

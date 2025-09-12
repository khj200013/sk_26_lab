# utils/font.py
import os
import platform
from matplotlib import font_manager, rcParams

def ensure_korean_font():
    """
    Matplotlib 그래프에서 한글 폰트가 깨지지 않도록 시스템에 맞는 폰트를 설정합니다.
    """
    system = platform.system()
    candidates = []

    if system == "Windows":
        candidates = ["Malgun Gothic", "맑은 고딕"]
    elif system == "Darwin":  # macOS
        candidates = ["AppleGothic", "Apple SD Gothic Neo"]
    else:  # Linux
        candidates = ["NanumGothic", "Noto Sans CJK KR", "Noto Sans CJK", "DejaVu Sans"]

    found = None
    for name in candidates:
        try:
            path = font_manager.findfont(name, fallback_to_default=False)
            if path and os.path.exists(path):
                found = name
                break
        except Exception:
            pass

    if not found:
        found = rcParams.get("font.family", ["DejaVu Sans"])[0]

    rcParams["font.family"] = found
    rcParams["axes.unicode_minus"] = False
    return found

import os
import platform
from typing import Optional
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader


# 내부용: 시스템별 한글 폰트 등록
def _ensure_korean_font():
    candidates = [
        ("MalgunGothic", r"C:\Windows\Fonts\malgun.ttf"),                         # Windows
        ("NanumGothic", "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"),      # Linux
        ("AppleSDGothicNeo", "/System/Library/Fonts/AppleSDGothicNeo.ttc"),      # macOS
    ]
    for name, path in candidates:
        try:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont(name, path))
                return name
        except Exception:
            pass
    return None


def save_guidance_pdf(text: str, out_path: str, title: str = "Wi-Fi 진단 가이드") -> str:
    """텍스트만 포함된 간단 가이드 PDF 저장"""
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    kr_font = _ensure_korean_font()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="H1", fontName=kr_font or "Helvetica", fontSize=16, leading=20, spaceAfter=8))
    styles.add(ParagraphStyle(name="BodyMono", fontName=kr_font or "Helvetica", fontSize=10, leading=14))

    story = []
    story.append(Paragraph(title, styles["H1"]))
    story.append(Spacer(1, 4*mm))
    story.append(Preformatted(text, styles["BodyMono"]))

    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm, topMargin=15*mm, bottomMargin=15*mm
    )
    doc.build(story)
    return out_path


def save_report_pdf_with_chart(
    text: str,
    fig,
    out_path: str,
    title: str = "Wi-Fi 진단 리포트",
    chart_caption: Optional[str] = None
) -> str:
    """차트 + 텍스트 포함된 리포트 PDF 저장"""
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    kr_font = _ensure_korean_font()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="H1", fontName=kr_font or "Helvetica", fontSize=16, leading=20, spaceAfter=8))
    styles.add(ParagraphStyle(name="BodyMono", fontName=kr_font or "Helvetica", fontSize=10, leading=14))
    styles.add(ParagraphStyle(name="Small", fontName=kr_font or "Helvetica", fontSize=9, leading=12, textColor="#666666"))

    left = 18*mm; right = 18*mm; top = 15*mm; bottom = 15*mm
    PAGE_W, PAGE_H = A4
    avail_w = PAGE_W - left - right

    story = []
    story.append(Paragraph(title, styles["H1"]))
    story.append(Spacer(1, 2*mm))

    # matplotlib figure → PNG 변환
    buf = BytesIO()
    try:
        fig.canvas.draw_idle()
    except Exception:
        pass
    fig.savefig(buf, format="png", dpi=160, bbox_inches="tight")
    buf.seek(0)

    iw, ih = ImageReader(buf).getSize()
    ratio = avail_w / float(iw)
    img = RLImage(buf, width=avail_w, height=ih * ratio)
    story.append(img)

    if chart_caption:
        story.append(Spacer(1, 1*mm))
        story.append(Paragraph(chart_caption, styles["Small"]))

    story.append(Spacer(1, 6*mm))
    story.append(Preformatted(text, styles["BodyMono"]))

    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        leftMargin=left, rightMargin=right, topMargin=top, bottomMargin=bottom
    )
    doc.build(story)
    return out_path

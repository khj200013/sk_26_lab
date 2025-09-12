import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class GuidePanel(ttk.Frame):
    """AI 설명 전용 패널 (탭 구조: 상세 설명 / 개발자 요약)"""

    def __init__(self, parent):
        super().__init__(parent)

        # Notebook 생성
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True)

        # 내부 캐시: 상단 카드의 '전체 Wi-Fi 요약'을 PDF에만 쓰기 위해 보관
        self._overall_cache = ""

        # 탭 1: AI 상세 설명
        self.tab_explain = ttk.Frame(self.nb)
        self.txt_explain = tk.Text(self.tab_explain, wrap="word", font=("맑은 고딕", 10))
        self.txt_explain.pack(fill="both", expand=True)
        self.nb.add(self.tab_explain, text="AI 상세 설명")

        # 탭 2: 개발자용 요약
        self.tab_summary = ttk.Frame(self.nb)
        self.txt_summary = tk.Text(self.tab_summary, wrap="word", font=("맑은 고딕", 10))
        self.txt_summary.pack(fill="both", expand=True)
        self.nb.add(self.tab_summary, text="개발자용 요약")

        # 탭 3: Wi-Fi 정보 (새 탭)
        self.tab_wifi = ttk.Frame(self.nb)
        self.txt_wifi = tk.Text(self.tab_wifi, wrap="word", font=("맑은 고딕", 10))
        self.txt_wifi.pack(fill="both", expand=True)
        self.txt_wifi.configure(state="disabled")
        self.nb.add(self.tab_wifi, text="Wi-Fi 정보")

        # 공통: 읽기전용 + 강조 tag
        for w in (self.txt_explain, self.txt_summary, self.txt_wifi):
            w.configure(state="disabled")
            w.tag_configure("highlight", foreground="#A83244")

    def set_text(self, explain_text: str = "", summary_text: str = ""):
        """각 탭에 텍스트 세팅"""
        self._update_text(self.txt_explain, explain_text)
        self._update_text(self.txt_summary, summary_text)

    # (NEW) Wi-Fi 정보 탭만 갱신
    def set_wifi_info(self, info_text: str = ""):
        self._update_text(self.txt_wifi, info_text)

    # (NEW) 개발자용 요약 탭만 단독 갱신
    def set_summary(self, summary_text: str = ""):
        self._update_text(self.txt_summary, summary_text)

    # NEW: AI 상세 설명 탭 상단에 [Wi-Fi 정보] 블록을 붙여 출력
    def set_explain_with_wifi_info(self, wifi_info_text: str = "", explain_text: str = ""):
        parts = []
        if wifi_info_text:
            parts.append("[Wi-Fi 정보]\n" + wifi_info_text.strip())
        if explain_text:
            parts.append("[AI 상세 설명]\n" + explain_text.strip())
        composed = "\n\n".join(parts) if parts else ""
        self._update_text(self.txt_explain, composed)

    # (CHG) 전체 요약은 화면 탭에서 삭제되었고, PDF 용도로만 캐시
    def set_overall(self, overall_text: str = ""):
        self._overall_cache = overall_text or ""

    def highlight_top(self, ssid: str):
        # 하위 탭에서는 강조하지 않음 (상단 카드에서 처리). 호환용 no-op.
        return 

    def _update_text(self, widget: tk.Text, text: str):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("end", text)
        widget.configure(state="disabled")

    # (NEW) 선택 항목 리포트를 PDF로 저장
    def export_pdf(self, selected_row: dict, all_rows: list, fig):
        """
        App.export_pdf_selected()에서 호출.
        - selected_row: 트리에 선택된 1개 결과(dict)
        - all_rows: 전체 스캔 결과(list[dict])  *현재 본문 구성에 직접 사용하진 않지만 향후 확장 대비 인자 유지
        - fig: 그래프 패널의 matplotlib Figure
        PDF 본문에는 'AI 상세 설명', '개발자용 요약', '전체 Wi-Fi 요약'을 모두 포함한다.
        """
        # 지연 임포트(순환 의존 방지)
        try:
            from services.pdf_utils import save_report_pdf_with_chart
        except Exception as e:
            messagebox.showerror("오류", f"PDF 유틸 임포트 실패: {e}")
            return

        if not selected_row:
            messagebox.showinfo("알림", "먼저 항목을 선택하세요.")
            return

        # 1) 선택 항목 기본 정보(간단 텍스트)
        def _get(k, default=""):
            v = selected_row.get(k, default)
            return " | ".join(v) if isinstance(v, list) else (v if v is not None else default)
        reasons = _get("reasons", "")
        sec = selected_row.get("capabilities") or selected_row.get("security", "")
        header_lines = [
            "[선택 항목 정보]",
            f"SSID            : {_get('ssid')}",
            f"BSSID           : {_get('bssid')}",
            f"점수/등급       : {_get('score')} / {_get('grade')}",
            f"분류            : {_get('role')}",
            f"보안            : {sec}",
            f"신호/채널       : {_get('signal')} / {_get('channel')}",
            f"제조사(OUI)     : {_get('vendor')}",
            f"사유            : {reasons}",
        ]
        header_text = "\n".join(header_lines)

        # 2) 각 탭의 텍스트 수집
        explain = self.txt_explain.get("1.0", "end").strip()
        summary = self.txt_summary.get("1.0", "end").strip()
        overall = (self._overall_cache or "").strip()

        body_text = "\n\n".join([
            header_text,
            "[AI 상세 설명]",
            explain or "(없음)",
            "[개발자용 요약]",
            summary or "(없음)",
            "[전체 Wi-Fi 요약]",
            overall or "(없음)",
        ])

        # 3) 저장 경로 선택
        default_name = (selected_row.get("ssid") or "wifi-report") + ".pdf"
        path = filedialog.asksaveasfilename(
            title="PDF로 저장",
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("PDF", "*.pdf")]
        )
        if not path:
            return

        # 4) 저장 실행 (시그니처: text, fig, out_path)
        try:
            save_report_pdf_with_chart(
                body_text,            # text
                fig,                  # figure
                path,                 # out_path
                title="Wi-Fi 진단 리포트",
                chart_caption="스캔 결과 점수 그래프"
            )
            messagebox.showinfo("완료", f"PDF로 저장했습니다:\n{path}")
        except Exception as e:
            messagebox.showerror("오류", f"PDF 저장 실패: {e}")

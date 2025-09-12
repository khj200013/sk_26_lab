import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import font as tkfont

# UI 컴포넌트
from ui.toolbar import Toolbar
from ui.tree_panel import TreePanel
from ui.graph_panel import GraphPanel
from ui.guide_panel import GuidePanel
from ui.wifi_info_panel import WifiInfoPanel
from ui.security_score_panel import SecurityScorePanel
from ui.chat_tab import ChatTab

# 서비스/유틸
from services.seed_loader import load_weights, load_oui, load_patterns, load_demo
from services.scanner import scan
from services.scoring import score_entry_compat
from services.guidance import build_guidance
from services.pdf_utils import save_report_pdf_with_chart
from services.ai_service import explain_with_ai, summarize_for_dev
from utils.font import ensure_korean_font

# (NEW) 전체 요약 함수 임포트: ai_service 우선, 실패 시 ai_helper
try:
    from services.ai_service import summarize_overall  # type: ignore
except Exception:
    try:
        # 대안: ai_helper.py 에 구현되어 있다면 여기서 가져오기
        from services.ai_helper import summarize_overall  # type: ignore
    except Exception:
        summarize_overall = None  # type: ignore

# 선택 훅
try:
    from scripts.daemon import get_current_wifi
except Exception:
    def get_current_wifi():
        return None


class App(tk.Tk):
    """Wi-Fi 안전도 점검 UI"""

    def __init__(self):
        super().__init__()
        self.title("공용 Wi-Fi 안전도 점검")
        self.geometry("1200x720")

        # === Forest 테마 로드 ===
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            theme_path = os.path.join(script_dir, "..", "themes", "Forest-ttk-theme-master", "forest-light.tcl")
            self.tk.call("source", theme_path)
            ttk.Style(self).theme_use("forest-light")
        except Exception as e:
            messagebox.showwarning("경고", f"Forest 테마 로드 실패: {e}")

        # === 전역 폰트 설정 (윈도우: 맑은 고딕) ===
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(family="맑은 고딕", size=10)

        text_font = tkfont.nametofont("TkTextFont")
        text_font.configure(family="맑은 고딕", size=10)

        fixed_font = tkfont.nametofont("TkFixedFont")
        fixed_font.configure(family="맑은 고딕", size=10)

        style = ttk.Style(self)
        style.configure(".", font=("맑은 고딕", 10))

        # 룰/시드 로딩
        self._load_rules()

        # 상태
        self.rows = []

        # === UI 조립 ===
        self._build_ui()

    # ------------------------------
    # 초기화
    # ------------------------------
    def _load_rules(self):
        try:
            self.weights = load_weights()
            self.oui = load_oui()
            pats = load_patterns()
            self.patterns = self.ssid_pats = self.kiosk = self.certified = None
            if isinstance(pats, tuple):
                if len(pats) >= 3:
                    self.ssid_pats, self.kiosk, self.certified = pats[0], pats[1], pats[2]
                    self.patterns = self.ssid_pats
                elif len(pats) == 2:
                    self.patterns, self.certified = pats
                    self.ssid_pats = self.patterns
                elif len(pats) == 1:
                    self.patterns = self.ssid_pats = pats[0]
            else:
                self.patterns = self.ssid_pats = pats
        except Exception as e:
            messagebox.showwarning("경고", f"룰셋 로딩 실패: {e}")
            self.weights, self.oui, self.patterns = {}, {}, None
            self.ssid_pats = self.kiosk = self.certified = None

    # ------------------------------
    # UI 조립
    # ------------------------------
    def _build_ui(self):
        self.toolbar = Toolbar(
            self,
            on_scan=self.scan_async,
            on_demo=self.show_demo,
            on_export_csv=self.export_csv,
            on_export_pdf=self.export_pdf_selected
        )
        self.toolbar.pack(fill="x", pady=(10, 0))

        # === Notebook 생성 ===
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, pady=(10, 10))

        # === 탭 1: 메인 ===
        main = ttk.Frame(self.nb)
        self.nb.add(main, text="메인")

        main.grid_rowconfigure(0, weight=2)   # 상단 (그래프/정보/점수)
        main.grid_rowconfigure(1, weight=4)   # 하단 (표 + AI 설명)

        main.grid_columnconfigure(0, weight=3)  # 그래프
        main.grid_columnconfigure(1, weight=1)  # Wi-Fi 요약
        main.grid_columnconfigure(2, weight=1)  # 보안 점수

        # --- (0,0) Wi-Fi 점수 그래프 ---
        graph_wrap = ttk.LabelFrame(main, text="WIFI 점수 그래프")
        graph_wrap.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.graph_panel = GraphPanel(graph_wrap)
        self.graph_panel.pack(fill="both", expand=True)

        # --- (0,1) WiFi 요약 정보 ---
        wifi_info_wrap = ttk.LabelFrame(main, text="전체 Wi-Fi 요약")
        wifi_info_wrap.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.wifi_info_panel = WifiInfoPanel(wifi_info_wrap)
        self.wifi_info_panel.pack(fill="both", expand=True)

        # --- (0,2) 보안 점수 & 단계 ---
        score_wrap = ttk.LabelFrame(main, text="보안 점수")
        score_wrap.grid(row=0, column=2, sticky="nsew")
        self.security_score_panel = SecurityScorePanel(score_wrap)
        self.security_score_panel.pack(fill="both", expand=True)

        # --- (1,0) 스캔 결과 표 ---
        table_wrap = ttk.LabelFrame(main, text="스캔 결과 표")
        table_wrap.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        btn_frame = ttk.Frame(table_wrap)
        btn_frame.pack(fill="x", pady=4)
        ttk.Button(btn_frame, text="CSV 내보내기", command=self.export_csv).pack(side="right", padx=4)
        ttk.Button(btn_frame, text="PDF 내보내기", command=self.export_pdf_selected).pack(side="right", padx=4)

        self.tree_panel = TreePanel(
            table_wrap,
            on_select=self.on_select_refresh,
            on_double=self.on_detail_popup
        )
        self.tree_panel.pack(fill="both", expand=True)

        # --- (1,1~2) AI 설명 ---
        ai_wrap = ttk.LabelFrame(main, text="AI 설명")
        ai_wrap.grid(row=1, column=1, columnspan=2, sticky="nsew", padx=5, pady=5)
        self.guide_panel = GuidePanel(ai_wrap)
        self.guide_panel.pack(fill="both", expand=True)

        # === 탭 2: 해킹 사례 설명 ===
        chat_tab = ChatTab(self.nb)
        self.nb.add(chat_tab, text="해킹 사례 설명")

    # ------------------------------
    # 이벤트/로직
    # ------------------------------
    def set_status(self, txt: str):
        self.toolbar.set_status(txt)

    def scan_async(self):
        def work():
            self.set_status("스캔 중...")
            try:
                items = scan()
                if not items:
                    self.set_status("스캔 결과 없음")
                self.show_scored(items)
            except Exception as e:
                self.set_status("스캔 실패")
                messagebox.showerror("오류", f"스캔 실패: {e}")
        threading.Thread(target=work, daemon=True).start()

    def show_demo(self):
        try:
            items = load_demo()
            self.show_scored(items)
            self.set_status("데모 데이터 표시 완료")
        except Exception as e:
            messagebox.showerror("오류", f"데모 데이터 로딩 실패: {e}")

    def show_scored(self, items):
        self.tree_panel.clear()
        self.rows = []

        for it in (items or []):
            try:
                r = score_entry_compat(
                    it, weights=self.weights, patterns=self.patterns,
                    oui=self.oui, ssid_pats=self.ssid_pats,
                    certified=self.certified, kiosk=self.kiosk
                )
            except Exception as e:
                r = {"ssid": it.get("ssid", ""), "bssid": it.get("bssid", ""),
                     "score": -1, "grade": "ERR",
                     "reasons": [f"스코어링 실패: {e}"],
                     "capabilities": it.get("capabilities", ""),
                     "signal": it.get("signal", ""),
                     "channel": it.get("channel", ""), "vendor": "", "role": "알수없음"}

            self.rows.append(r)
            self.tree_panel.insert_row(r)

        self.set_status(f"총 {len(self.rows)}개 결과")
        self.graph_panel.update_chart(self.rows)

        # (NEW) 스캔 직후 "전체 Wi‑Fi 요약" 생성/표시
        try:
            # 가이드 패널이 새 탭을 지원할 때만 동작
            if hasattr(self.guide_panel, "set_overall"):
                if not self.rows:
                    self.guide_panel.set_overall("스캔된 Wi‑Fi가 없습니다.")
                    return
                # 생성중 플레이스홀더
                self.guide_panel.set_overall("전체 Wi‑Fi 요약을 생성하는 중입니다…")
                # 최상위(가장 안전) AP 계산
                top = max(self.rows, key=lambda r: r.get("score", -1))

                def _gen_overall():
                    try:
                        if callable(summarize_overall):
                            text = summarize_overall(self.rows)  # type: ignore
                        else:
                            text = "요약 함수를 찾을 수 없습니다. ai_service.py 또는 ai_helper.py 에 summarize_overall 를 추가하세요."
                    except Exception as e:
                        text = f"[전체 요약 실패] {e}"
                    # UI 업데이트
                    self.after(0, lambda: self._apply_overall_text(text, top.get("ssid", "")))

                threading.Thread(target=_gen_overall, daemon=True).start()
        except Exception:
            # 전체 요약은 부가 기능이므로 실패해도 앱은 계속 동작
            pass

    # (NEW) 전체 요약 텍스트 적용 + 최상위 AP 빨간 강조
    def _apply_overall_text(self, text: str, top_ssid: str = ""):
        try:
            # (중요) 아래 탭은 삭제되었지만, PDF 용 캐시는 남겨둠
            if hasattr(self.guide_panel, "set_overall"):
                self.guide_panel.set_overall(text)
            # 상단 카드에 표시
            if hasattr(self, "wifi_info_panel") and self.wifi_info_panel:
                self.wifi_info_panel.set_text(text)
            # 상단/하단 모두 강조
            if top_ssid:
                if hasattr(self.wifi_info_panel, "highlight_top"):
                    self.wifi_info_panel.highlight_top(top_ssid)
        except Exception:
            pass

    def on_select_refresh(self, _evt=None):
        r = self.tree_panel.get_selected(self.rows)
        if not r:
            return

        # Wi-Fi 정보 텍스트 → 아래 'Wi-Fi 정보' 탭에만 표시 (새 탭)
        wifi_info_text = build_guidance(r)
        if hasattr(self.guide_panel, "set_wifi_info"):
            self.guide_panel.set_wifi_info(wifi_info_text)

        # 보안 점수
        self.security_score_panel.update_score(r.get("score", 0))

        # AI 설명/개발자 요약 플레이스홀더
        self.guide_panel.set_text("AI 설명 생성중...", "AI 설명 생성중...")

        # AI 백그라운드 실행
        def gen_ai():
            try:
                if not r.get("ai_explain"):
                    r["ai_explain"] = explain_with_ai(r)
                if not r.get("ai_summary"):
                    r["ai_summary"] = summarize_for_dev(r)

                explain_text = r.get("ai_explain", "")
                summary_text = r.get("ai_summary", "")
            except Exception as e:
                explain_text = f"[AI 설명 실패] {e}"
                summary_text = ""

            # 최종 반영: 첫 탭=AI 설명, 둘째 탭=개발자 요약
            self.after(0, lambda: self.guide_panel.set_text(explain_text, summary_text))

        threading.Thread(target=gen_ai, daemon=True).start()

    def on_detail_popup(self, _evt=None):
        r = self.tree_panel.get_selected(self.rows)
        if not r:
            return
        win = tk.Toplevel(self)
        win.title(f"세부 정보 - {r.get('ssid','')}")
        win.geometry("520x460")
        txt = tk.Text(win, wrap="word")
        txt.pack(fill="both", expand=True)
        for k, v in r.items():
            if isinstance(v, list):
                v = " | ".join(v)
            txt.insert("end", f"{k}: {v}\n")
        txt.configure(state="disabled")

    def export_csv(self):
        self.tree_panel.export_csv(self.rows)

    def export_pdf_selected(self):
        r = self.tree_panel.get_selected(self.rows)
        if not r:
            messagebox.showinfo("알림", "먼저 항목을 선택하세요.")
            return
        self.guide_panel.export_pdf(r, self.rows, self.graph_panel.fig)


if __name__ == "__main__":
    App().mainloop()

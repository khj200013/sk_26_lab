import tkinter as tk
from tkinter import ttk

class WifiInfoPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.txt = tk.Text(self, wrap="word", height=12, font=("맑은 고딕", 10))
        self.txt.pack(fill="both", expand=True)
        # 상단 요약에서 '가장 안전한 Wi-Fi' 강조 (빨간색 + 크게)
        self.txt.tag_configure("highlight", foreground="#A83244", font=("맑은 고딕", 12, "bold"))

    def set_info(self, wifi_data: dict):
        self.txt.configure(state="normal")
        self.txt.delete("1.0", "end")
        for k, v in wifi_data.items():
            self.txt.insert("end", f"{k}: {v}\n")
        self.txt.configure(state="disabled")

    def set_text(self, text: str):
        """일반 텍스트도 출력 가능"""
        self.txt.configure(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.insert("end", text or "")
        self.txt.configure(state="disabled")

    # (NEW) '가장 안전한 Wi-Fi' 한 줄 강조
    def highlight_top(self, ssid: str):
        if not ssid:
            return
        tv = self.txt
        tv.configure(state="normal")
        try:
            # SSID가 들어간 첫 줄 전체를 강조
            idx = tv.search(ssid, "1.0", tk.END)
            if idx:
                tv.tag_add("highlight", f"{idx} linestart", f"{idx} lineend")
        finally:
            tv.configure(state="disabled")


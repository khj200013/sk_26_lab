import tkinter as tk
from tkinter import ttk
import csv
from tkinter import filedialog

class TreePanel(ttk.Frame):
    def __init__(self, parent, on_select=None, on_double=None):
        super().__init__(parent)

        self.on_select = on_select
        self.on_double = on_double

        cols = ("SSID", "BSSID", "점수", "등급", "벤더", "신호", "채널")
        self.tree = ttk.Treeview(
            self, columns=cols, show="headings", height=15
        )

        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")

        # --- 스크롤바 추가 ---
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # 배치 (grid 사용 → 스크롤바와 함께 정렬)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 이벤트 바인딩
        if self.on_select:
            self.tree.bind("<<TreeviewSelect>>", self.on_select)
        if self.on_double:
            self.tree.bind("<Double-1>", self.on_double)

    # ------------------------
    def insert_row(self, r):
        self.tree.insert("", "end", values=(
            r.get("ssid", ""), r.get("bssid", ""), r.get("score", ""),
            r.get("grade", ""), r.get("vendor", ""), r.get("signal", ""),
            r.get("channel", "")
        ))

    def get_selected(self, rows):
        sel = self.tree.selection()
        if not sel:
            return None
        idx = self.tree.index(sel[0])
        return rows[idx] if 0 <= idx < len(rows) else None

    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def export_csv(self, rows):
        if not rows:
            return
        fpath = filedialog.asksaveasfilename(defaultextension=".csv",
                                             filetypes=[("CSV Files", "*.csv")])
        if not fpath:
            return
        with open(fpath, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["SSID", "BSSID", "점수", "등급", "벤더", "신호", "채널"])
            for r in rows:
                w.writerow([
                    r.get("ssid", ""), r.get("bssid", ""), r.get("score", ""),
                    r.get("grade", ""), r.get("vendor", ""), r.get("signal", ""),
                    r.get("channel", "")
                ])

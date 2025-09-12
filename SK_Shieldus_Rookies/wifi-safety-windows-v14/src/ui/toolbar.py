import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk  # Pillow 필요: pip install pillow
import os

class Toolbar(ttk.Frame):
    def __init__(self, parent, on_scan, on_demo, on_export_csv, on_export_pdf):
        super().__init__(parent)

        # Grid 레이아웃 2분할
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        # --- 왼쪽 영역 (로고 + 프로그램명) ---
        left_frame = ttk.Frame(self)
        left_frame.grid(row=0, column=0, sticky="w", padx=6)

        # 로고 이미지 불러오기
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            assets_dir = os.path.join(script_dir, "..", "..", "assets")
            logo_path = os.path.join(assets_dir, "logo.png")

            img = Image.open(logo_path)
            img = img.resize((32, 32), Image.LANCZOS)  # 크기 조정
            self.logo_img = ImageTk.PhotoImage(img)

            self.logo_label = ttk.Label(left_frame, image=self.logo_img)
            self.logo_label.pack(side="left")
        except Exception as e:
            # 실패 시 텍스트 대체
            self.logo_label = ttk.Label(left_frame, text="🛡️", font=("Arial", 20))
            self.logo_label.pack(side="left")

        self.app_name = ttk.Label(left_frame, text="공용 Wi-Fi 안전도 점검", font=("Arial", 16, "bold"))
        self.app_name.pack(side="left", padx=6)

        # --- 오른쪽 영역 (상태 + 버튼) ---
        right_frame = ttk.Frame(self)
        right_frame.grid(row=0, column=1, sticky="e", padx=6)

        ttk.Button(right_frame, text="스캔", command=on_scan, style="Accent.TButton").pack(side="right", padx=4, pady=2)
        ttk.Button(right_frame, text="데모", command=on_demo, style="TButton").pack(side="right", padx=4, pady=2)

        self.status_var = tk.StringVar(value="준비됨")
        ttk.Label(right_frame, textvariable=self.status_var).pack(side="right", padx=8)

    def set_status(self, txt: str):
        self.status_var.set(txt)

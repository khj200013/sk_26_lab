import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class SecurityScorePanel(ttk.Frame):
    """보안 점수 도넛 반원 그래프"""

    def __init__(self, parent):
        super().__init__(parent)

        self.fig = Figure(figsize=(3,2))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # 등급 표시용 Label (하단 고정)
        self.label_grade = ttk.Label(self, font=("맑은 고딕", 11, "bold"))
        self.label_grade.pack(side="bottom", pady=(2, 2))

    def update_score(self, score: int):
        self.ax.clear()

        # 점수에 따른 색상과 등급
        if score < 40:
            color, grade = "#A83244", "위험"
        elif score < 70:
            color, grade = "#E6B422", "관심"
        else:
            color, grade = "#2C6E91", "안전"

        # 도넛 반원 데이터
        val = score
        remain = 100 - val
        self.ax.pie(
            [val, remain],
            startangle=180,           # 반원 시작 (180°부터)
            colors=[color, "lightgray"],
            radius=1,
            counterclock=False,
            wedgeprops=dict(width=0.3)  # 도넛 두께
        )

        # 중앙에 점수 표시
        self.ax.text(0, 0, f"{score}", ha="center", va="center",
                     fontsize=14, weight="bold", color=color)
        # 도넛 내부에 등급 텍스트(관심/안전/위험) 추가
        self.ax.text(0, -0.35, f"{grade}", ha="center", va="center",
                     fontsize=10, weight="bold", color=color)

        # 축 숨기기
        self.ax.set(aspect="equal")  # 원형 비율 유지
        self.ax.axis("off")

        # 🔑 여백 줄이기
        self.fig.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.05)
        self.fig.tight_layout(pad=0)

        # 등급 라벨 업데이트
        self.label_grade.configure(text=f"등급: {grade}", foreground=color)

        self.canvas.draw()

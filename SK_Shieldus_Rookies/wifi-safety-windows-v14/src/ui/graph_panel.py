# ui/graph_panel.py
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from utils.font import ensure_korean_font
import numpy as np
from scipy.interpolate import make_interp_spline


class GraphPanel(ttk.Frame):
    """Wi-Fi 점수 그래프 패널"""

    def __init__(self, parent):
        super().__init__(parent)

        ensure_korean_font()

        self.fig = Figure(figsize=(5, 2.5), dpi=100, constrained_layout=False)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_ylabel("점수")
        self.ax.grid(True, alpha=0.3)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # 데이터 저장
        self.scores = []
        self.labels = []
        self.scatter = None
        self.annot = None

        # 이벤트 연결 (한 번만)
        self.canvas.mpl_connect("motion_notify_event", self.on_hover)

    def update_chart(self, rows):
        """스코어링 결과(rows)를 받아 차트를 갱신"""
        self.ax.clear()
        self.ax.set_ylabel("점수")
        self.ax.grid(True, alpha=0.3)

        if not rows:
            self.ax.text(0.5, 0.5, "표시할 데이터가 없습니다.",
                         ha='center', va='center', transform=self.ax.transAxes)
            self.canvas.draw()
            return

        self.scores = [r.get("score", 0) for r in rows]
        self.labels = [r.get("ssid", "") for r in rows]

        x = np.arange(1, len(self.scores) + 1)

        # --- 1) 곡선화된 선 만들기 ---
        if len(x) > 3:  # 보간은 3개 이상 점 필요
            x_smooth = np.linspace(x.min(), x.max(), 200)
            spline = make_interp_spline(x, self.scores, k=3)
            y_smooth = spline(x_smooth)
            self.ax.plot(x_smooth, y_smooth, linewidth=1.8, color='#217346')
        else:
            self.ax.plot(x, self.scores, linewidth=1.8, color='#217346')

        # --- 2) 점 표시 ---
        self.scatter = self.ax.scatter(x, self.scores, s=50, c="#217346", zorder=3)

        # X축, Y축 범위 고정
        self.ax.set_xlim(0.5, len(self.scores) + 0.5)
        self.ax.set_ylim(0, 100)  # 항상 0~100 점수 범위
        self.ax.set_autoscale_on(False)

        # X축 라벨 제거
        self.ax.set_xticks(x)
        self.ax.set_xticklabels([])

        # --- 3) tooltip annotation 새로 생성 ---
        self.annot = self.ax.annotate(
            "", xy=(0, 0), xytext=(10, 10), textcoords="offset points",
            fontsize=9, fontweight="bold", color="black",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="none", alpha=0.9),
            arrowprops=dict(arrowstyle="-", color="black", lw=0.8)  # 점에서 직선 연결
        )
        self.annot.set_visible(False)
        self.annot.set_clip_on(False)

        self.canvas.draw()

    def on_hover(self, event):
        """마우스 호버 시 SSID + 점수 표시 (자동 위치 보정 포함)"""
        if event.inaxes == self.ax and self.scatter is not None:
            cont, ind = self.scatter.contains(event)
            if cont:
                idx = ind["ind"][0]
                pos = self.scatter.get_offsets()[idx]
                self.annot.xy = pos
                self.annot.set_text(f"{self.labels[idx]} ({self.scores[idx]}점)")

                # 자동 위치 조정
                x_disp, y_disp = self.ax.transData.transform(pos)
                x0, y0 = self.ax.transAxes.transform((0, 0))
                x1, y1 = self.ax.transAxes.transform((1, 1))

                offset_x, offset_y = 10, 10
                if x_disp > x1 - 50:
                    offset_x = -50
                if y_disp > y1 - 30:
                    offset_y = -30
                if y_disp < y0 + 30:
                    offset_y = 30

                self.annot.set_position((offset_x, offset_y))

                self.annot.set_visible(True)
                self.canvas.draw_idle()
            else:
                if self.annot and self.annot.get_visible():
                    self.annot.set_visible(False)
                    self.canvas.draw_idle()

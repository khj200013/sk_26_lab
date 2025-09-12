import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from services.ai_helper import explain_attack_with_ai  # 기존 함수

BUBBLE_MAX_WIDTH = 680
SIDE_PAD_X       = 40
WRAP_RATIO       = 0.92

class HackingChat(ttk.Frame):
    def __init__(self, master=None, topics=None, **kwargs):
        super().__init__(master, **kwargs)
        self.pack(fill="both", expand=True)

        # 기본 주제
        self.all_topics = topics or [
            "ARP 스푸핑", "Evil Twin", "SSL Strip", "DNS 하이재킹",
            "Deauth 공격", "KRACK", "피싱(캡티브 포털 악용)", "DNS 스푸핑"
        ]
        self.filtered = list(self.all_topics)

        # ── 좌우 레이아웃 ─────────────────────────────
        paned = ttk.Panedwindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True)

        # ── 좌측: 주제 목록 ───────────────────────────
        left = ttk.Frame(paned, padding=(6,6,6,6))
        paned.add(left, weight=1)   # 비율은 밑에서 수정됨

        ttk.Label(left, text="해킹 사례 목록", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0,6))

        search_row = ttk.Frame(left); search_row.pack(fill="x", pady=(0,6))
        self.search_var = tk.StringVar()
        se = ttk.Entry(search_row, textvariable=self.search_var)
        se.pack(side="left", fill="x", expand=True)
        ttk.Button(search_row, text="🔍", command=self._on_search).pack(side="left", padx=(4,0))
        se.bind("<Return>", lambda e: self._on_search())

        # Treeview 스타일 목록
        self.topic_tree = ttk.Treeview(left, show="tree", selectmode="browse", height=14)
        self.topic_tree.pack(fill="both", expand=True)

        for t in self.filtered:
            self.topic_tree.insert("", "end", text=t)

        # "설명 보기" 버튼 (가로 꽉차게, accent 스타일)
        self.run_btn = ttk.Button(left, text="📖 설명 보기", style="Accent.TButton", command=self._run_selected)
        self.run_btn.pack(fill="x", pady=(6,0))

        # ── 좌/우 사이 경계선 ───────────────────────────
        sep = ttk.Separator(paned, orient="vertical")
        paned.add(sep, weight=0)   # weight=0 → 크기 고정

        # ── 우측: 채팅 영역 ───────────────────────────
        right = ttk.Frame(paned, padding=(6,6,6,6))
        paned.add(right, weight=3)  # 좌측 1, 우측 3

        # 툴바
        toolbar = ttk.Frame(right); toolbar.pack(fill="x", pady=(0,6))
        ttk.Label(toolbar, text="난이도:").pack(side="left")
        self.level_var = tk.StringVar(value="초보자")
        ttk.Combobox(toolbar, textvariable=self.level_var,
                     values=["초보자","중급","전문가"], width=6,
                     state="readonly").pack(side="left", padx=(4,8))

        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=6)

        # 버튼들 → 아이콘+텍스트
        self.copy_btn  = ttk.Button(toolbar, text="📋 복사", command=self._copy_text);  self.copy_btn.pack(side="left", padx=2)
        self.clear_btn = ttk.Button(toolbar, text="🗑 초기화", command=self._clear_chat); self.clear_btn.pack(side="left", padx=2)
        self.save_btn  = ttk.Button(toolbar, text="💾 저장", command=self._save_text);  self.save_btn.pack(side="left", padx=2)

        # 상태바
        statusbar = ttk.Frame(right); statusbar.pack(fill="x", pady=(4,0))
        self.status_var = tk.StringVar(value="준비됨")
        ttk.Label(statusbar, textvariable=self.status_var).pack(side="left", padx=(6,0))
        self.progress = ttk.Progressbar(statusbar, mode="indeterminate", length=100)
        self.progress.pack(side="right", padx=(0,6))

        # 채팅 영역
        chat_wrap = ttk.Frame(right); chat_wrap.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(chat_wrap, highlightthickness=0, bg="white")
        self.vsb = ttk.Scrollbar(chat_wrap, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.vsb.pack(side="right", fill="y")

        self.chat_frame = tk.Frame(self.canvas, bg="white")
        self.canvas_window = self.canvas.create_window((0,0), window=self.chat_frame, anchor="nw")
        self.chat_frame.columnconfigure(0, weight=1)

        self.chat_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        if self.topic_tree.get_children():  # 기본 선택
            first = self.topic_tree.get_children()[0]
            self.topic_tree.selection_set(first)

        self._busy = False
        self._row = 0
        self._bubbles = []
        self._wrap_current = BUBBLE_MAX_WIDTH

    # ── 좌측 검색 & 실행 ─────────────────────────────
    def _on_search(self, _evt=None):
        q = (self.search_var.get() or "").strip().lower()
        for i in self.topic_tree.get_children():
            self.topic_tree.delete(i)
        self.filtered = [t for t in self.all_topics if q in t.lower()] if q else list(self.all_topics)
        for t in self.filtered:
            self.topic_tree.insert("", "end", text=t)
        if self.topic_tree.get_children():
            first = self.topic_tree.get_children()[0]
            self.topic_tree.selection_set(first)

    def _run_selected(self):
        sel = self.topic_tree.selection()
        topic = self.topic_tree.item(sel[0], "text") if sel else ""
        if not topic:
            messagebox.showinfo("안내", "주제를 선택하거나 직접 입력하세요.")
            return
        self.ask_topic(topic)

    # ── 채팅 ────────────────────────────────────────
    def _compose_prompt_hint(self):
        return f" — (난이도:{self.level_var.get()})"

    def ask_topic(self, topic: str):
        if self._busy: return
        topic = (topic or "").strip()
        if not topic: return

        self._add_bubble("user", f"{topic}이(가) 궁금해요")
        self._set_busy(True)

        def worker():
            try:
                answer = explain_attack_with_ai(topic + self._compose_prompt_hint())
            except Exception as e:
                answer = f"[오류] {e}"
            finally:
                self._set_busy(False)
            self._add_bubble("ai", answer)

        threading.Thread(target=worker, daemon=True).start()

    def _add_bubble(self, role: str, text: str):
        container = tk.Frame(self.chat_frame, bg="white")
        container.grid(row=self._row, column=0, sticky="ew",
                       padx=(SIDE_PAD_X, SIDE_PAD_X), pady=(4,4))
        self._row += 1

        if role == "user":
            bg, fg, anchor = "#0b57d0", "white", "e"
        else:
            bg, fg, anchor = "#f1f1f1", "black", "w"

        msg = tk.Message(
            container, text=text, width=self._wrap_current,
            bg=bg, fg=fg, font=("Segoe UI", 10), padx=14, pady=8,
            relief="flat"
        )
        msg.pack(side=("right" if role=="user" else "left"), anchor=anchor)

        self._bubbles.append((msg, role))
        self.chat_frame.update_idletasks()
        self.canvas.yview_moveto(1.0)

    # ── 기능 버튼 ────────────────────────────────────
    def _copy_text(self):
        try:
            text = self._collect_plaintext()
            if not text.strip(): return
            self.clipboard_clear(); self.clipboard_append(text)
            self.status_var.set("복사됨"); self.after(1500, lambda: self.status_var.set("준비됨"))
        except Exception:
            pass

    def _save_text(self):
        text = self._collect_plaintext()
        if not text.strip():
            messagebox.showinfo("안내", "저장할 내용이 없습니다."); return
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text","*.txt")])
        if not path: return
        try:
            with open(path, "w", encoding="utf-8") as f: f.write(text)
            self.status_var.set("저장 완료"); self.after(1500, lambda: self.status_var.set("준비됨"))
        except Exception as e:
            messagebox.showerror("오류", f"저장 실패: {e}")

    def _clear_chat(self):
        for child in self.chat_frame.winfo_children(): child.destroy()
        self._row = 0; self._bubbles.clear()
        self.canvas.yview_moveto(0.0)

    def _collect_plaintext(self):
        lines = []
        for bubble, role in self._bubbles:
            prefix = "[사용자]" if role == "user" else "[AI]"
            lines.append(f"{prefix} {bubble.cget('text')}")
            lines.append("")
        return "\n".join(lines)

    # ── 상태 관리 ────────────────────────────────────
    def _set_busy(self, busy: bool):
        self._busy = busy
        state = "disabled" if busy else "normal"
        for w in (self.run_btn, self.copy_btn, self.clear_btn, self.save_btn):
            w.configure(state=state)
        if busy:
            self.status_var.set("생성 중…"); self.progress.start(10)
        else:
            self.progress.stop(); self.status_var.set("준비됨")

    # ── 스크롤/리사이즈 ──────────────────────────────
    def _on_frame_configure(self, _evt=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, evt=None):
        canvas_width = evt.width if evt else self.canvas.winfo_width()
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)
        avail = max(160, int(canvas_width * WRAP_RATIO) - SIDE_PAD_X * 2)
        self._wrap_current = min(BUBBLE_MAX_WIDTH, avail)
        for lbl, _ in self._bubbles:
            lbl.configure(width=self._wrap_current)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Wi-Fi 해킹 사례 교육")
    root.geometry("900x560")
    app = HackingChat(root)
    root.mainloop()

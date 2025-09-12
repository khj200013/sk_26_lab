from tkinter import ttk

try:
    from scripts.hacking_chat import HackingChat
except Exception:
    HackingChat = None

class ChatTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        if HackingChat is not None:
            try:
                self.chat_widget = HackingChat(self)
                self.chat_widget.pack(fill="both", expand=True)
            except Exception as e:
                ttk.Label(self, text=f"HackingChat 로딩 실패: {e}").pack(fill="both", expand=True)
        else:
            ttk.Label(
                self,
                text="hacking_chat 모듈을 찾을 수 없어 탭을 대체합니다.",
                justify="center"
            ).pack(fill="both", expand=True, padx=16, pady=16)

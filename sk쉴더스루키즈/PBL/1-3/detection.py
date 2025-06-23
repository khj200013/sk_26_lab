import os
import time
import re
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_DIR = "./monitor_directory"

EXTENSIONS = {
    '.py': 'Python Script',
    '.js': 'JavaScript',
    '.class': 'Java Class File'
}

SENSITIVE_PATTERNS = {
    "주석": r"(#.*|//.*|/\*[\s\S]*?\*/)",
    "이메일": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    "SQL": r"\b(SELECT|INSERT|UPDATE|DELETE)\b\s+.*?\b(FROM|INTO|SET|WHERE)\b"
}

# 분석한 파일 기록 (중복 분석 방지)
analyzed_files = {}

def detect_sensitive_info(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            found = False

            for info_type, pattern in SENSITIVE_PATTERNS.items():
                if re.search(pattern, content, re.IGNORECASE):
                    print(f"[민감 정보 탐지] {info_type} 포함 - {file_path}")
                    found = True

            if not found:
                print(f"[안전 파일] 민감 정보 없음 - {file_path}")

    except Exception as e:
        print(f"파일 분석 중 오류 발생: {file_path} - {str(e)}")

class MonitorHandler(FileSystemEventHandler):
    def process_file(self, file_path):
        ext = os.path.splitext(file_path)[1]

        if file_path in analyzed_files and os.path.getmtime(file_path) == analyzed_files[file_path]:
            return  # 이미 분석한 파일은 생략

        print(f"[파일 처리] {file_path}")

        if ext in EXTENSIONS:
            print(f"[확장자 분류] {EXTENSIONS[ext]} 파일로 분류됨")
        else:
            print(f"[확장자 경고] 주의가 필요한 파일 확장자: {ext}")

        detect_sensitive_info(file_path)
        analyzed_files[file_path] = os.path.getmtime(file_path)

    def on_created(self, event):
        if not event.is_directory:
            time.sleep(0.5)  # 잠깐 기다린 후 분석
            self.process_file(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            time.sleep(0.5)  # 잠깐 기다린 후 분석
            self.process_file(event.src_path)

if __name__ == "__main__":
    print(f"모니터링 시작: {WATCH_DIR}")

    if not os.path.exists(WATCH_DIR):
        os.makedirs(WATCH_DIR)

    observer = Observer()
    event_handler = MonitorHandler()
    observer.schedule(event_handler, path=WATCH_DIR, recursive=True)

    try:
        observer.start()
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        observer.stop()
    observer.join()

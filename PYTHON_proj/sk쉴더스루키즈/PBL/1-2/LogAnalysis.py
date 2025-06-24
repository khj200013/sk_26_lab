import re
from collections import Counter
import csv
import os

class IPAnalyzer:
    def __init__(self, log_file_path):
        self.log_file_path = log_file_path
        self.ip_counter = Counter()

    # 로그 파일에서 IP 추출
    def extract_ips(self):
        if not os.path.exists(self.log_file_path):
            print(f"입력한 경로에 파일이 존재하지 않습니다: {self.log_file_path}")
            return False

        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    ip_match = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', line)

                    if ip_match:
                        ip = ip_match.group()
                        self.ip_counter[ip] += 1
            return True
        
        except Exception as e:
            print(f"파일 읽기 중 문제 발생: {e}")
            return False

    # 상위 3개 IP 반환
    def get_top_ips(self, n=3):
        return self.ip_counter.most_common(n)

    # 결과를 CSV로 저장
    def save_to_csv(self, output_file=r"C:\Users\khj98\Documents\python\1-2\ip_analysis.csv"):
        try:
            with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['IP Address', 'Count'])

                for ip, count in self.ip_counter.items():
                    writer.writerow([ip, count])
            print(f"분석 결과가 '{output_file}'에 저장되었습니다.")

        except Exception as e:
            print(f"CSV 저장 실패: {e}")

    # 요약 출력
    def print_summary(self):
        print("\n 상위 3개 접속 IP 주소:")
        
        for ip, count in self.get_top_ips():
            print(f" - {ip} : {count}회")

# 메인 실행부
if __name__ == "__main__":
    log_file_path = input("분석할 로그 파일 경로를 입력하세요: ").strip()

    analyzer = IPAnalyzer(log_file_path)

    if analyzer.extract_ips():
        analyzer.print_summary()
        analyzer.save_to_csv()
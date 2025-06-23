class StudentScores:
    def __init__(self, filename):
        self.filename = filename
        self.scores = {}

        try:
            with open(self.filename, 'r', encoding='utf-8') as file:
                for line in file:
                    name, score = line.strip().split(',')
                    self.scores[name] = int(score)
        except FileNotFoundError:
            print(f"파일 '{self.filename}'을(를) 찾을 수 없습니다.")
        except Exception as e:
            print(f"파일 처리 중 문제가 발생했습니다: {e}")

    def calculate_average(self):
        if not self.scores:
            return 0
        return sum(self.scores.values()) / len(self.scores)

    def get_above_average(self):
        average = self.calculate_average()
        return [name for name, score in self.scores.items() if score >= average]

    def save_below_average(self, output_file=r"C:\Users\khj98\Documents\python\20250611_164731_scores_korean\below_average_korean.txt"):
        average = self.calculate_average()
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for name, score in self.scores.items():
                    if score < average:
                        f.write(f"{name},{score}\n")
            print(f"평균 미만 학생 정보를 '{output_file}'에 저장했습니다.")
        except Exception as e:
            print(f"파일 저장 중 문제가 발생했습니다: {e}")

    def print_summary(self):
        average = self.calculate_average()
        above_list = self.get_above_average()
        print("학생 성적 요약")
        print(f" - 전체 평균 점수: {average:.2f}")
        print(" - 평균 이상 학생:")
        for name in above_list:
            print(f"   · {name}")


# 예시 실행 코드
if __name__ == "__main__":
    score_manager = StudentScores(r"C:\Users\khj98\Documents\python\20250611_164731_scores_korean\scores_korean.txt")
    score_manager.save_below_average()
    score_manager.print_summary()
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

matplotlib.rc('font', family='Malgun Gothic')  # 한글 폰트 설정
plt.rcParams['axes.unicode_minus'] = False     # 마이너스 기호 깨짐 방지

class StudentScoreAnalysis:
    def __init__(self):
        # 학생 이름 리스트
        self.students = [f'학생{i+1}' for i in range(20)]

        # 과목 점수 랜덤 생성 (50 ~ 100)
        np.random.seed(42)  # 결과 재현
        self.scores = {
            '이름': self.students,
            '수학': np.random.randint(50, 101, size=20),
            '영어': np.random.randint(50, 101, size=20),
            '과학': np.random.randint(50, 101, size=20)
        }

        # 데이터프레임 생성
        self.df = pd.DataFrame(self.scores)

        # 평균 컬럼 추가
        self.df['평균'] = self.df[['수학', '영어', '과학']].mean(axis=1)

    def plot_subject_avg(self):
        # 과목별 평균 점수 계산
        subject_avg = self.df[['수학', '영어', '과학']].mean()

        # 시각화
        plt.figure(figsize=(8, 5))
        subject_avg.plot(kind='bar', color=['skyblue', 'lightgreen', 'salmon'])
        plt.title('과목별 평균 점수')
        plt.ylabel('점수')
        plt.ylim(0, 100)
        plt.grid(axis='y')
        plt.tight_layout()
        plt.show()

    def plot_top5_students(self):
        # 평균 점수 기준 상위 5명 정렬
        top5 = self.df.sort_values(by='평균', ascending=False).head(5)

        # 시각화
        plt.figure(figsize=(8, 5))
        plt.bar(top5['이름'], top5['평균'], color='orange')
        plt.title('평균 성적 상위 5명')
        plt.ylabel('평균 점수')
        plt.ylim(0, 100)
        plt.grid(axis='y')
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    analyzer = StudentScoreAnalysis()
    print(analyzer.df)  # 학생 성적 출력
    analyzer.plot_subject_avg()
    analyzer.plot_top5_students()

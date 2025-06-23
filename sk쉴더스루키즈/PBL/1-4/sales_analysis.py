import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

class SalesAnalysis:
    def __init__(self):
        # 날짜 생성
        self.dates = pd.date_range(start='2024-01-01', end='2024-12-31')
        
        # 일별 매출 랜덤 생성 (1000 ~ 10000)
        np.random.seed(42)  # 결과 재현을 위해 시드 고정
        self.sales = np.random.randint(1000, 10001, size=len(self.dates))
        
        # DataFrame 구성
        self.df = pd.DataFrame({'날짜': self.dates, '매출': self.sales})
        self.df['월'] = self.df['날짜'].dt.month

    def analyze_monthly_sales(self):
        # 월별 매출 합계 계산
        monthly_sales = self.df.groupby('월')['매출'].sum().reset_index()
        return monthly_sales

    def plot_sales(self, monthly_sales):
        # 한글 폰트 설정 (시스템에 따라 다를 수 있음)
        plt.rcParams['font.family'] = 'AppleGothic' if 'AppleGothic' in fm.findSystemFonts(fontpaths=None, fontext='ttf') else 'Malgun Gothic'
        plt.rcParams['axes.unicode_minus'] = False

        # 그래프 출력
        plt.figure(figsize=(10, 5))
        plt.plot(monthly_sales['월'], monthly_sales['매출'], marker='o', color='blue', linewidth=2)
        plt.title('2024년 월별 매출 추이')
        plt.xlabel('월')
        plt.ylabel('매출 합계')
        plt.grid(True)
        plt.xticks(range(1, 13))
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    sa = SalesAnalysis()
    monthly_data = sa.analyze_monthly_sales()

    print(monthly_data)  # 결과 확인용
    
    sa.plot_sales(monthly_data)

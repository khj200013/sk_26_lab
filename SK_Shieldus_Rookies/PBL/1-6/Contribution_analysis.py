import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import random
from datetime import datetime, timedelta

# 한글 폰트 설정
matplotlib.rc('font', family='Malgun Gothic')
plt.rcParams['axes.unicode_minus'] = False

class CustomerSalesAnalysis:
    def __init__(self):
        self.df = self._generate_sample_data()

    def _generate_sample_data(self):
        customers = [f'고객{i}' for i in range(1, 11)]
        products = ['상품A', '상품B', '상품C']
        start_date = datetime(2024, 1, 1)
        data = []

        for _ in range(300):
            customer = random.choice(customers)
            product = random.choice(products)
            quantity = random.randint(1, 5)
            unit_price = random.randint(10000, 50000)
            purchase_date = start_date + timedelta(days=random.randint(0, 364))

            data.append({
                '고객명': customer,
                '구매일자': purchase_date,
                '상품명': product,
                '수량': quantity,
                '단가': unit_price,
                '총매출': quantity * unit_price
            })

        return pd.DataFrame(data)

    def show_monthly_sales_bar_chart(self):
        self.df['월'] = self.df['구매일자'].dt.to_period('M')
        monthly_sales = self.df.groupby('월')['총매출'].sum()

        monthly_sales.plot(kind='bar', figsize=(10, 5), title='월별 매출 총합')
        
        plt.xlabel('월')
        plt.ylabel('총매출')
        plt.tight_layout()
        plt.show()

    def show_customer_sales_pie_chart(self):
        customer_sales = self.df.groupby('고객명')['총매출'].sum()
        customer_sales.sort_values(ascending=False).plot(kind='pie', autopct='%.1f%%', figsize=(8, 8), title='고객별 누적 매출 비율')
        
        plt.ylabel('')
        plt.tight_layout()
        plt.show()

    def run_all(self):
        print("==== [데이터 미리보기] ====")
        print(self.df.head())
        print("\n==== [총 데이터 건수] ====")
        print(len(self.df))
        
        self.show_monthly_sales_bar_chart()
        self.show_customer_sales_pie_chart()

if __name__ == '__main__':
    analysis = CustomerSalesAnalysis()
    analysis.run_all()

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt
import seaborn as sns

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 1. 데이터 로드
df = pd.read_csv("20250618_175248_diabetes.csv")  # 파일명 확인

# 2. 결측치 처리
# 0을 결측치로 간주할 열
cols = ['Glucose', 'BloodPressure', 'SkinThickness', 'Insulin', 'BMI']
df[cols] = df[cols].replace(0, np.nan)

# 평균으로 결측치 대체 (apply 사용)
df[cols] = df[cols].apply(lambda col: col.fillna(col.mean()))

# 3. 이상치 처리 (SkinThickness, Insulin에서 상위 1% 이상치 → 평균으로 대체)
def replace_top_1_percent_with_mean(col):
    threshold = col.quantile(0.99)
    mean_val = col.mean()
    return col.apply(lambda x: mean_val if x > threshold else x)

df['SkinThickness'] = replace_top_1_percent_with_mean(df['SkinThickness'])
df['Insulin'] = replace_top_1_percent_with_mean(df['Insulin'])

# 4. Age 정규화 (0~1 범위로 MinMaxScaler 사용)
scaler = MinMaxScaler()
df['Age'] = scaler.fit_transform(df[['Age']])

# 5. EDA

# (1) 각 열의 결측치 개수 출력
print("각 열의 결측치 개수")
print(df.isnull().sum())

# (2) Outcome 별 Glucose 평균 출력
print("\n Outcome 별 Glucose 평균")
print(df.groupby('Outcome')['Glucose'].mean())

# (3) 전처리 후 데이터프레임 상위 5개 행 출력
print("\n 전처리 후 상위 5개 행")
print(df.head())

# (4) 추가 시각화 (선택 사항)
plt.figure(figsize=(6, 4))
sns.countplot(x='Outcome', data=df)
plt.title("Outcome 분포")
plt.xlabel("Outcome (0: 정상, 1: 당뇨)")
plt.ylabel("개수")
plt.show()

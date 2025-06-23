import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# 1. 데이터 불러오기
df = pd.read_csv("20250620_143716_train.csv")

# 2. 결측값 처리
# (1) 결측치 비율이 높은 열 제거
missing_ratio = df.isnull().mean()

# 'LotFrontage'를 제외하고 결측치 비율 50% 초과하는 열 제거
cols_to_drop = missing_ratio[(missing_ratio > 0.5) & (missing_ratio.index != 'LotFrontage')].index
df.drop(columns=cols_to_drop, inplace=True)

# LotFrontage는 평균으로 결측치 대체
if 'LotFrontage' in df.columns:
    df['LotFrontage'] = df['LotFrontage'].fillna(df['LotFrontage'].mean())

# 3. 불필요한 열 제거
if 'Id' in df.columns:
    df.drop(columns=['Id'], inplace=True)

# 4. 범주형 변수 인코딩
df = pd.get_dummies(df)

# 5. 피처/타겟 분리
X = df.drop(columns=['SalePrice'])
y = df['SalePrice']

# 6. 학습/테스트 데이터 분리 (8:2 비율)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 7. 모델 학습
model = DecisionTreeRegressor(random_state=42)
model.fit(X_train, y_train)

# 8. 예측
y_pred = model.predict(X_test)

# 9. 평가
mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
r2 = r2_score(y_test, y_pred)

# 10. 출력
print(f"MAE (Mean Absolute Error): {mae:.2f}")
print(f"MSE (Mean Squared Error): {mse:.2f}")
print(f"RMSE (Root Mean Squared Error): {rmse:.2f}")
print(f"R2 Score: {r2:.4f}")

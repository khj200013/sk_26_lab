import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report

# 1. 데이터 로딩
df = pd.read_csv("2_4_web_server_logs_2.csv")

# 2. timestamp → datetime 변환 후 hour 파생 변수 생성
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['hour'] = df['timestamp'].dt.hour    # timestamp에서 hour만 추출

# 3. 상태 코드로 is_error 파생 변수 생성 (400 이상: 에러)
df['is_error'] = (df['status_code'] >= 400).astype(int) # 400이상인 status_code의 개수: 435

# 4. 범주형 변수 인코딩 (method만 사용, ip는 제외)
df_encoded = pd.get_dummies(df, columns=['method'], drop_first=True)

# 5. 특성(X), 타깃(y) 분리
X = df_encoded.drop(columns=['timestamp', 'ip', 'label'])  # ip는 학습에 사용하지 않음
y = df_encoded['label']  # 타깃: 정상(0) / 악성(1)

# 6. 수치형 특성 정규화
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 7. 학습/테스트 데이터 분할
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# 8. 모델 학습 (Logistic Regression)
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

# 9. 예측 및 평가
y_pred = model.predict(X_test)
report = classification_report(y_test, y_pred, digits=4)

# 10. 결과 출력
print("[악성 요청 분류 결과 - Classification Report]")
print(report)

# 11. 결과 해석
print("\n전체 요약")
print("전체 테스트 데이터: 300건")
print("이 중 악성(label = 1) 요청: 95건 (31.7%)")
print("전체 요청 중 악성 요청 비율(전체 데이터 기준): 약 27.33%\n")

print(" 클래스별 평가 지표 해석")
print("{:<6} {:<10} {:<10} {:<10} {:<10} {:<10}".format("클래스", "설명", "Precision", "Recall", "F1-Score", "지원 수"))
print("{:<6} {:<10} {:<10} {:<10} {:<10} {:<10}".format("0", "정상 요청", "93.03%", "91.22%", "92.12%", "205건"))
print("{:<6} {:<10} {:<10} {:<10} {:<10} {:<10}".format("1", "악성 요청", "81.82%", "85.26%", "83.51%", "95건"))
print()

print(" Precision (정밀도)")
print("1 클래스의 정밀도: 81.82%")
print("모델이 \"악성\"이라고 예측한 것 중 실제로 악성인 비율")
print("→ False Positive가 적을수록 높아짐\n")

print(" Recall (재현율)")
print("1 클래스의 재현율: 85.26%")
print("실제 악성 요청 중에서 모델이 정확히 잡아낸 비율")
print("→ False Negative가 적을수록 높음")
print("보안에서는 재현율이 매우 중요 (악성 놓치면 안 되니까)\n")

print(" F1-Score")
print("1 클래스의 F1-score: 83.51%")
print("정밀도와 재현율의 조화 평균")
print("정밀도와 재현율의 균형을 잘 맞춘 결과")
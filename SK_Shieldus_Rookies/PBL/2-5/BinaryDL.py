# 데이터 개요
# 샘플 수: 2000개
# 특성 수: 6개 (Age, Tenure, MonthlySpending_KRW, ContractType, CustomerServiceCalls, IsChurn)
# 결측치: 없음

# ===============================================================================================
# ===============================================================================================

# 변수별 통계 요약
# 변수                      설명                    평균    		표준편차
# Age	                고객 나이                   43.8세	         14.93
# Tenure	            서비스 이용 개월 수          29.7개월		  16.84
# MonthlySpending_KRW   월 지출                    266,740		    136,766
# ContractType	        계약 형태(0: 월 단위, 1: 1년, 2: 2년)
# CustomerServiceCalls  고객센터 이용 횟수            4.53회		  2.91
# IsChurn	            이탈 여부(0: 잔류, 1: 이탈)	  37.9%가 이탈     0.485

# ===============================================================================================
# ===============================================================================================

# 주요 인사이트
# 나이 분포: 고객의 연령대는 평균 43.8세이며, 전반적으로 30대~50대에 집중.

# 이용 기간(Tenure): 평균 약 30개월 사용, 최장 59개월까지 있음.

# 지출: 월 평균 26만 원, 최대 50만 원으로 큰 차이 → 지출이 churn과 어떤 관계인지 분석 가치 있음.

# 계약 형태: ContractType은 범주형 변수로 원-핫 인코딩 필요

# 이탈자 비율: 2000명 중 758명(37.9%)이 이탈 → 클래스 비율 균형 잡힘


import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report

# 1. 데이터 로드 및 탐색
df = pd.read_csv('2_5_customer_data_balanced.csv')

# ContractType One-hot 인코딩
contract_dummies = pd.get_dummies(df['ContractType'], prefix='Contract')
df = pd.concat([df, contract_dummies], axis=1)
df = df.drop('ContractType', axis=1)

# 특성과 타겟 분리
X = df.drop('IsChurn', axis=1)
y = df['IsChurn']

# 4. 훈련/테스트 분할
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

# 특성 정규화 (StandardScaler)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 클래스 가중치 계산
class_weight = {0: 1.0 , 1: 1.64}  # 요구사항에 따른 가중치

# 딥러닝 모델 구성
def create_mlp_model(input_dim):
    """MLP 모델 생성 함수"""
    model = keras.Sequential([
        layers.Input(shape=(input_dim,)),
        layers.Dense(512, activation='relu', name='dense_1'),
        layers.Dropout(0.5, name='dropout_1'),
        layers.Dense(64, activation='relu', name='dense_2'),
        layers.Dropout(0.7, name='dropout_2'),
        layers.Dense(31, activation='relu', name='dense_3'),
        layers.Dropout(0.3, name='dropout_3'),
        layers.Dense(1, activation='sigmoid', name='output')
    ])
    return model

# 모델 생성
model = create_mlp_model(X_train_scaled.shape[1])

# 모델 컴파일
model.compile(
    optimizer='adam',
    loss='binary_crossentropy',
    metrics=['accuracy']
)
# 조기 종료 콜백
early_stopping = keras.callbacks.EarlyStopping(
    monitor='val_loss',
    patience=10,
    restore_best_weights=True
)
# 모델 훈련
history = model.fit(
    X_train_scaled, y_train,
    epochs=100,
    batch_size=32,
    validation_split=0.2,
    class_weight=class_weight,
    callbacks=[early_stopping],
    verbose=1
)
# 모델 평가
print("\n=== 모델 평가 ===")

# 예측 수행
y_pred_proba = model.predict(X_test_scaled)
y_pred = (y_pred_proba > 0.5).astype(int).flatten()

# 평가 지표 계산
accuracy = accuracy_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)

print(f"테스트 정확도 (Accuracy): {accuracy:.4f}")
print(f"테스트 F1-Score: {f1:.4f}")

# Classification Report
print(f"\n분류 리포트:")
print(classification_report(y_test, y_pred))

# Confusion Matrix
cm = confusion_matrix(y_test, y_pred)

# 혼동 행렬 히트맵
fig, ax = plt.subplots(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax) 

ax.set_title('Confusion Matrix')
ax.set_xlabel('Predicted')
ax.set_ylabel('Actual')

plt.tight_layout()
plt.show()

# 혼동 행렬 기반 세부 지표 계산
tn, fp, fn, tp = cm.ravel()
precision = tp / (tp + fp)
recall = tp / (tp + fn)
specificity = tn / (tn + fp)

# 결과 해석
print(f"\n혼동 행렬 (Confusion Matrix):")
print(cm)
print(f"\n혼동 행렬 해석:")
print(f"   - 실제 이탈 고객 중 {recall:.1%}를 올바르게 예측")
print(f"   - 이탈 예측 중 {precision:.1%}가 실제 이탈 고객")
print(f"   - 비이탈 고객 중 {specificity:.1%}를 올바르게 예측")
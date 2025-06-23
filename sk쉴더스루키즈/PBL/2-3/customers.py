import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.model_selection import train_test_split

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 1. 데이터 불러오기
df = pd.read_csv("20250620_143916_mall_customers.csv")

# 2. 분석에 사용할 열 선택
X = df[['Annual Income (k$)', 'Spending Score (1-100)']]

# 3. 데이터 표준화 (StandardScaler 사용)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 4. 학습/테스트 데이터 분리 (8:2)
X_train, X_test = train_test_split(X_scaled, test_size=0.2, random_state=42)

# 5. 엘보우 기법으로 최적 k 찾기
inertias = []
silhouette_scores = []
K_range = range(2, 11)  # silhouette는 최소 k=2 이상이어야 하므로 1 제외

for k in K_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init='auto')
    kmeans.fit(X_train)
    labels = kmeans.labels_
    unique_labels = np.unique(labels)

    inertias.append(kmeans.inertia_)

    # 클러스터 수가 2개 이상일 때만 silhouette score 계산
    if len(unique_labels) > 1:
        try:
            score = silhouette_score(X_train, labels)
        except:
            score = -1  # silhouette_score = -1 설정한 이유, Silhouette Score는 -1 ~ 1 범위이므로, -1로 설정하면 최적 k 선택 시 절대 선택되지 않도록 유도하는 효과

    else:
        score = -1

    silhouette_scores.append(score)

# 6. 정규화 (0~1 스케일로)
inertia_scaled = MinMaxScaler().fit_transform(np.array(inertias).reshape(-1, 1)).flatten()
silhouette_scaled = MinMaxScaler().fit_transform(np.array(silhouette_scores).reshape(-1, 1)).flatten()

# 7. 혼합 점수 계산: silhouette는 클수록 좋고, inertia는 작을수록 좋음 → (1 - inertia_scaled)
combined_scores = silhouette_scaled + (1 - inertia_scaled)

# 8. 최적 k 선택
optimal_k = K_range[np.argmax(combined_scores)]
print(f"Silhouette + Inertia 혼합 기준 최적 k: {optimal_k}")

# 9. 엘보우 그래프 시각화
plt.figure(figsize=(6, 4))
plt.plot(K_range, inertias, marker='o')
plt.title('Elbow Method for Optimal k')
plt.xlabel('Number of Clusters (k)')
plt.ylabel('Inertia')
plt.grid(True)
plt.show()

# 10. 최적 k로 모델 학습
model = KMeans(n_clusters=optimal_k, random_state=42)
model.fit(X_train)

# 11. 테스트 데이터에 클러스터 할당
test_labels = model.predict(X_test)

# 12. 실루엣 점수 평가
sil_score = silhouette_score(X_test, test_labels)
print(f"Silhouette Score on Test Set: {sil_score:.4f}")

# 13. 혼합 스코어 시각화
plt.figure(figsize=(8, 5))
plt.plot(K_range, silhouette_scaled, label='Silhouette (scaled)', marker='o')
plt.plot(K_range, 1 - inertia_scaled, label='1 - Inertia (scaled)', marker='s')
plt.plot(K_range, combined_scores, label='Combined Score', marker='^', linewidth=2, color='purple')
plt.axvline(optimal_k, color='red', linestyle='--', label=f'Optimal k = {optimal_k}')
plt.title('Silhouette + Inertia 기반 k 선택')
plt.xlabel('Number of clusters (k)')
plt.ylabel('Normalized Score')
plt.legend()
plt.grid(True)
plt.show()

# 14. 학습 데이터 클러스터 시각화
train_labels = model.labels_
plt.figure(figsize=(6, 4))
plt.scatter(X_train[:, 0], X_train[:, 1], c=train_labels, cmap='viridis', s=50)
plt.scatter(model.cluster_centers_[:, 0], model.cluster_centers_[:, 1],
            s=200, c='red', marker='X', label='Centers')
plt.title('K-Means Clusters (Train Data)')
plt.xlabel('Annual Income (scaled)')
plt.ylabel('Spending Score (scaled)')
plt.legend()
plt.show()

# 15. 테스트 데이터 클러스터 시각화
plt.figure(figsize=(6, 4))
plt.scatter(X_test[:, 0], X_test[:, 1], c=test_labels, cmap='viridis', s=50)
plt.title('K-Means Clusters (Test Data)')
plt.xlabel('Annual Income (scaled)')
plt.ylabel('Spending Score (scaled)')
plt.show()

# 16. 각 클러스터 특징 분석 (원래 데이터 기반)
df_scaled = scaler.transform(X)
df_clustered = df.copy()
df_clustered['Cluster'] = KMeans(n_clusters=optimal_k, random_state=42).fit_predict(df_scaled)

# 전체 평균 계산
avg_income = df['Annual Income (k$)'].mean()
avg_score = df['Spending Score (1-100)'].mean()

print("\n[클러스터별 평균 특성 및 해석]")
centers = scaler.inverse_transform(model.cluster_centers_)

for i, center in enumerate(centers):
    income, score = center
    income_level = '고소득' if income >= avg_income else '저소득'
    score_level = '고소비' if score >= avg_score else '저소비'
    print(f"클러스터 {i}: 연소득 평균 = {income:.2f}k$, 소비점수 평균 = {score:.2f} → [{income_level}, {score_level}]")
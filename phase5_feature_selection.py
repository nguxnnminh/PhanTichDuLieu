# Phase 5: Feature Selection va Feature Importance
# Khong dung ket qua nay de tuyen bo Rolling-Origin CV tuyet doi khach quan, vi neu
# chon feature tren toan bo du lieu roi moi CV thi co nguy co leakage.

from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.inspection import permutation_importance
from sklearn.ensemble import RandomForestRegressor


print("=" * 70)
print("PHASE 5 - FEATURE SELECTION")
print("=" * 70)

RUN_ADVANCED_FEATURE_SELECTION = False

if "X_ml" not in globals() or "y_ml" not in globals():
    raise NameError("Phase 5 can X_ml va y_ml tu Phase 3 Feature Engineering.")

X_fs = X_ml.replace([np.inf, -np.inf], np.nan).copy()
X_fs = X_fs.fillna(X_fs.median(numeric_only=True))
y_fs = y_ml.copy()


corr_with_target = (
    pd.concat([X_fs, y_fs.rename("Rainfall")], axis=1)
    .corr(numeric_only=True)["Rainfall"]
    .drop("Rainfall")
    .sort_values(key=lambda s: s.abs(), ascending=False)
)

print("\n" + "=" * 60)
print("TOP 10 FEATURE THEO ABS CORRELATION VOI RAINFALL")
print("=" * 60)
print(corr_with_target.head(10).to_string(float_format=lambda x: f"{x:.3f}"))

fig, ax = plt.subplots(figsize=(10, 7), dpi=100)
top_corr = corr_with_target.head(10).sort_values()
colors = ["#2166ac" if v >= 0 else "#b2182b" for v in top_corr.values]
ax.barh(top_corr.index, top_corr.values, color=colors)
ax.axvline(0, color="black", linewidth=0.8)
ax.set_title("Top 10 Feature Correlation voi Rainfall", fontsize=13, fontweight="bold")
ax.set_xlabel("Pearson correlation")
plt.tight_layout()
plt.show()


if RUN_ADVANCED_FEATURE_SELECTION:
    top_vif_features = corr_with_target.head(25).index.tolist()
    X_vif = X_fs[top_vif_features].copy()

    vif_rows = []
    try:
        for i, col in enumerate(X_vif.columns):
            vif_rows.append({
                "Feature": col,
                "VIF": float(variance_inflation_factor(X_vif.values, i)),
            })
        vif_df = pd.DataFrame(vif_rows).sort_values("VIF", ascending=False)
    except Exception as exc:
        print(f"[VIF loi] {exc}")
        vif_df = pd.DataFrame(columns=["Feature", "VIF"])

    print("\n" + "=" * 60)
    print("VIF - TOP 25 FEATURE THEO CORRELATION")
    print("=" * 60)
    if not vif_df.empty:
        print(vif_df.to_string(index=False, float_format=lambda x: f"{x:.2f}"))
        high_vif_features = vif_df[vif_df["VIF"] > 10]["Feature"].tolist()
    else:
        high_vif_features = []
    print(f"\nFeature co VIF > 10: {high_vif_features if high_vif_features else 'Khong co hoac khong tinh duoc'}")
else:
    vif_df = pd.DataFrame(columns=["Feature", "VIF"])
    high_vif_features = []


rf_feature_selector = RandomForestRegressor(
    random_state=42,
    n_estimators=300,
    max_depth=8,
    min_samples_leaf=5,
    n_jobs=-1,
)
rf_feature_selector.fit(X_fs, y_fs)

feature_importance_df = pd.DataFrame({
    "Feature": X_fs.columns,
    "Importance": rf_feature_selector.feature_importances_,
}).sort_values("Importance", ascending=False)

print("\n" + "=" * 60)
print("TOP 10 RANDOM FOREST FEATURE IMPORTANCE")
print("=" * 60)
print(feature_importance_df.head(10).to_string(index=False, float_format=lambda x: f"{x:.4f}"))

fig, ax = plt.subplots(figsize=(10, 7), dpi=100)
top_fi = feature_importance_df.head(10).sort_values("Importance")
ax.barh(top_fi["Feature"], top_fi["Importance"], color="teal")
ax.set_title("Top 10 Random Forest Feature Importance", fontsize=13, fontweight="bold")
ax.set_xlabel("Importance")
plt.tight_layout()
plt.show()


if RUN_ADVANCED_FEATURE_SELECTION:
    perm = permutation_importance(
        rf_feature_selector,
        X_fs,
        y_fs,
        n_repeats=10,
        random_state=42,
        scoring="neg_root_mean_squared_error",
    )

    perm_importance_df = pd.DataFrame({
        "Feature": X_fs.columns,
        "PermutationImportance": perm.importances_mean,
    }).sort_values("PermutationImportance", ascending=False)

    print("\n" + "=" * 60)
    print("TOP 20 PERMUTATION IMPORTANCE")
    print("=" * 60)
    print(perm_importance_df.head(20).to_string(index=False, float_format=lambda x: f"{x:.4f}"))

    fig, ax = plt.subplots(figsize=(10, 7), dpi=100)
    top_perm = perm_importance_df.head(20).sort_values("PermutationImportance")
    ax.barh(top_perm["Feature"], top_perm["PermutationImportance"], color="royalblue")
    ax.set_title("Top 20 Permutation Importance", fontsize=13, fontweight="bold")
    ax.set_xlabel("Increase in RMSE importance proxy")
    plt.tight_layout()
    plt.show()
else:
    perm_importance_df = pd.DataFrame(columns=["Feature", "PermutationImportance"])


selected_features = sorted(set(
    corr_with_target.head(10).index.tolist()
    + feature_importance_df.head(10)["Feature"].tolist()
    + perm_importance_df.head(10)["Feature"].tolist()
))

selected_features = [f for f in selected_features if f not in high_vif_features]

print("\n" + "=" * 60)
print("SELECTED FEATURES - PHUC VU GIAI THICH/BAO CAO")
print("=" * 60)
selected_features = selected_features[:10]
print(f"So selected features cho slide: {len(selected_features)}")
for feature in selected_features:
    print(f"  - {feature}")

print("\nGhi chu hoc thuat:")
print("- Correlation va importance giup giai thich feature nao lien quan manh den Rainfall.")
if RUN_ADVANCED_FEATURE_SELECTION:
    print("- VIF va permutation importance duoc dung nhu phan phan tich nang cao.")
print("- Ket qua feature selection nay phuc vu bao cao, khong dung de lam ro ri du lieu trong CV.")

print("=" * 70)
print("✅ Phase 5 hoan tat - Feature selection da san sang cho bao cao.")
print("=" * 70)

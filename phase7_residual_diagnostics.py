# Phase 7: Residual Diagnostics

from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.stats.diagnostic import acorr_ljungbox


print("=" * 70)
print("PHASE 7 - RESIDUAL DIAGNOSTICS")
print("=" * 70)

if "forecast_model_name" not in globals() or "forecast_forecast" not in globals():
    raise NameError("Phase 7 can forecast_model_name va forecast_forecast tu Phase 6.")

residuals = (test - forecast_forecast).dropna()

print(f"Model kiem tra residual: {forecast_model_name}")
print(f"So residual quan sat   : {len(residuals)}")
print(f"Residual mean          : {residuals.mean():.3f}")
print(f"Residual std           : {residuals.std():.3f}")

fig, axes = plt.subplots(1, 3, figsize=(16, 4), dpi=100)

axes[0].plot(residuals.index, residuals, color="firebrick", linewidth=1.4)
axes[0].axhline(0, color="black", linestyle="--", linewidth=0.9)
axes[0].set_title("Residuals Theo Thoi Gian", fontsize=12, fontweight="bold")
axes[0].set_xlabel("Thoi gian")
axes[0].set_ylabel("Residual")
axes[0].grid(True, alpha=0.3)

axes[1].hist(residuals, bins=12, edgecolor="black", color="steelblue", alpha=0.85)
axes[1].axvline(0, color="black", linestyle="--", linewidth=0.9)
axes[1].set_title("Residual Histogram", fontsize=12, fontweight="bold")
axes[1].set_xlabel("Residual")
axes[1].set_ylabel("Tan suat")

acf_lags = max(1, min(23, len(residuals) - 1))
plot_acf(residuals, lags=acf_lags, ax=axes[2])
axes[2].set_title("Residual ACF", fontsize=12, fontweight="bold")

plt.tight_layout()
plt.show()

ljung_lags = [lag for lag in [6, 12, 24] if lag < len(residuals)]
if ljung_lags:
    ljung_box_df = acorr_ljungbox(residuals, lags=ljung_lags, return_df=True)
    print("\n" + "=" * 60)
    print("LJUNG-BOX TEST")
    print("=" * 60)
    print(ljung_box_df.to_string(float_format=lambda x: f"{x:.4f}"))

    min_pvalue = float(ljung_box_df["lb_pvalue"].min())
    if min_pvalue > 0.05:
        residual_diagnostic_conclusion = (
            "Residual khong con autocorrelation dang ke theo Ljung-Box (p-value > 0.05)."
        )
    else:
        residual_diagnostic_conclusion = (
            "Residual van co dau hieu autocorrelation; model co the con bo sot cau truc thoi gian."
        )
else:
    ljung_box_df = pd.DataFrame()
    residual_diagnostic_conclusion = "Khong du do dai residual de chay Ljung-Box."

print("\nKet luan residual diagnostics:")
print(residual_diagnostic_conclusion)

print("=" * 70)
print("✅ Phase 7 hoan tat - Residual diagnostics da san sang.")
print("=" * 70)

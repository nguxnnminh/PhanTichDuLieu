# Phase 7: Residual Diagnostics — tất cả 4 mô hình

from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.stats.diagnostic import acorr_ljungbox

print("=" * 70)
print("PHASE 7 — RESIDUAL DIAGNOSTICS")
print("=" * 70)

if "forecasts" not in globals():
    raise NameError("Phase 7 cần forecasts dict từ Phase 6.")

residual_conclusions = {}

for model_name, fc in forecasts.items():
    residuals = (test - fc).dropna()
    if len(residuals) < 4:
        print(f"\n[{model_name}] Không đủ residual để phân tích.")
        continue

    print(f"\n{'─' * 60}")
    print(f"RESIDUAL — {model_name}")
    print(f"{'─' * 60}")
    print(f"Số residual  : {len(residuals)}")
    print(f"Mean         : {residuals.mean():.3f}")
    print(f"Std          : {residuals.std():.3f}")

    # Ljung-Box test
    ljung_lags = [lag for lag in [6, 12] if lag < len(residuals)]
    if ljung_lags:
        ljung_box_df = acorr_ljungbox(residuals, lags=ljung_lags, return_df=True)
        min_pvalue = float(ljung_box_df["lb_pvalue"].min())
        if min_pvalue > 0.05:
            conclusion = "Residual không còn autocorrelation đáng kể (p > 0.05)."
        else:
            conclusion = "Residual vẫn có autocorrelation; mô hình có thể còn bỏ sót cấu trúc."
        print(f"Ljung-Box    : {conclusion}")
        print(ljung_box_df.to_string(float_format=lambda x: f"{x:.4f}"))
    else:
        conclusion = "Không đủ dữ liệu cho Ljung-Box."

    residual_conclusions[model_name] = conclusion


# ── Plot residuals for best model ──────────────────────────────
best_model = globals().get("forecast_model_name", list(forecasts.keys())[0])
best_residuals = (test - forecasts[best_model]).dropna()

fig, axes = plt.subplots(1, 3, figsize=(16, 4), dpi=100)

axes[0].plot(best_residuals.index, best_residuals, color="firebrick", linewidth=1.4)
axes[0].axhline(0, color="black", linestyle="--", linewidth=0.9)
axes[0].set_title(f"Residuals — {best_model}", fontsize=12, fontweight="bold")
axes[0].set_xlabel("Thời gian")
axes[0].set_ylabel("Residual")
axes[0].grid(True, alpha=0.3)

axes[1].hist(best_residuals, bins=12, edgecolor="black", color="steelblue", alpha=0.85)
axes[1].axvline(0, color="black", linestyle="--", linewidth=0.9)
axes[1].set_title("Residual Histogram", fontsize=12, fontweight="bold")
axes[1].set_xlabel("Residual")
axes[1].set_ylabel("Tần suất")

acf_lags = max(1, min(23, len(best_residuals) - 1))
plot_acf(best_residuals, lags=acf_lags, ax=axes[2])
axes[2].set_title("Residual ACF", fontsize=12, fontweight="bold")

plt.tight_layout()
plt.show()

print("\n" + "=" * 60)
print("TÓM TẮT RESIDUAL DIAGNOSTICS")
print("=" * 60)
for model_name, conclusion in residual_conclusions.items():
    print(f"  {model_name:<20}: {conclusion}")
print("=" * 60)

# Keep for Phase 8
residual_diagnostic_conclusion = residual_conclusions.get(best_model, "N/A")

print("\n✅ Phase 7 hoàn tất — Residual diagnostics đã xong.")

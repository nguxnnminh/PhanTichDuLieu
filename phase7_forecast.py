from prophet import Prophet
from xgboost import XGBRegressor

FORECAST_STEPS = 12

target_label = globals().get("TARGET_LABEL", "Lượng mưa trung bình tháng")
target_unit = globals().get("TARGET_UNIT", "mm/tháng")
target_axis_label = f"{target_label} ({target_unit})"

if "forecast_model_name" not in globals():
    raise NameError("Phase 7 cần chạy sau Phase 5 để có forecast_model_name.")

full_series = df_monthly["Rainfall"].asfreq("MS")
future_index = pd.date_range(
    start=full_series.index[-1] + pd.DateOffset(months=1),
    periods=FORECAST_STEPS,
    freq="MS",
)

MODEL_COLORS = {
    "Seasonal Naive": "dimgray",
    "SARIMAX": "royalblue",
    "Prophet": "seagreen",
    "XGBoost": "firebrick",
}


def _residual_interval(forecast, fitted, actual):
    common = actual.loc[fitted.index].dropna()
    fitted_common = fitted.loc[common.index].dropna()
    if len(fitted_common) < 2:
        resid_std = float(actual.std())
    else:
        resid_std = float((common - fitted_common).std())
    lower = forecast - 1.96 * resid_std
    upper = forecast + 1.96 * resid_std
    lower.name = "Giới hạn dưới"
    upper.name = "Giới hạn trên"
    return lower, upper


print("=" * 60)
print(f"DỰ BÁO 12 THÁNG TƯƠNG LAI — TẤT CẢ 4 MÔ HÌNH")
print("=" * 60)

future_forecasts = {}
future_intervals = {}


print("\n[Seasonal Naive] Refit...")
sn_fc = pd.Series(
    [full_series[full_series.index.month == d.month].iloc[-1] for d in future_index],
    index=future_index,
    name="Seasonal Naive",
)
sn_fitted = pd.Series(
    [full_series[full_series.index.month == m].mean() for m in full_series.index.month],
    index=full_series.index,
)
sn_lower, sn_upper = _residual_interval(sn_fc, sn_fitted, full_series)
future_forecasts["Seasonal Naive"] = sn_fc
future_intervals["Seasonal Naive"] = (sn_lower, sn_upper)
print(f"  → OK")

print("\n[SARIMAX] Refit trên toàn bộ dữ liệu...")
try:
    _order = globals().get("sarimax_order", (1, 0, 1))
    _seasonal = globals().get("sarimax_seasonal_order", (1, 0, 1, 12))

    exog_full = df_meteo_monthly_context.reindex(full_series.index)[SARIMAX_EXOG_COLS]
    exog_full = exog_full.shift(1).interpolate(method="time").ffill().bfill()

    # Exog tương lai dùng climatology proxy.
    exog_future_rows = []
    for fd in future_index:
        proxy = {}
        for col in SARIMAX_EXOG_COLS:
            same_month = exog_full.loc[exog_full.index.month == fd.month, col].dropna()
            proxy[col] = float(same_month.mean()) if len(same_month) > 0 else float(exog_full[col].mean())
        exog_future_rows.append(proxy)
    exog_future = pd.DataFrame(exog_future_rows, index=future_index)

    sarimax_full = SARIMAX(
        full_series,
        exog=exog_full,
        order=_order,
        seasonal_order=_seasonal,
        enforce_stationarity=False,
        enforce_invertibility=False,
    ).fit(disp=False, maxiter=200)

    raw_fc = sarimax_full.forecast(steps=FORECAST_STEPS, exog=exog_future)
    sarimax_fc = pd.Series(np.clip(raw_fc.values, 0, None), index=future_index, name="SARIMAX")
    sarimax_fitted = pd.Series(sarimax_full.fittedvalues.values, index=full_series.index)
    sarimax_lower, sarimax_upper = _residual_interval(sarimax_fc, sarimax_fitted, full_series)

    future_forecasts["SARIMAX"] = sarimax_fc
    future_intervals["SARIMAX"] = (sarimax_lower, sarimax_upper)
    print(f"  → SARIMAX{_order}x{_seasonal} OK")
except Exception as exc:
    print(f"  → [Bỏ qua] {exc}")

print("\n[Prophet] Refit trên toàn bộ dữ liệu...")
try:
    prophet_train_full = pd.DataFrame({
        "ds": full_series.index,
        "y": full_series.values,
    })
    prophet_full = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        seasonality_mode="additive",
        changepoint_prior_scale=0.05,
    )
    prophet_full.fit(prophet_train_full)

    future_df = prophet_full.make_future_dataframe(periods=FORECAST_STEPS, freq="MS")
    prophet_pred = prophet_full.predict(future_df)

    prophet_future = prophet_pred.iloc[-FORECAST_STEPS:]
    prophet_fc = pd.Series(
        np.clip(prophet_future["yhat"].values, 0, None),
        index=future_index,
        name="Prophet",
    )
    prophet_lower = pd.Series(prophet_future["yhat_lower"].values, index=future_index)
    prophet_upper = pd.Series(prophet_future["yhat_upper"].values, index=future_index)

    future_forecasts["Prophet"] = prophet_fc
    future_intervals["Prophet"] = (prophet_lower, prophet_upper)
    print(f"  → OK")
except Exception as exc:
    print(f"  → [Bỏ qua] {exc}")

print("\n[XGBoost] Refit trên toàn bộ dữ liệu...")
try:
    meteo_context_full = df_meteo_monthly_context.reindex(full_series.index)[WEATHER_FEATURE_COLS]

    rows_full, targets_full = [], []
    for i in range(24, len(full_series)):
        rows_full.append(
            make_xgb_feature_row(full_series.iloc[:i], full_series.index[i], meteo_context_full.iloc[:i])
        )
        targets_full.append(full_series.iloc[i])

    X_full = pd.DataFrame(rows_full)
    feature_means_full = X_full.mean()
    feature_columns_full = X_full.columns.tolist()
    X_full = X_full.fillna(feature_means_full)

    xgb_full = XGBRegressor(
        n_estimators=200, max_depth=4, learning_rate=0.05,
        min_child_weight=5, subsample=0.8, colsample_bytree=0.8,
        random_state=42, verbosity=0,
    )
    xgb_full.fit(X_full, np.array(targets_full))

    rain_hist = full_series.copy()
    meteo_hist = meteo_context_full.copy()
    xgb_preds = []

    for fd in future_index:
        x_next = pd.DataFrame([make_xgb_feature_row(rain_hist, fd, meteo_hist)])
        x_next = x_next.reindex(columns=feature_columns_full).fillna(feature_means_full)
        pred = max(0.0, float(xgb_full.predict(x_next)[0]))
        xgb_preds.append(pred)
        rain_hist = pd.concat([rain_hist, pd.Series([pred], index=[fd])])
        meteo_hist = pd.concat([
            meteo_hist,
            pd.DataFrame([make_meteo_proxy_row(meteo_hist, fd)], index=[fd]),
        ])

    xgb_fc = pd.Series(xgb_preds, index=future_index, name="XGBoost")
    xgb_fitted = pd.Series(xgb_full.predict(X_full), index=full_series.index[24:])
    xgb_lower, xgb_upper = _residual_interval(xgb_fc, xgb_fitted, full_series)

    future_forecasts["XGBoost"] = xgb_fc
    future_intervals["XGBoost"] = (xgb_lower, xgb_upper)
    print(f"  → OK, {len(feature_columns_full)} features")
except Exception as exc:
    print(f"  → [Bỏ qua] {exc}")

THANG_VI = {
    1: "Tháng 1", 2: "Tháng 2", 3: "Tháng 3", 4: "Tháng 4",
    5: "Tháng 5", 6: "Tháng 6", 7: "Tháng 7", 8: "Tháng 8",
    9: "Tháng 9", 10: "Tháng 10", 11: "Tháng 11", 12: "Tháng 12",
}

future_forecast = future_forecasts[forecast_model_name]
future_lower, future_upper = future_intervals[forecast_model_name]
future_lower_display = future_lower.clip(lower=0)

print("\n" + "=" * 68)
print(f"DỰ BÁO 12 THÁNG — {city_name} ({forecast_model_name})")
print("=" * 68)
print(f"{'Tháng':<16}{'Dự báo':>14}{'Cận dưới':>14}{'Cận trên':>14}")
print("-" * 68)
for dt, fc_val, lo, hi in zip(
    future_index,
    future_forecast.values,
    future_lower_display.values,
    future_upper.values,
):
    print(f"{THANG_VI[dt.month] + '/' + str(dt.year):<16}{fc_val:>14.2f}{lo:>14.2f}{hi:>14.2f}")
print("-" * 68)

forecast_period_sum = float(future_forecast.sum())
forecast_period_mean = float(future_forecast.mean())
print(f"Tổng mưa dự báo 12 tháng: {forecast_period_sum:.1f} mm")

thang_mua = future_forecast.idxmax()
thang_kho = future_forecast.idxmin()
print(
    f"Tháng mưa nhiều nhất: {THANG_VI[thang_mua.month]}/{thang_mua.year} "
    f"({future_forecast[thang_mua]:.2f} {target_unit})"
)
print(
    f"Tháng mưa ít nhất  : {THANG_VI[thang_kho.month]}/{thang_kho.year} "
    f"({future_forecast[thang_kho]:.2f} {target_unit})"
)

print("\n" + "=" * 80)
print("SO SÁNH DỰ BÁO TẤT CẢ MÔ HÌNH")
print("=" * 80)
comparison_data = {}
for name, fc in future_forecasts.items():
    comparison_data[name] = fc.values
comparison_df = pd.DataFrame(
    comparison_data,
    index=[f"{THANG_VI[d.month]}/{d.year}" for d in future_index],
)
print(comparison_df.to_string(float_format=lambda x: f"{x:.1f}"))

best_color = MODEL_COLORS.get(forecast_model_name, "steelblue")

fig, ax = plt.subplots(figsize=(16, 6), dpi=100)
ax.plot(full_series.index, full_series, color="steelblue", linewidth=1.3, label="Dữ liệu lịch sử")
ax.plot(
    future_forecast.index, future_forecast,
    color=best_color, linewidth=2.4, marker="o",
    label=f"Dự báo {forecast_model_name}",
)
ax.fill_between(
    future_index, future_lower_display, future_upper,
    color=best_color, alpha=0.18, label="Khoảng tin cậy 95%",
)
ax.axvline(future_index[0], color="black", linestyle="--", linewidth=1.2)
ax.set_title(f"Dự báo {target_label} 12 tháng — {city_name}", fontsize=14, fontweight="bold")
ax.set_xlabel("Thời gian")
ax.set_ylabel(target_axis_label)
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

zoom_history = full_series.iloc[-24:]
fig, ax = plt.subplots(figsize=(14, 5), dpi=100)
ax.plot(
    zoom_history.index, zoom_history,
    color="steelblue", linewidth=1.8, marker="o", label="Lịch sử 24 tháng cuối",
)

for name, fc in future_forecasts.items():
    color = MODEL_COLORS.get(name, "gray")
    ax.plot(fc.index, fc, linewidth=1.7, linestyle="--", color=color, label=name)

ax.axvline(future_index[0], color="black", linestyle="--", linewidth=1.2)
all_ticks = zoom_history.index.tolist() + future_index.tolist()
ax.set_xticks(all_ticks)
ax.set_xticklabels(
    [f"T{d.month}/{str(d.year)[2:]}" for d in all_ticks],
    rotation=45, ha="right", fontsize=8,
)
ax.set_title("Phóng to: 24 tháng cuối + 12 tháng dự báo", fontsize=13, fontweight="bold")
ax.set_xlabel("Tháng")
ax.set_ylabel(target_axis_label)
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

test_rmse = metrics_df.loc[forecast_model_name, "RMSE"]
test_wape = metrics_df.loc[forecast_model_name, "WAPE (%)"]
cv_rmse = globals().get("_cv_mean", {}).get(forecast_model_name, float("nan"))

print("\n" + "=" * 70)
print("TÓM TẮT TOÀN BỘ DỰ ÁN")
print("=" * 70)
print(f"Thành phố             : {city_name}")
print(f"Phạm vi dữ liệu      : {df_monthly.index.min():%m/%Y} → {df_monthly.index.max():%m/%Y}")
print(f"Số tháng dữ liệu     : {len(df_monthly)}")
print(f"Mô hình forecast      : {forecast_model_name}")
if not np.isnan(cv_rmse):
    print(f"RMSE CV nhiều cửa sổ  : {cv_rmse:.2f} {target_unit}")
print(f"RMSE hold-out         : {test_rmse:.2f} {target_unit}")
print(f"WAPE hold-out         : {test_wape:.2f}%")
print(f"Giai đoạn dự báo      : {future_index[0]:%m/%Y} → {future_index[-1]:%m/%Y}")
print(f"Tổng mưa dự báo       : {forecast_period_sum:.1f} mm")
print("=" * 70)

print("\n✅ Phase 7 hoàn tất — forecast đã sẵn sàng.")

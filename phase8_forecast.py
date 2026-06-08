# Phase 8: Forecast 12 thang tuong lai
# Refit mo hinh da duoc Phase 4 chon tren toan bo du lieu lich su,

from pmdarima.arima import ARIMA as PmARIMA

FORECAST_STEPS = 12

target_label = globals().get("TARGET_LABEL", "Luong mua trung binh thang")
target_unit = globals().get("TARGET_UNIT", "mm/thang")
target_axis_label = f"{target_label} ({target_unit})"
target_agg = globals().get("TARGET_AGG", "monthly_total")

if "forecast_model_name" not in globals():
    raise NameError("Phase 8 can chay sau Phase 6 de co forecast_model_name.")

full_series = df_monthly["Rainfall"].asfreq("MS")
future_index = pd.date_range(
    start=full_series.index[-1] + pd.DateOffset(months=1),
    periods=FORECAST_STEPS,
    freq="MS",
)

print("=" * 60)
print(f"HUAN LUYEN LAI {forecast_model_name} TREN TOAN BO DU LIEU")
print("=" * 60)

SHOW_MODEL_SUMMARY = globals().get("SHOW_MODEL_SUMMARY", False)


def _residual_interval(forecast: pd.Series, fitted: pd.Series, actual: pd.Series):
    resid_std = float((actual.loc[fitted.index] - fitted).std())
    lower = forecast - 1.96 * resid_std
    upper = forecast + 1.96 * resid_std
    lower.name = "Gioi han duoi"
    upper.name = "Gioi han tren"
    return lower, upper


if forecast_model_name == "SARIMA":
    sarima_full = PmARIMA(
        order=sarima_auto.order,
        seasonal_order=sarima_auto.seasonal_order,
        with_intercept=getattr(sarima_auto, "with_intercept", True),
        suppress_warnings=True,
    )
    sarima_full.fit(full_series)
    if SHOW_MODEL_SUMMARY:
        print(sarima_full.summary())

    fc_arr, ci_arr = sarima_full.predict(
        n_periods=FORECAST_STEPS,
        return_conf_int=True,
        alpha=0.05,
    )
    future_forecast = pd.Series(np.clip(fc_arr, 0, None), index=future_index, name="Du bao")
    future_lower = pd.Series(ci_arr[:, 0], index=future_index, name="Gioi han duoi")
    future_upper = pd.Series(ci_arr[:, 1], index=future_index, name="Gioi han tren")

elif forecast_model_name == "ARIMA":
    arima_full = ARIMA(full_series, order=(1, 0, 1)).fit()
    if SHOW_MODEL_SUMMARY:
        print(arima_full.summary())

    fc_arr = arima_full.forecast(steps=FORECAST_STEPS).values
    future_forecast = pd.Series(np.clip(fc_arr, 0, None), index=future_index, name="Du bao")
    fitted = pd.Series(arima_full.fittedvalues.values, index=full_series.index, name="Fitted")
    future_lower, future_upper = _residual_interval(future_forecast, fitted, full_series)

elif forecast_model_name == "SARIMAX Weather":
    if not globals().get("SARIMAX_WEATHER_COLS"):
        raise RuntimeError("Khong co bien khi tuong de refit SARIMAX Weather.")

    exog_full_raw = (
        df_meteo_monthly_context
        .reindex(full_series.index)[SARIMAX_WEATHER_COLS]
        .interpolate(method="time")
        .ffill()
        .bfill()
    )
    exog_future_raw = make_sarimax_weather_exog(exog_full_raw, future_index)
    exog_full, exog_future, _, _ = scale_exog(exog_full_raw, exog_future_raw)

    sarimax_full = SARIMAX(
        full_series,
        exog=exog_full,
        order=sarima_auto.order,
        seasonal_order=sarima_auto.seasonal_order,
        enforce_stationarity=False,
        enforce_invertibility=False,
    ).fit(disp=False)
    if SHOW_MODEL_SUMMARY:
        print(sarimax_full.summary())

    forecast_result = sarimax_full.get_forecast(steps=FORECAST_STEPS, exog=exog_future)
    fc_arr = forecast_result.predicted_mean.values
    ci_df = forecast_result.conf_int(alpha=0.05)

    future_forecast = pd.Series(np.clip(fc_arr, 0, None), index=future_index, name="Du bao")
    future_lower = pd.Series(ci_df.iloc[:, 0].values, index=future_index, name="Gioi han duoi")
    future_upper = pd.Series(ci_df.iloc[:, 1].values, index=future_index, name="Gioi han tren")

elif forecast_model_name == "Holt-Winters":
    hw_full_model = ExponentialSmoothing(
        full_series,
        trend="add",
        seasonal="add",
        seasonal_periods=12,
        initialization_method="estimated",
    )
    hw_full_fit = hw_full_model.fit(optimized=True)
    if SHOW_MODEL_SUMMARY:
        print(hw_full_fit.summary())

    raw_fc = hw_full_fit.forecast(steps=FORECAST_STEPS)
    future_forecast = pd.Series(np.clip(raw_fc.values, 0, None), index=future_index, name="Du bao")
    fitted = pd.Series(hw_full_fit.fittedvalues.values, index=full_series.index, name="Fitted")
    future_lower, future_upper = _residual_interval(future_forecast, fitted, full_series)

elif forecast_model_name == "Gradient Boosting Lag":
    rows, targets = [], []
    for i in range(24, len(full_series)):
        rows.append(make_lag_feature_row(full_series.iloc[:i], full_series.index[i]))
        targets.append(full_series.iloc[i])

    X_full = pd.DataFrame(rows)
    feature_means = X_full.mean()
    feature_columns = X_full.columns.tolist()
    X_full = X_full.fillna(feature_means)

    gbr_full = GradientBoostingRegressor(
        random_state=42,
        max_depth=2,
        n_estimators=80,
        learning_rate=0.05,
    )
    gbr_full.fit(X_full, np.array(targets))

    hist = full_series.copy()
    preds = []
    for fd in future_index:
        x_next = pd.DataFrame([make_lag_feature_row(hist, fd)])
        x_next = x_next.reindex(columns=feature_columns).fillna(feature_means)
        pred = max(0.0, float(gbr_full.predict(x_next)[0]))
        preds.append(pred)
        hist = pd.concat([hist, pd.Series([pred], index=[fd])])

    future_forecast = pd.Series(preds, index=future_index, name="Du bao")
    fitted = pd.Series(gbr_full.predict(X_full), index=full_series.index[24:], name="Fitted")
    future_lower, future_upper = _residual_interval(future_forecast, fitted, full_series)

elif forecast_model_name == "Gradient Boosting Weather":
    if not globals().get("WEATHER_FEATURE_COLS"):
        raise RuntimeError("Khong co bien khi tuong de refit Gradient Boosting Weather.")

    meteo_context_full = df_meteo_monthly_context.reindex(full_series.index)[WEATHER_FEATURE_COLS]
    rows, targets = [], []
    for i in range(24, len(full_series)):
        rows.append(
            make_weather_feature_row(full_series.iloc[:i], full_series.index[i], meteo_context_full.iloc[:i])
        )
        targets.append(full_series.iloc[i])

    X_full = pd.DataFrame(rows)
    feature_means = X_full.mean()
    feature_columns = X_full.columns.tolist()
    X_full = X_full.fillna(feature_means)

    gbr_weather_full = GradientBoostingRegressor(
        random_state=42,
        max_depth=2,
        n_estimators=100,
        learning_rate=0.04,
    )
    gbr_weather_full.fit(X_full, np.array(targets))

    rain_hist = full_series.copy()
    meteo_hist = meteo_context_full.copy()
    preds = []
    for fd in future_index:
        x_next = pd.DataFrame([make_weather_feature_row(rain_hist, fd, meteo_hist)])
        x_next = x_next.reindex(columns=feature_columns).fillna(feature_means)
        pred = max(0.0, float(gbr_weather_full.predict(x_next)[0]))
        preds.append(pred)
        rain_hist = pd.concat([rain_hist, pd.Series([pred], index=[fd])])
        meteo_hist = pd.concat([
            meteo_hist,
            pd.DataFrame([make_meteo_proxy_row(meteo_hist, fd)], index=[fd]),
        ])

    future_forecast = pd.Series(preds, index=future_index, name="Du bao")
    fitted = pd.Series(gbr_weather_full.predict(X_full), index=full_series.index[24:], name="Fitted")
    future_lower, future_upper = _residual_interval(future_forecast, fitted, full_series)

elif forecast_model_name == "Random Forest Weather":
    if not globals().get("WEATHER_FEATURE_COLS"):
        raise RuntimeError("Khong co bien khi tuong de refit Random Forest Weather.")

    meteo_context_full = df_meteo_monthly_context.reindex(full_series.index)[WEATHER_FEATURE_COLS]
    rows, targets = [], []
    for i in range(24, len(full_series)):
        rows.append(
            make_weather_feature_row(full_series.iloc[:i], full_series.index[i], meteo_context_full.iloc[:i])
        )
        targets.append(full_series.iloc[i])

    X_full = pd.DataFrame(rows)
    feature_means = X_full.mean()
    feature_columns = X_full.columns.tolist()
    X_full = X_full.fillna(feature_means)

    rf_weather_full = RandomForestRegressor(
        n_estimators=300,
        max_depth=8,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1,
    )
    rf_weather_full.fit(X_full, np.array(targets))

    rain_hist = full_series.copy()
    meteo_hist = meteo_context_full.copy()
    preds = []
    for fd in future_index:
        x_next = pd.DataFrame([make_weather_feature_row(rain_hist, fd, meteo_hist)])
        x_next = x_next.reindex(columns=feature_columns).fillna(feature_means)
        pred = max(0.0, float(rf_weather_full.predict(x_next)[0]))
        preds.append(pred)
        rain_hist = pd.concat([rain_hist, pd.Series([pred], index=[fd])])
        meteo_hist = pd.concat([
            meteo_hist,
            pd.DataFrame([make_meteo_proxy_row(meteo_hist, fd)], index=[fd]),
        ])

    future_forecast = pd.Series(preds, index=future_index, name="Du bao")
    fitted = pd.Series(rf_weather_full.predict(X_full), index=full_series.index[24:], name="Fitted")
    future_lower, future_upper = _residual_interval(future_forecast, fitted, full_series)

elif forecast_model_name in ("Weighted Seasonal Mean", "Seasonal Mean", "Damped Seasonal Mean"):
    if forecast_model_name == "Weighted Seasonal Mean":
        age = np.array(
            [(full_series.index[-1].year - d.year) * 12 + (full_series.index[-1].month - d.month)
             for d in full_series.index],
            dtype=float,
        )
        weights = 0.5 ** (age / WEIGHTED_CLIM_HALFLIFE)
        wdf = pd.DataFrame({"Rainfall": full_series.values, "Month": full_series.index.month, "Weight": weights})
        clim = wdf.groupby("Month").apply(lambda g: np.average(g["Rainfall"], weights=g["Weight"]))
    else:
        clim = full_series.groupby(full_series.index.month).mean()

    seasonal_fc = pd.Series([clim[d.month] for d in future_index], index=future_index, name="Du bao")
    if forecast_model_name == "Damped Seasonal Mean":
        global_mean = float(full_series.mean())
        alpha = globals().get("seasonal_damping_alpha", 0.20)
        future_forecast = pd.Series(
            global_mean + alpha * (seasonal_fc.values - global_mean),
            index=future_index,
            name="Du bao",
        )
    else:
        future_forecast = seasonal_fc

    fitted = pd.Series([clim[m] for m in full_series.index.month], index=full_series.index, name="Fitted")
    future_lower, future_upper = _residual_interval(future_forecast, fitted, full_series)

else:
    raise ValueError(f"Mo hinh khong duoc ho tro trong Phase 8: {forecast_model_name}")

future_lower_display = future_lower.clip(lower=0)
best_color = MODEL_COLORS.get(forecast_model_name, "steelblue")

print(f"\n[OK] Da refit {forecast_model_name} tren {len(full_series)} thang du lieu.")
if (future_lower < 0).any():
    print("[Luu y] Mot so can duoi CI < 0; khi hien thi da chan ve 0 vi luong mua khong the am.")


THANG_VI = {
    1: "Thang 1", 2: "Thang 2", 3: "Thang 3", 4: "Thang 4",
    5: "Thang 5", 6: "Thang 6", 7: "Thang 7", 8: "Thang 8",
    9: "Thang 9", 10: "Thang 10", 11: "Thang 11", 12: "Thang 12",
}

print("\n" + "=" * 68)
print(f"DU BAO 12 THANG TUONG LAI - {city_name} ({forecast_model_name})")
print("=" * 68)
print(f"Forecast bat dau tu {future_index[0]:%m/%Y}")
print(f"{'Thang':<16}{'Du bao':>14}{'Can duoi':>14}{'Can tren':>14}")
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
if target_agg == "monthly_total":
    print(f"Tong luong mua du bao 12 thang tiep theo: {forecast_period_sum:.1f} mm")
else:
    print(f"Trung binh du bao 12 thang tiep theo: {forecast_period_mean:.2f} {target_unit}")

thang_mua = future_forecast.idxmax()
thang_kho = future_forecast.idxmin()
print(f"Thang du bao mua nhieu nhat: {THANG_VI[thang_mua.month]}/{thang_mua.year} "
      f"({future_forecast[thang_mua]:.2f} {target_unit})")
print(f"Thang du bao mua it nhat   : {THANG_VI[thang_kho.month]}/{thang_kho.year} "
      f"({future_forecast[thang_kho]:.2f} {target_unit})")


forecast_start = future_index[0]

fig, ax = plt.subplots(figsize=(16, 6), dpi=100)
ax.plot(full_series.index, full_series, color="steelblue", linewidth=1.3, label="Du lieu lich su")
ax.plot(future_forecast.index, future_forecast, color=best_color, linewidth=2.4,
        marker="o", label=f"Du bao {forecast_model_name}")
ax.fill_between(future_index, future_lower_display, future_upper, color=best_color,
                alpha=0.18, label="Khoang tin cay 95%")
ax.axvline(forecast_start, color="black", linestyle="--", linewidth=1.2)
ax.set_title(f"Du bao {target_label} 12 thang - {city_name}", fontsize=14, fontweight="bold")
ax.set_xlabel("Thoi gian")
ax.set_ylabel(target_axis_label)
ax.tick_params(axis="x", rotation=45)
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

zoom_history = full_series.iloc[-24:]
fig, ax = plt.subplots(figsize=(14, 5), dpi=100)
ax.plot(zoom_history.index, zoom_history, color="steelblue", linewidth=1.8,
        marker="o", label="Lich su 24 thang cuoi")
ax.plot(future_forecast.index, future_forecast, color=best_color, linewidth=2.2,
        marker="s", label=f"Du bao {forecast_model_name}")
ax.fill_between(future_index, future_lower_display, future_upper, color=best_color, alpha=0.18)
ax.axvline(forecast_start, color="black", linestyle="--", linewidth=1.2)
all_ticks = zoom_history.index.tolist() + future_index.tolist()
ax.set_xticks(all_ticks)
ax.set_xticklabels([f"T{d.month}/{str(d.year)[2:]}" for d in all_ticks],
                   rotation=45, ha="right", fontsize=8)
ax.set_title("Phong to: 24 thang cuoi + 12 thang du bao", fontsize=13, fontweight="bold")
ax.set_xlabel("Thang")
ax.set_ylabel(target_axis_label)
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()


test_rmse = metrics_df.loc[forecast_model_name, "RMSE"]
test_wape = metrics_df.loc[forecast_model_name, "WAPE (%)"]
cv_rmse = globals().get("_cv_mean", {}).get(forecast_model_name, float("nan"))

print("\n" + "=" * 70)
print("TOM TAT TOAN BO DU AN")
print("=" * 70)
print(f"Thanh pho             : {city_name}")
print(f"Pham vi du lieu       : {df_monthly.index.min():%m/%Y} -> {df_monthly.index.max():%m/%Y}")
print(f"So thang du lieu      : {len(df_monthly)}")
print(f"Mo hinh forecast      : {forecast_model_name}")
if not np.isnan(cv_rmse):
    print(f"RMSE CV nhieu cua so  : {cv_rmse:.2f} {target_unit}  (chi so dang tin nhat)")
print(f"RMSE hold-out         : {test_rmse:.2f} {target_unit}  (tham khao)")
print(f"WAPE hold-out         : {test_wape:.2f}%")
print(f"Giai doan du bao      : {future_index[0]:%m/%Y} -> {future_index[-1]:%m/%Y}")
if target_agg == "monthly_total":
    print(f"Tong mua du bao       : {forecast_period_sum:.1f} mm")
else:
    print(f"TB du bao             : {forecast_period_mean:.2f} {target_unit}")
print("=" * 70)

print("\nKET LUAN")
print("-" * 70)
print(
    f"Bai da hoan thanh pipeline chuoi thoi gian dung trong tam: lam sach du lieu, EDA, "
    f"kiem tra mua vu, xay dung ARIMA/SARIMA/Holt-Winters va cac mo hinh Scikit-Learn co bien khi tuong, danh gia bang "
    f"rolling-origin CV. Mo hinh duoc chon la {forecast_model_name}; con so nen bao cao "
    f"la CV-RMSE nhieu cua so thay vi chi dua vao mot hold-out don le."
)
print("=" * 70)

print("\n✅ Phase 8 hoan tat - forecast da san sang.")

# Phase 6: Evaluation va Rolling-Origin Cross Validation

MODEL_COLORS = {
    "Holt-Winters": "firebrick",
    "Random Forest Weather": "teal",
    "Seasonal Mean": "dimgray",
}

target_label = globals().get("TARGET_LABEL", "Luong mua trung binh thang")
target_unit = globals().get("TARGET_UNIT", "mm/thang")
target_axis_label = f"{target_label} ({target_unit})"


def mape(actual: pd.Series, predicted: pd.Series) -> float:
    actual_safe = actual.replace(0, np.nan)
    pct_errors = np.abs((actual_safe - predicted) / actual_safe)
    return round(float(np.nanmean(pct_errors) * 100), 2)


def wape(actual: pd.Series, predicted: pd.Series) -> float:
    num = float(np.sum(np.abs(actual.values - predicted.values)))
    den = float(np.sum(np.abs(actual.values)))
    return round(num / den * 100, 2) if den > 0 else float("nan")


def smape(actual: pd.Series, predicted: pd.Series) -> float:
    denom = (np.abs(actual.values) + np.abs(predicted.values)) / 2.0
    with np.errstate(divide="ignore", invalid="ignore"):
        vals = np.where(denom == 0, 0.0, np.abs(actual.values - predicted.values) / denom)
    return round(float(np.mean(vals)) * 100, 2)


def rmse(actual: pd.Series, predicted: pd.Series) -> float:
    return float(np.sqrt(mean_squared_error(actual, predicted)))


def mae(actual: pd.Series, predicted: pd.Series) -> float:
    return float(mean_absolute_error(actual, predicted))


forecasts = {
    "Seasonal Mean": seasonal_mean_forecast,
    "Holt-Winters": hw_forecast,
}
if globals().get("rf_weather_forecast") is not None:
    forecasts["Random Forest Weather"] = rf_weather_forecast

rows = []
for model_name, fc in forecasts.items():
    rows.append({
        "Mo Hinh": model_name,
        "MAE": round(mae(test, fc), 2),
        "RMSE": round(rmse(test, fc), 2),
        "MAPE (%)": mape(test, fc),
        "WAPE (%)": wape(test, fc),
        "sMAPE (%)": smape(test, fc),
    })

metrics_df = pd.DataFrame(rows).set_index("Mo Hinh").sort_values("RMSE")
model_notes = {
    "Seasonal Mean": "Benchmark mua vu",
    "Holt-Winters": "Phu hop chuoi mua vu manh",
    "Random Forest Weather": "ML Scikit-Learn + importance",
}
metrics_df["Nhan xet"] = [model_notes.get(idx, "") for idx in metrics_df.index]

REPORT_MODELS = [
    "Seasonal Mean",
    "Holt-Winters",
    "Random Forest Weather",
]
report_models_available = [m for m in REPORT_MODELS if m in metrics_df.index]
report_metrics_df = metrics_df.loc[report_models_available].sort_values("RMSE")

print("=" * 74)
print(f"CHI SO DANH GIA MO HINH - TAP KIEM TRA {len(test)} THANG")
print("=" * 74)
print(report_metrics_df.to_string())
print("\nGhi chu: MAPE khong on dinh khi luong mua gan 0; WAPE va RMSE nen duoc uu tien.")


SELECT_BY_CV = True
N_CV = 6
_cv_scores, _cv_mean, _cv_wins, _win_labels = {}, {}, [], []

for k in range(1, N_CV + 1):
    train_end = len(series) - 12 * k
    if train_end < 60:
        break
    _cv_wins.append((series.iloc[:train_end], series.iloc[train_end:train_end + 12]))
_cv_wins = _cv_wins[::-1]
_win_labels = [f"{te.index[0]:%m/%y}-{te.index[-1]:%m/%y}" for _, te in _cv_wins]


def _cv_clim(tr: pd.Series, te: pd.Series) -> pd.Series:
    clim = tr.groupby(tr.index.month).mean()
    return pd.Series([clim.get(d.month, tr.mean()) for d in te.index], index=te.index)


def _cv_hw(tr: pd.Series, te: pd.Series) -> pd.Series:
    model = ExponentialSmoothing(
        tr,
        trend="add",
        seasonal="add",
        seasonal_periods=12,
        initialization_method="estimated",
    ).fit(optimized=True)
    return pd.Series(np.clip(model.forecast(len(te)).values, 0, None), index=te.index)


def _cv_rf_weather(tr: pd.Series, te: pd.Series) -> pd.Series:
    if not globals().get("WEATHER_FEATURE_COLS"):
        raise RuntimeError("khong co WEATHER_FEATURE_COLS")

    meteo_context = df_meteo_monthly_context.reindex(tr.index)[WEATHER_FEATURE_COLS]
    rows_cv, targets_cv = [], []
    for i in range(24, len(tr)):
        rows_cv.append(make_weather_feature_row(tr.iloc[:i], tr.index[i], meteo_context.iloc[:i]))
        targets_cv.append(tr.iloc[i])

    X_cv = pd.DataFrame(rows_cv)
    means_cv = X_cv.mean()
    cols_cv = X_cv.columns.tolist()
    X_cv = X_cv.fillna(means_cv)

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=8,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_cv, np.array(targets_cv))

    rain_hist = tr.copy()
    meteo_hist = meteo_context.copy()
    preds = []
    for fd in te.index:
        x_next = pd.DataFrame([make_weather_feature_row(rain_hist, fd, meteo_hist)])
        x_next = x_next.reindex(columns=cols_cv).fillna(means_cv)
        pred = max(0.0, float(model.predict(x_next)[0]))
        preds.append(pred)
        rain_hist = pd.concat([rain_hist, pd.Series([pred], index=[fd])])
        meteo_hist = pd.concat([
            meteo_hist,
            pd.DataFrame([make_meteo_proxy_row(meteo_hist, fd)], index=[fd]),
        ])
    return pd.Series(preds, index=te.index)


_cv_models = {
    "Seasonal Mean": lambda tr, te: _cv_clim(tr, te),
    "Holt-Winters": _cv_hw,
    "Random Forest Weather": _cv_rf_weather,
}

for name, fn in _cv_models.items():
    errs = []
    for tr, te in _cv_wins:
        try:
            errs.append(rmse(te, fn(tr, te)))
        except Exception as exc:
            print(f"[CV bo qua] {name}: {exc}")
            errs.append(np.nan)
    _cv_scores[name] = errs

_cv_mean = {
    name: float(np.nanmean(scores))
    for name, scores in _cv_scores.items()
    if not np.all(np.isnan(scores))
}

print("\n" + "=" * 74)
print("ROLLING-ORIGIN CROSS-VALIDATION")
print("=" * 74)
print(f"{len(_cv_wins)} cua so test 12 thang: {', '.join(_win_labels)}")
print(f"{'Mo hinh':<26}{'CV-RMSE_tb':>12}{'CV_std':>10}{'Hold-out':>12}")
print("-" * 60)
for name in [m for m in REPORT_MODELS if m in _cv_mean]:
    arr = np.array(_cv_scores[name], dtype=float)
    ho = metrics_df.loc[name, "RMSE"] if name in metrics_df.index else float("nan")
    print(f"{name:<26}{_cv_mean[name]:>12.2f}{np.nanstd(arr):>10.2f}{ho:>12.2f}")


_cv_pool = [m for m in REPORT_MODELS if m in _cv_mean]
forecast_model_name = min(_cv_pool, key=lambda m: _cv_mean[m]) if SELECT_BY_CV and _cv_pool else REPORT_MODELS[0]

forecast_forecast = forecasts[forecast_model_name]
best_forecast = forecast_forecast
best_accuracy_model = metrics_df["RMSE"].idxmin()

print("\n" + "=" * 60)
print("LUA CHON MO HINH CHO PHASE 8")
print("=" * 60)
print(f"Best hold-out RMSE       : {best_accuracy_model} ({metrics_df.loc[best_accuracy_model, 'RMSE']:.2f})")
print(f"Best CV model            : {forecast_model_name} ({_cv_mean.get(forecast_model_name, float('nan')):.2f})")
print(f"Model du bao Phase 8     : {forecast_model_name}")
print(f"CV-RMSE trung thuc nhat  : {_cv_mean.get(forecast_model_name, float('nan')):.2f} {target_unit}")
print(f"Hold-out RMSE tham khao  : {metrics_df.loc[forecast_model_name, 'RMSE']:.2f} {target_unit}")
if forecast_model_name != best_accuracy_model:
    print(f"Ghi chu: neu chi nhin hold-out se chon {best_accuracy_model}; bai uu tien CV de on dinh hon.")


fig, ax = plt.subplots(figsize=(14, 5), dpi=100)
ax.plot(test.index, test, color="black", linewidth=2.2, label="Thuc te")
for name in REPORT_MODELS:
    if name not in forecasts:
        continue
    ax.plot(test.index, forecasts[name], linewidth=1.7, linestyle="--",
            color=MODEL_COLORS.get(name, "gray"), label=name)
ax.set_title("So sanh du bao tren tap kiem tra", fontsize=13, fontweight="bold")
ax.set_xlabel("Thoi gian")
ax.set_ylabel(target_axis_label)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

_WET_MONTHS = [5, 6, 7, 8, 9, 10, 11]
_DRY_MONTHS = [12, 1, 2, 3, 4]
_test_wet = test[test.index.month.isin(_WET_MONTHS)]
_test_dry = test[test.index.month.isin(_DRY_MONTHS)]

season_rows = []
for name, fc in forecasts.items():
    row = {
        "Mo Hinh": name,
        "RMSE_all": round(rmse(test, fc), 1),
        "WAPE_all": round(wape(test, fc), 1),
    }
    fc_wet = fc[fc.index.month.isin(_WET_MONTHS)]
    fc_dry = fc[fc.index.month.isin(_DRY_MONTHS)]
    row["RMSE_mua"] = round(rmse(_test_wet, fc_wet), 1)
    row["WAPE_mua"] = round(wape(_test_wet, fc_wet), 1)
    row["RMSE_kho"] = round(rmse(_test_dry, fc_dry), 1)
    row["WAPE_kho"] = round(wape(_test_dry, fc_dry), 1)
    season_rows.append(row)

seasonal_error_df = pd.DataFrame(season_rows).set_index("Mo Hinh").sort_values("RMSE_all")
seasonal_error_report_df = seasonal_error_df.loc[
    [m for m in REPORT_MODELS if m in seasonal_error_df.index]
].sort_values("RMSE_all")
print("\n" + "=" * 74)
print("SAI SO THEO MUA")
print("=" * 74)
print(seasonal_error_report_df.to_string())


print("\n" + "=" * 60)
print("KET LUAN PHASE 6")
print("=" * 60)
print(f"Mo hinh duoc chon cho Phase 8: {forecast_model_name}.")
print("Tieu chi chinh la CV-RMSE nhieu cua so, vi dang tin hon mot tap hold-out don le.")
print("Cac metric hold-out van duoc bao cao de tham khao, nhung khong dung lam can cu duy nhat.")
print("=" * 60)

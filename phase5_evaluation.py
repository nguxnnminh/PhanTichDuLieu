from sklearn.metrics import mean_absolute_error, mean_squared_error

target_label = globals().get("TARGET_LABEL", "Lượng mưa trung bình tháng")
target_unit = globals().get("TARGET_UNIT", "mm/tháng")
target_axis_label = f"{target_label} ({target_unit})"

MODEL_COLORS = {
    "Seasonal Naive": "dimgray",
    "SARIMAX": "royalblue",
    "Prophet": "seagreen",
    "XGBoost": "firebrick",
}

def mae(actual, predicted):
    return float(mean_absolute_error(actual, predicted))


def rmse(actual, predicted):
    return float(np.sqrt(mean_squared_error(actual, predicted)))


def wape(actual, predicted):
    num = float(np.sum(np.abs(actual.values - predicted.values)))
    den = float(np.sum(np.abs(actual.values)))
    return round(num / den * 100, 2) if den > 0 else float("nan")


def smape(actual, predicted):
    denom = (np.abs(actual.values) + np.abs(predicted.values)) / 2.0
    with np.errstate(divide="ignore", invalid="ignore"):
        vals = np.where(denom == 0, 0.0, np.abs(actual.values - predicted.values) / denom)
    return round(float(np.mean(vals)) * 100, 2)


def mase(actual, predicted, train_series, season=12):
    """Mean Absolute Scaled Error — scaled by seasonal naive error on train."""
    naive_errors = np.abs(
        train_series.values[season:] - train_series.values[:-season]
    )
    scale = float(np.mean(naive_errors))
    if scale == 0:
        return float("inf")
    return round(float(np.mean(np.abs(actual.values - predicted.values))) / scale, 4)

REPORT_MODELS = ["Seasonal Naive", "SARIMAX", "Prophet", "XGBoost"]

forecasts = {"Seasonal Naive": seasonal_naive_forecast}
if globals().get("sarimax_forecast") is not None:
    forecasts["SARIMAX"] = sarimax_forecast
if globals().get("prophet_forecast") is not None:
    forecasts["Prophet"] = prophet_forecast
if globals().get("xgb_forecast") is not None:
    forecasts["XGBoost"] = xgb_forecast

rows = []
for model_name, fc in forecasts.items():
    rows.append({
        "Mô Hình": model_name,
        "MAE": round(mae(test, fc), 2),
        "RMSE": round(rmse(test, fc), 2),
        "WAPE (%)": wape(test, fc),
        "sMAPE (%)": smape(test, fc),
        "MASE": mase(test, fc, train, season=12),
    })

metrics_df = pd.DataFrame(rows).set_index("Mô Hình").sort_values("RMSE")

print("=" * 80)
print(f"CHỈ SỐ ĐÁNH GIÁ MÔ HÌNH — TẬP KIỂM TRA {len(test)} THÁNG")
print("=" * 80)
print(metrics_df.to_string())
print("\nGhi chú: MAPE không được dùng vì tháng mùa khô có lượng mưa gần 0.")
print("WAPE, RMSE và MASE là các chỉ số ưu tiên.")

N_CV = 6
_cv_wins = []

for k in range(1, N_CV + 1):
    train_end = len(series) - 12 * k
    if train_end < 60:
        break
    _cv_wins.append((series.iloc[:train_end], series.iloc[train_end:train_end + 12]))
_cv_wins = _cv_wins[::-1]
_win_labels = [f"{te.index[0]:%m/%y}–{te.index[-1]:%m/%y}" for _, te in _cv_wins]

def _cv_seasonal_naive(tr, te):
    return pd.Series(
        [tr[tr.index.month == d.month].iloc[-1] for d in te.index],
        index=te.index,
    )


def _cv_sarimax(tr, te):
    _order = globals().get("sarimax_order", (1, 0, 1))
    _seasonal = globals().get("sarimax_seasonal_order", (1, 0, 1, 12))

    exog_full = df_meteo_monthly_context.reindex(series.index)[SARIMAX_EXOG_COLS]
    exog_full = exog_full.shift(1).interpolate(method="time").ffill().bfill()

    exog_tr = exog_full.reindex(tr.index)
    exog_te = exog_full.reindex(te.index)

    model = SARIMAX(
        tr, exog=exog_tr,
        order=_order, seasonal_order=_seasonal,
        enforce_stationarity=False, enforce_invertibility=False,
    ).fit(disp=False, maxiter=50)
    return pd.Series(
        np.clip(model.forecast(len(te), exog=exog_te).values, 0, None),
        index=te.index,
    )


def _cv_prophet(tr, te):
    df_train = pd.DataFrame({"ds": tr.index, "y": tr.values})
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        seasonality_mode="additive",
        changepoint_prior_scale=0.05,
    )
    model.fit(df_train)
    future = model.make_future_dataframe(periods=len(te), freq="MS")
    pred = model.predict(future)
    return pd.Series(
        np.clip(pred.iloc[-len(te):]["yhat"].values, 0, None),
        index=te.index,
    )


def _cv_xgboost(tr, te):
    meteo_context = df_meteo_monthly_context.reindex(tr.index)[WEATHER_FEATURE_COLS]
    rows_cv, targets_cv = [], []
    for i in range(24, len(tr)):
        rows_cv.append(
            make_xgb_feature_row(tr.iloc[:i], tr.index[i], meteo_context.iloc[:i])
        )
        targets_cv.append(tr.iloc[i])

    X_cv = pd.DataFrame(rows_cv)
    means_cv = X_cv.mean()
    cols_cv = X_cv.columns.tolist()
    X_cv = X_cv.fillna(means_cv)

    model = XGBRegressor(
        n_estimators=200, max_depth=4, learning_rate=0.05,
        min_child_weight=5, subsample=0.8, colsample_bytree=0.8,
        random_state=42, verbosity=0,
    )
    model.fit(X_cv, np.array(targets_cv))

    rain_hist = tr.copy()
    meteo_hist = meteo_context.copy()
    preds = []
    for fd in te.index:
        x_next = pd.DataFrame([make_xgb_feature_row(rain_hist, fd, meteo_hist)])
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
    "Seasonal Naive": _cv_seasonal_naive,
    "SARIMAX": _cv_sarimax,
    "Prophet": _cv_prophet,
    "XGBoost": _cv_xgboost,
}

_cv_scores = {}
for name, fn in _cv_models.items():
    errs = []
    for tr, te in _cv_wins:
        try:
            errs.append(rmse(te, fn(tr, te)))
        except Exception as exc:
            print(f"[CV bỏ qua] {name}: {exc}")
            errs.append(np.nan)
    _cv_scores[name] = errs

_cv_mean = {
    name: float(np.nanmean(scores))
    for name, scores in _cv_scores.items()
    if not np.all(np.isnan(scores))
}

print("\n" + "=" * 80)
print("ROLLING-ORIGIN CROSS-VALIDATION")
print("=" * 80)
print(f"{len(_cv_wins)} cửa sổ test 12 tháng: {', '.join(_win_labels)}")
print(f"{'Mô hình':<20}{'CV-RMSE_tb':>14}{'CV_std':>10}{'Hold-out':>12}")
print("-" * 56)
for name in [m for m in REPORT_MODELS if m in _cv_mean]:
    arr = np.array(_cv_scores[name], dtype=float)
    ho = metrics_df.loc[name, "RMSE"] if name in metrics_df.index else float("nan")
    print(f"{name:<20}{_cv_mean[name]:>14.2f}{np.nanstd(arr):>10.2f}{ho:>12.2f}")

_cv_pool = [m for m in REPORT_MODELS if m in _cv_mean]
forecast_model_name = min(_cv_pool, key=lambda m: _cv_mean[m]) if _cv_pool else "Seasonal Naive"
forecast_forecast = forecasts[forecast_model_name]
best_forecast = forecast_forecast
best_accuracy_model = metrics_df["RMSE"].idxmin()

print("\n" + "=" * 60)
print("LỰA CHỌN MÔ HÌNH CHO PHASE 7")
print("=" * 60)
print(f"Best hold-out RMSE       : {best_accuracy_model} ({metrics_df.loc[best_accuracy_model, 'RMSE']:.2f})")
print(f"Best CV model            : {forecast_model_name} ({_cv_mean.get(forecast_model_name, float('nan')):.2f})")
print(f"Mô hình dự báo Phase 7  : {forecast_model_name}")

fig, ax = plt.subplots(figsize=(14, 5), dpi=100)
ax.plot(test.index, test, color="black", linewidth=2.2, label="Thực tế")
for name in REPORT_MODELS:
    if name not in forecasts:
        continue
    ax.plot(
        test.index, forecasts[name],
        linewidth=1.7, linestyle="--",
        color=MODEL_COLORS.get(name, "gray"),
        label=name,
    )
ax.set_title("So sánh dự báo trên tập kiểm tra", fontsize=13, fontweight="bold")
ax.set_xlabel("Thời gian")
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
        "Mô Hình": name,
        "RMSE_all": round(rmse(test, fc), 1),
        "WAPE_all": round(wape(test, fc), 1),
    }
    fc_wet = fc[fc.index.month.isin(_WET_MONTHS)]
    fc_dry = fc[fc.index.month.isin(_DRY_MONTHS)]
    row["RMSE_mưa"] = round(rmse(_test_wet, fc_wet), 1)
    row["WAPE_mưa"] = round(wape(_test_wet, fc_wet), 1)
    row["RMSE_khô"] = round(rmse(_test_dry, fc_dry), 1)
    row["WAPE_khô"] = round(wape(_test_dry, fc_dry), 1)
    season_rows.append(row)

seasonal_error_df = pd.DataFrame(season_rows).set_index("Mô Hình").sort_values("RMSE_all")
print("\n" + "=" * 80)
print("SAI SỐ THEO MÙA")
print("=" * 80)
print(seasonal_error_df.to_string())

print("\n" + "=" * 60)
print("KẾT LUẬN PHASE 5")
print("=" * 60)
print(f"Mô hình được chọn cho Phase 7: {forecast_model_name}.")
print("Tiêu chí chính là CV-RMSE nhiều cửa sổ, đáng tin hơn hold-out đơn lẻ.")
print("=" * 60)

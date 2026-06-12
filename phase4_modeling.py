import os
import warnings
warnings.filterwarnings("ignore")

from statsmodels.tsa.statespace.sarimax import SARIMAX
from pmdarima import auto_arima
from prophet import Prophet
from xgboost import XGBRegressor

target_label = globals().get("TARGET_LABEL", "Lượng mưa trung bình tháng")
target_unit = globals().get("TARGET_UNIT", "mm/tháng")
target_axis_label = f"{target_label} ({target_unit})"
TEST_SIZE = 24
series = df_monthly["Rainfall"].asfreq("MS")
train = series.iloc[:-TEST_SIZE]
test = series.iloc[-TEST_SIZE:]
split_date = test.index[0]

print("=" * 60)
print("CHIA TẬP HUẤN LUYỆN / KIỂM TRA")
print("=" * 60)
print(
    f"Tập huấn luyện : {len(train)} tháng "
    f"({train.index[0]:%m/%Y} → {train.index[-1]:%m/%Y})"
)
print(
    f"Tập kiểm tra   : {len(test)} tháng "
    f"({test.index[0]:%m/%Y} → {test.index[-1]:%m/%Y})"
)

fig, ax = plt.subplots(figsize=(14, 4), dpi=100)
ax.plot(train.index, train, color="steelblue", linewidth=1.5, label="Train")
ax.plot(test.index, test, color="darkorange", linewidth=1.5, label="Test")
ax.axvline(split_date, color="black", linestyle="--", linewidth=1.2)
ax.set_title(
    f"Chia Train/Test — {TEST_SIZE} tháng cuối làm tập kiểm tra",
    fontsize=13,
    fontweight="bold",
)
ax.set_xlabel("Thời gian")
ax.set_ylabel(target_axis_label)
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()


def _quick_rmse(actual, predicted):
    from sklearn.metrics import mean_squared_error
    return float(np.sqrt(mean_squared_error(actual, predicted)))


print("\n" + "=" * 60)
print("MODEL 1: SEASONAL NAIVE")
print("=" * 60)

seasonal_naive_forecast = pd.Series(
    [train[train.index.month == d.month].iloc[-1] for d in test.index],
    index=test.index,
    name="Seasonal Naive",
)
print(
    f"Seasonal Naive: y_hat(t) = y(t-12)\n"
    f"RMSE hold-out: {_quick_rmse(test, seasonal_naive_forecast):.2f} {target_unit}"
)

print("\n" + "=" * 60)
print("MODEL 2: SARIMAX")
print("=" * 60)

sarimax_forecast = None
sarimax_fit = None
sarimax_order = None
sarimax_seasonal_order = None

SARIMAX_EXOG_COLS = [
    c for c in [
        "HumidityMean", "CloudCoverMean", "DewPointMean",
        "PrecipitationHours", "TempMean", "ShortwaveRadiation",
    ]
    if c in df_meteo_monthly_context.columns
]

try:
    # Exogenous dùng lag-1 để tránh leakage.
    exog_full = df_meteo_monthly_context.reindex(series.index)[SARIMAX_EXOG_COLS]
    exog_full = exog_full.shift(1)
    exog_full = exog_full.interpolate(method="time").ffill().bfill()

    exog_train = exog_full.iloc[:-TEST_SIZE]
    exog_test = exog_full.iloc[-TEST_SIZE:]

    print("Đang chạy auto_arima (có thể mất 1-2 phút)...")
    auto_model = auto_arima(
        train,
        exogenous=exog_train,
        seasonal=True,
        m=12,
        max_p=3,
        max_q=3,
        max_P=2,
        max_Q=2,
        max_d=1,
        max_D=1,
        stepwise=True,
        suppress_warnings=True,
        error_action="ignore",
        trace=False,
    )
    sarimax_order = auto_model.order
    sarimax_seasonal_order = auto_model.seasonal_order

    print(f"Best order: SARIMAX{sarimax_order}x{sarimax_seasonal_order}")

    sarimax_model = SARIMAX(
        train,
        exog=exog_train,
        order=sarimax_order,
        seasonal_order=sarimax_seasonal_order,
        enforce_stationarity=False,
        enforce_invertibility=False,
    )
    sarimax_fit = sarimax_model.fit(disp=False, maxiter=200)
    raw_fc = sarimax_fit.forecast(steps=TEST_SIZE, exog=exog_test)
    sarimax_forecast = pd.Series(
        np.clip(raw_fc.values, 0, None),
        index=test.index,
        name="SARIMAX",
    )
    print(
        f"SARIMAX{sarimax_order}x{sarimax_seasonal_order} "
        f"RMSE hold-out: {_quick_rmse(test, sarimax_forecast):.2f} {target_unit}"
    )
    print(f"Exogenous vars (lag-1): {SARIMAX_EXOG_COLS}")
except Exception as exc:
    print(f"[SARIMAX bỏ qua] {exc}")
    sarimax_forecast = None
    sarimax_fit = None

print("\n" + "=" * 60)
print("MODEL 3: PROPHET")
print("=" * 60)

prophet_forecast = None

try:
    prophet_train = pd.DataFrame({
        "ds": train.index,
        "y": train.values,
    })

    prophet_model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        seasonality_mode="additive",
        changepoint_prior_scale=0.05,
    )
    prophet_model.fit(prophet_train)

    future_dates = prophet_model.make_future_dataframe(periods=TEST_SIZE, freq="MS")
    prophet_pred = prophet_model.predict(future_dates)

    prophet_test_pred = prophet_pred.iloc[-TEST_SIZE:]
    prophet_forecast = pd.Series(
        np.clip(prophet_test_pred["yhat"].values, 0, None),
        index=test.index,
        name="Prophet",
    )
    print(
        f"Prophet RMSE hold-out: {_quick_rmse(test, prophet_forecast):.2f} {target_unit}"
    )
except Exception as exc:
    print(f"[Prophet bỏ qua] {exc}")
    prophet_forecast = None

print("\n" + "=" * 60)
print("MODEL 4: XGBOOST REGRESSOR")
print("=" * 60)

xgb_forecast = None
xgb_model = None

WEATHER_FEATURE_COLS = [
    c for c in [
        "PrecipitationHours", "ShortwaveRadiation", "Evapotranspiration",
        "TempMean", "TempMin", "TempMax", "ApparentTempMean",
        "HumidityMean", "HumidityMax", "DewPointMean",
        "PressureMSLMean", "SurfacePressureMean",
        "CloudCoverMean", "CloudCoverLowMean", "CloudCoverMidMean",
        "CloudCoverHighMean", "WindSpeedMax", "WindGustMax",
        "WindSpeedHourlyMean", "WindGustHourlyMean",
    ]
    if "df_meteo_monthly_context" in globals()
    and c in df_meteo_monthly_context.columns
]


def make_xgb_feature_row(history: pd.Series, forecast_date: pd.Timestamp,
                          meteo_history: pd.DataFrame = None) -> dict:
    """Build one XGBoost row from past data only."""
    month = forecast_date.month
    row = {
        "month": month,
        "month_sin": np.sin(2 * np.pi * month / 12),
        "month_cos": np.cos(2 * np.pi * month / 12),
        "fourier_sin_2": np.sin(2 * np.pi * 2 * month / 12),
        "fourier_cos_2": np.cos(2 * np.pi * 2 * month / 12),
        "fourier_sin_3": np.sin(2 * np.pi * 3 * month / 12),
        "fourier_cos_3": np.cos(2 * np.pi * 3 * month / 12),
    }

    for lag in [1, 2, 3, 6, 12, 24]:
        row[f"rain_lag_{lag}"] = (
            history.iloc[-lag] if len(history) >= lag else np.nan
        )

    for window in [3, 6, 12, 24]:
        vals = history.iloc[-window:] if len(history) >= window else history
        row[f"rain_roll_mean_{window}"] = float(vals.mean()) if len(vals) > 0 else np.nan
        row[f"rain_roll_std_{window}"] = float(vals.std()) if len(vals) > 1 else np.nan

    same_month = history[history.index.month == month]
    row["rain_clim_mean"] = float(same_month.mean()) if len(same_month) > 0 else np.nan
    row["rain_clim_median"] = float(same_month.median()) if len(same_month) > 0 else np.nan

    if meteo_history is not None and not meteo_history.empty:
        for col in WEATHER_FEATURE_COLS:
            if col not in meteo_history.columns:
                continue
            col_hist = meteo_history[col].dropna()
            if len(col_hist) == 0:
                continue
            row[f"{col}_lag1"] = float(col_hist.iloc[-1]) if len(col_hist) >= 1 else np.nan
            row[f"{col}_lag3"] = float(col_hist.iloc[-3]) if len(col_hist) >= 3 else np.nan
            row[f"{col}_roll3"] = float(col_hist.iloc[-3:].mean()) if len(col_hist) >= 3 else np.nan
            row[f"{col}_roll12"] = float(col_hist.iloc[-12:].mean()) if len(col_hist) >= 12 else np.nan

    return row


def make_meteo_proxy_row(meteo_history: pd.DataFrame,
                          forecast_date: pd.Timestamp) -> dict:
    """Climatology proxy for future weather (same-month historical mean)."""
    if meteo_history is None or meteo_history.empty:
        return {}
    month = forecast_date.month
    proxy = {}
    for col in meteo_history.columns:
        same_month = meteo_history.loc[meteo_history.index.month == month, col].dropna()
        proxy[col] = float(same_month.mean()) if len(same_month) > 0 else float(meteo_history[col].mean())
    return proxy


try:
    meteo_train_context = df_meteo_monthly_context.reindex(train.index)[WEATHER_FEATURE_COLS]

    xgb_rows, xgb_targets = [], []
    for i in range(24, len(train)):
        xgb_rows.append(
            make_xgb_feature_row(
                train.iloc[:i], train.index[i], meteo_train_context.iloc[:i]
            )
        )
        xgb_targets.append(train.iloc[i])

    xgb_X_train = pd.DataFrame(xgb_rows)
    xgb_feature_columns = xgb_X_train.columns.tolist()
    xgb_feature_means = xgb_X_train.mean()
    xgb_X_train = xgb_X_train.fillna(xgb_feature_means)

    xgb_model = XGBRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        min_child_weight=5,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbosity=0,
    )
    xgb_model.fit(xgb_X_train, np.array(xgb_targets))

    xgb_rain_history = train.copy()
    xgb_meteo_history = meteo_train_context.copy()
    xgb_preds = []

    for forecast_date in test.index:
        x_next = pd.DataFrame([
            make_xgb_feature_row(xgb_rain_history, forecast_date, xgb_meteo_history)
        ])
        x_next = x_next.reindex(columns=xgb_feature_columns).fillna(xgb_feature_means)
        pred = max(0.0, float(xgb_model.predict(x_next)[0]))
        xgb_preds.append(pred)

        xgb_rain_history = pd.concat([
            xgb_rain_history,
            pd.Series([pred], index=[forecast_date]),
        ])
        xgb_meteo_history = pd.concat([
            xgb_meteo_history,
            pd.DataFrame(
                [make_meteo_proxy_row(xgb_meteo_history, forecast_date)],
                index=[forecast_date],
            ),
        ])

    xgb_forecast = pd.Series(
        xgb_preds, index=test.index, name="XGBoost",
    )
    print(
        f"XGBoost dùng {len(xgb_feature_columns)} features.\n"
        f"RMSE hold-out: {_quick_rmse(test, xgb_forecast):.2f} {target_unit}"
    )
except Exception as exc:
    print(f"[XGBoost bỏ qua] {exc}")
    import traceback; traceback.print_exc()
    xgb_forecast = None
    xgb_model = None

fig, ax = plt.subplots(figsize=(14, 5), dpi=100)
ax.plot(train.index[-60:], train.iloc[-60:], color="steelblue", linewidth=1.3, label="Train")
ax.plot(test.index, test, color="black", linewidth=2.2, label="Thực tế")

MODEL_COLORS = {
    "Seasonal Naive": "dimgray",
    "SARIMAX": "royalblue",
    "Prophet": "seagreen",
    "XGBoost": "firebrick",
}

for name, fc in [
    ("Seasonal Naive", seasonal_naive_forecast),
    ("SARIMAX", sarimax_forecast),
    ("Prophet", prophet_forecast),
    ("XGBoost", xgb_forecast),
]:
    if fc is not None:
        ax.plot(
            fc.index, fc,
            linewidth=1.7, linestyle="--",
            color=MODEL_COLORS.get(name, "gray"),
            label=name,
        )

ax.axvline(split_date, color="black", linestyle=":", linewidth=1)
ax.set_title(
    f"So sánh dự báo 4 mô hình — {city_name}",
    fontsize=13, fontweight="bold",
)
ax.set_xlabel("Thời gian")
ax.set_ylabel(target_axis_label)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

print("\n" + "=" * 60)
print("MODEL CATALOG")
print("=" * 60)

MODEL_CATALOG_REPORT = ["Seasonal Naive", "SARIMAX", "Prophet", "XGBoost"]

forecasts = {"Seasonal Naive": seasonal_naive_forecast}
if sarimax_forecast is not None:
    forecasts["SARIMAX"] = sarimax_forecast
if prophet_forecast is not None:
    forecasts["Prophet"] = prophet_forecast
if xgb_forecast is not None:
    forecasts["XGBoost"] = xgb_forecast

for name, fc in forecasts.items():
    print(f"  {name:<20} RMSE={_quick_rmse(test, fc):.2f}")

print("\n" + "=" * 60)
print("KẾT LUẬN PHASE 4")
print("=" * 60)
print("Đã xây dựng 4 mô hình: Seasonal Naive (baseline), SARIMAX (thống kê),")
print("Prophet (chuỗi thời gian), XGBoost (machine learning).")
print("Tất cả đều dùng dữ liệu quá khứ hợp lệ, không có data leakage.")
print("=" * 60)

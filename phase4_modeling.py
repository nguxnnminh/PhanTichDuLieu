# Phase 4: Modeling - 3 Models (Baseline, Statistical, Machine Learning)

target_label = globals().get("TARGET_LABEL", "Luong mua trung binh thang")
target_unit = globals().get("TARGET_UNIT", "mm/thang")
target_axis_label = f"{target_label} ({target_unit})"

from sklearn.ensemble import RandomForestRegressor

SHOW_MODEL_SUMMARY = False

TEST_SIZE = 24
series = df_monthly["Rainfall"].asfreq("MS")
train = series.iloc[:-TEST_SIZE]
test = series.iloc[-TEST_SIZE:]
split_date = test.index[0]

print("=" * 60)
print("CHIA TAP HUAN LUYEN / KIEM TRA")
print("=" * 60)
print(f"Tap huan luyen : {len(train)} thang ({train.index[0]:%m/%Y} -> {train.index[-1]:%m/%Y})")
print(f"Tap kiem tra   : {len(test)} thang ({test.index[0]:%m/%Y} -> {test.index[-1]:%m/%Y})")

fig, ax = plt.subplots(figsize=(14, 4), dpi=100)
ax.plot(train.index, train, color="steelblue", linewidth=1.5, label="Train")
ax.plot(test.index, test, color="darkorange", linewidth=1.5, label="Test")
ax.axvline(split_date, color="black", linestyle="--", linewidth=1.2)
ax.set_title(f"Chia Train/Test - {TEST_SIZE} thang cuoi lam tap kiem tra", fontsize=13, fontweight="bold")
ax.set_xlabel("Thoi gian")
ax.set_ylabel(target_axis_label)
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

model_catalog_rows = []


def register_model(model_name, model_type, uses_weather, note):
    model_catalog_rows.append({
        "Model": model_name,
        "Loai model": model_type,
        "Dung weather": "Co" if uses_weather else "Khong",
        "Ghi chu": note,
    })


def _quick_rmse(actual: pd.Series, predicted: pd.Series) -> float:
    return float(np.sqrt(mean_squared_error(actual, predicted)))


# ============================================================
# BASELINE: Seasonal Mean
# ============================================================
print("\n" + "=" * 60)
print("BASELINE")
print("=" * 60)

_train_month = train.to_frame("Rainfall")
_train_month["Month"] = _train_month.index.month
monthly_climatology = _train_month.groupby("Month")["Rainfall"].mean()
seasonal_mean_forecast = pd.Series(
    [monthly_climatology[d.month] for d in test.index],
    index=test.index,
    name="Seasonal Mean",
)
register_model("Seasonal Mean", "Baseline", False, "Trung binh lich su theo thang")
print(f"Seasonal Mean tao xong - RMSE: {_quick_rmse(test, seasonal_mean_forecast):.2f} {target_unit}")

# ============================================================
# STATISTICAL: Holt-Winters
# ============================================================
print("\n" + "=" * 60)
print("HOLT-WINTERS")
print("=" * 60)

hw_model = ExponentialSmoothing(
    train,
    trend="add",
    seasonal="add",
    seasonal_periods=12,
    initialization_method="estimated",
)
hw_fit = hw_model.fit(optimized=True)
if SHOW_MODEL_SUMMARY:
    print(hw_fit.summary())
register_model("Holt-Winters", "Statistical", False, "Exponential smoothing mua vu")

hw_raw_fc = hw_fit.forecast(steps=TEST_SIZE)
hw_forecast = pd.Series(np.clip(hw_raw_fc.values, 0, None), index=test.index, name="Holt-Winters")

fig, ax = plt.subplots(figsize=(14, 5), dpi=100)
ax.plot(train.index, train, color="steelblue", linewidth=1.3, label="Train")
ax.plot(test.index, test, color="darkorange", linewidth=1.8, label="Thuc te")
ax.plot(hw_forecast.index, hw_forecast, color="firebrick", linewidth=2, linestyle="--", label="Holt-Winters")
ax.axvline(split_date, color="black", linestyle=":", linewidth=1)
ax.set_title(f"Holt-Winters: du bao vs thuc te - {city_name}", fontsize=13, fontweight="bold")
ax.set_xlabel("Thoi gian")
ax.set_ylabel(target_axis_label)
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
print(f"Holt-Winters RMSE hold-out: {_quick_rmse(test, hw_forecast):.2f} {target_unit}")

# ============================================================
# MACHINE LEARNING: Random Forest Weather
# ============================================================
print("\n" + "=" * 70)
print("MACHINE LEARNING MODELS - SCIKIT-LEARN")
print("=" * 70)

WEATHER_FEATURE_COLS = [
    c for c in [
        "PrecipitationHours",
        "ShortwaveRadiation",
        "Evapotranspiration",
        "TempMean",
        "TempMin",
        "TempMax",
        "ApparentTempMean",
        "HumidityMean",
        "HumidityMax",
        "DewPointMean",
        "PressureMSLMean",
        "SurfacePressureMean",
        "CloudCoverMean",
        "CloudCoverLowMean",
        "CloudCoverMidMean",
        "CloudCoverHighMean",
        "WindSpeedMax",
        "WindGustMax",
        "WindSpeedHourlyMean",
        "WindGustHourlyMean",
    ]
    if "df_meteo_monthly_context" in globals()
    and c in df_meteo_monthly_context.columns
]


def make_lag_feature_row(history: pd.Series, forecast_date: pd.Timestamp) -> dict:
    month = forecast_date.month
    same_month_history = history[history.index.month == month]
    row = {
        "month": month,
        "sin12": np.sin(2 * np.pi * month / 12),
        "cos12": np.cos(2 * np.pi * month / 12),
        "last_year_same_month": same_month_history.iloc[-1] if len(same_month_history) else np.nan,
        "clim_mean": history.groupby(history.index.month).mean().get(month, history.mean()),
        "clim_median": history.groupby(history.index.month).median().get(month, history.median()),
        "global_mean": history.mean(),
        "global_median": history.median(),
    }
    for lag in [1, 2, 3, 6, 12, 24]:
        row[f"lag{lag}"] = history.iloc[-lag] if len(history) >= lag else np.nan
    for window in [3, 6, 12, 24]:
        row[f"roll{window}"] = history.iloc[-window:].mean() if len(history) >= window else np.nan
    return row


def make_meteo_proxy_row(meteo_history: pd.DataFrame, forecast_date: pd.Timestamp) -> dict:
    if meteo_history is None or meteo_history.empty:
        return {}
    month = forecast_date.month
    proxy = {}
    for col in meteo_history.columns:
        same_month = meteo_history.loc[meteo_history.index.month == month, col].dropna()
        proxy[col] = float(same_month.mean()) if len(same_month) else float(meteo_history[col].mean())
    return proxy


def make_weather_feature_row(
    rain_history: pd.Series,
    forecast_date: pd.Timestamp,
    meteo_history: pd.DataFrame | None,
) -> dict:
    row = make_lag_feature_row(rain_history, forecast_date)
    month = forecast_date.month

    if meteo_history is None or meteo_history.empty or not WEATHER_FEATURE_COLS:
        return row

    meteo_history = meteo_history[WEATHER_FEATURE_COLS].copy()
    proxy = make_meteo_proxy_row(meteo_history, forecast_date)

    for col in WEATHER_FEATURE_COLS:
        col_hist = meteo_history[col].dropna()
        same_month = col_hist[col_hist.index.month == month]
        row[f"{col}_clim"] = proxy.get(col, np.nan)
        row[f"{col}_same_month_median"] = float(same_month.median()) if len(same_month) else np.nan
        row[f"{col}_last"] = float(col_hist.iloc[-1]) if len(col_hist) else np.nan
        for window in [3, 6, 12]:
            row[f"{col}_roll{window}"] = float(col_hist.iloc[-window:].mean()) if len(col_hist) >= window else np.nan

    return row


print("\n" + "=" * 60)
print("RANDOM FOREST WEATHER - SCIKIT-LEARN")
print("=" * 60)

rf_weather_forecast = None
rf_weather_model = None

try:
    if not WEATHER_FEATURE_COLS:
        raise RuntimeError("Khong co bien khi tuong phu hop cho Random Forest Weather.")

    meteo_train_context = df_meteo_monthly_context.reindex(train.index)[WEATHER_FEATURE_COLS]
    rf_rows, rf_targets = [], []
    for i in range(24, len(train)):
        rf_rows.append(
            make_weather_feature_row(train.iloc[:i], train.index[i], meteo_train_context.iloc[:i])
        )
        rf_targets.append(train.iloc[i])

    rf_X_train = pd.DataFrame(rf_rows)
    rf_feature_columns = rf_X_train.columns.tolist()
    rf_feature_means = rf_X_train.mean()
    rf_X_train = rf_X_train.fillna(rf_feature_means)
    rf_y_train = np.array(rf_targets)

    rf_weather_model = RandomForestRegressor(
        n_estimators=300,
        max_depth=8,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1,
    )
    rf_weather_model.fit(rf_X_train, rf_y_train)

    rf_rain_history = train.copy()
    rf_meteo_history = meteo_train_context.copy()
    rf_preds = []
    for forecast_date in test.index:
        x_next = pd.DataFrame([
            make_weather_feature_row(rf_rain_history, forecast_date, rf_meteo_history)
        ])
        x_next = x_next.reindex(columns=rf_feature_columns).fillna(rf_feature_means)
        pred = max(0.0, float(rf_weather_model.predict(x_next)[0]))
        rf_preds.append(pred)
        rf_rain_history = pd.concat([
            rf_rain_history,
            pd.Series([pred], index=[forecast_date]),
        ])
        rf_meteo_history = pd.concat([
            rf_meteo_history,
            pd.DataFrame([make_meteo_proxy_row(rf_meteo_history, forecast_date)], index=[forecast_date]),
        ])

    rf_weather_forecast = pd.Series(
        rf_preds,
        index=test.index,
        name="Random Forest Weather",
    )
    register_model("Random Forest Weather", "Machine Learning", True, "Scikit-Learn, co feature importance")

    fig, ax = plt.subplots(figsize=(14, 5), dpi=100)
    ax.plot(train.index, train, color="steelblue", linewidth=1.3, label="Train")
    ax.plot(test.index, test, color="darkorange", linewidth=1.8, label="Thuc te")
    ax.plot(rf_weather_forecast.index, rf_weather_forecast,
            color="teal", linewidth=2, linestyle="--", label="Random Forest Weather")
    ax.axvline(split_date, color="black", linestyle=":", linewidth=1)
    ax.set_title(f"Random Forest Weather: du bao vs thuc te - {city_name}",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("Thoi gian")
    ax.set_ylabel(target_axis_label)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

    print(f"Random Forest Weather dung {len(rf_feature_columns)} features.")
    print(f"RMSE hold-out: {_quick_rmse(test, rf_weather_forecast):.2f} {target_unit}")
except Exception as exc:
    print(f"[Random Forest Weather bo qua] {exc}")
    rf_weather_forecast = None
    rf_weather_model = None


print("\n" + "=" * 60)
print("MODEL CATALOG - BANG NGAN CHO SLIDE")
print("=" * 60)
model_catalog_df = pd.DataFrame(model_catalog_rows).drop_duplicates(subset=["Model"])
MODEL_CATALOG_REPORT = [
    "Seasonal Mean",
    "Holt-Winters",
    "Random Forest Weather",
]
model_catalog_report_df = (
    model_catalog_df
    .set_index("Model")
    .reindex([m for m in MODEL_CATALOG_REPORT if m in model_catalog_df["Model"].values])
    .reset_index()
)
print(model_catalog_report_df.to_string(index=False))

print("\n" + "=" * 60)
print("KET LUAN PHASE 4")
print("=" * 60)
print("Da xay dung 3 mo hinh dai dien: Baseline (Seasonal Mean), Statistical (Holt-Winters), ML (Random Forest Weather).")
print("Random Forest Weather khong dung khi tuong tuong lai that; test/future dung proxy/climatology.")
print("=" * 60)

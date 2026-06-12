print("=" * 70)
print("PHASE 3 — FEATURE ENGINEERING")
print("=" * 70)


WEATHER_BASE_COLS = [
    "PrecipitationHours",
    "ShortwaveRadiation",
    "Evapotranspiration",
    "TempMean",
    "TempMin",
    "TempMax",
    "ApparentTempMean",
    "WindSpeedMax",
    "WindGustMax",
    "HumidityMean",
    "HumidityMax",
    "DewPointMean",
    "PressureMSLMean",
    "SurfacePressureMean",
    "CloudCoverMean",
    "CloudCoverLowMean",
    "CloudCoverMidMean",
    "CloudCoverHighMean",
    "WindSpeedHourlyMean",
    "WindGustHourlyMean",
]


def build_ml_features(df_monthly: pd.DataFrame):
    df = df_monthly.copy()
    df = df.sort_index()
    y = df["Rainfall"].asfreq("MS")

    # Chống leakage: lag/rolling chỉ dùng dữ liệu trước tháng dự báo.
    feature_groups = {
        "time": [],
        "fourier": [],
        "rainfall_lag": [],
        "rainfall_rolling": [],
        "weather_lag": [],
        "weather_rolling": [],
    }

    df["month"] = df.index.month
    df["quarter"] = df.index.quarter
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    feature_groups["time"].extend(["month", "quarter", "month_sin", "month_cos"])

    for k in [1, 2, 3]:
        sin_col = f"fourier_sin_{k}"
        cos_col = f"fourier_cos_{k}"
        df[sin_col] = np.sin(2 * np.pi * k * df.index.month / 12)
        df[cos_col] = np.cos(2 * np.pi * k * df.index.month / 12)
        feature_groups["fourier"].extend([sin_col, cos_col])

    for lag in [1, 2, 3, 6, 12, 24, 36]:
        col = f"rain_lag_{lag}"
        df[col] = y.shift(lag)
        feature_groups["rainfall_lag"].append(col)

    for window in [3, 6, 12, 24]:
        mean_col = f"rain_roll_mean_{window}"
        std_col = f"rain_roll_std_{window}"
        df[mean_col] = y.shift(1).rolling(window).mean()
        df[std_col] = y.shift(1).rolling(window).std()
        feature_groups["rainfall_rolling"].extend([mean_col, std_col])

    available_weather_cols = [c for c in WEATHER_BASE_COLS if c in df.columns]
    for col in available_weather_cols:
        lag1 = f"{col}_lag1"
        lag3 = f"{col}_lag3"
        roll3 = f"{col}_roll3"
        roll12 = f"{col}_roll12"
        df[lag1] = df[col].shift(1)
        df[lag3] = df[col].shift(3)
        df[roll3] = df[col].shift(1).rolling(3).mean()
        df[roll12] = df[col].shift(1).rolling(12).mean()
        feature_groups["weather_lag"].extend([lag1, lag3])
        feature_groups["weather_rolling"].extend([roll3, roll12])

    feature_df = df.dropna().copy()
    y_ml = feature_df["Rainfall"].copy()

    all_feature_cols = []
    for cols in feature_groups.values():
        all_feature_cols.extend(cols)

    X_ml = feature_df[all_feature_cols].copy()
    X_ml = X_ml.select_dtypes(include=[np.number])

    feature_groups = {
        group: [c for c in cols if c in X_ml.columns]
        for group, cols in feature_groups.items()
    }

    return X_ml, y_ml, feature_df, feature_groups


X_ml, y_ml, feature_df, feature_groups = build_ml_features(df_monthly)

print(f"Shape X_ml                    : {X_ml.shape}")
print(f"Số dòng sau khi drop NaN       : {len(feature_df)}")
print(
    f"Thời gian supervised dataset   : "
    f"{feature_df.index.min():%m/%Y} → {feature_df.index.max():%m/%Y}"
)
print("\nSố feature theo nhóm:")
for group_name, cols in feature_groups.items():
    print(f"  {group_name:<18}: {len(cols)}")

print("\nGhi chú leakage:")
print("- Weather features chỉ dùng lag/rolling quá khứ, không dùng giá trị cùng tháng.")
print("- Rolling features dùng shift(1).rolling(...) để không nhìn vào tháng đang dự báo.")

print("=" * 70)
print("✅ Phase 3 hoàn tất — X_ml, y_ml, feature_df, feature_groups đã sẵn sàng.")
print("=" * 70)

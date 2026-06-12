# Phase 1: Tải dữ liệu & Tiền xử lý
# ─────────────────────────────────────────────────────────────────
# Đọc dữ liệu monthly đã được tổng hợp từ 7 tọa độ đại diện TP.HCM.
# Kiểm tra chất lượng, impute nếu cần, chuẩn bị df_monthly cho pipeline.

import os
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings("ignore")

# ── Constants ──────────────────────────────────────────────────
OPENMETEO_MONTHLY_PATH = "hcmc_openmeteo_monthly.csv"
city_name = "TP. Hồ Chí Minh"

PROJECT_TITLE = (
    "Phân tích và dự báo lượng mưa trung bình "
    "của Thành phố Hồ Chí Minh dựa trên dữ liệu khí tượng"
)
TARGET_AGG = "monthly_total"
TARGET_LABEL = "Lượng mưa trung bình tháng"
TARGET_UNIT = "mm/tháng"
TARGET_DEFINITION = (
    "Mỗi ngày: trung bình không gian rain_sum từ 7 tọa độ đại diện TP.HCM. "
    "Mỗi tháng: tổng các giá trị trung bình ngày → lượng mưa trung bình tháng (mm/tháng). "
    "Các mô hình dự báo giá trị này cho từng tháng tương lai."
)

PRORATE_THRESHOLD = 0.80

VERBOSE_PHASE1 = False

print("✅ Tất cả thư viện đã được import thành công.")


# ── Quality classification ─────────────────────────────────────
def classify_month(row):
    v, e = row["ValidDays"], row["ExpectedDays"]
    if v == e:
        return "Du"
    elif v >= PRORATE_THRESHOLD * e:
        return "Gan du"
    elif v > 0:
        return "Thieu nhieu"
    else:
        return "Trong hoan toan"


def impute_monthly_rainfall(df_monthly: pd.DataFrame) -> pd.DataFrame:
    df_monthly = df_monthly.copy()

    # Loại tháng cuối nếu chưa đủ dữ liệu
    last_idx = df_monthly.index[-1]
    last_quality = df_monthly.loc[last_idx, "Quality"]
    if last_quality != "Du":
        print(
            f"\n[Loại] Tháng cuối {last_idx.strftime('%m/%Y')} ({last_quality})"
            f" → bị loại khỏi chuỗi."
        )
        df_monthly = df_monthly.iloc[:-1]

    df_monthly["WasImputed"] = False
    df_monthly["ImputeMethod"] = "none"

    good_mask = df_monthly["Quality"] == "Du"
    monthly_median = (
        df_monthly.loc[good_mask]
        .groupby(df_monthly.loc[good_mask].index.month)["Rainfall"]
        .median()
    )

    for idx, row in df_monthly.iterrows():
        q = row["Quality"]
        if q == "Du":
            continue
        if q == "Gan du":
            if row["ValidDays"] > 0:
                df_monthly.loc[idx, "Rainfall"] = (
                    row["Rainfall"] * row["ExpectedDays"] / row["ValidDays"]
                )
            df_monthly.loc[idx, "WasImputed"] = True
            df_monthly.loc[idx, "ImputeMethod"] = "prorate"
        else:
            m = idx.month
            df_monthly.loc[idx, "Rainfall"] = monthly_median.get(m, np.nan)
            df_monthly.loc[idx, "WasImputed"] = True
            df_monthly.loc[idx, "ImputeMethod"] = "monthly_median"

    remaining_nan = df_monthly["Rainfall"].isna().sum()
    if remaining_nan > 0:
        print(f"\n[Cảnh báo] {remaining_nan} tháng vẫn NaN sau impute → nội suy 'time'.")
        df_monthly["Rainfall"] = df_monthly["Rainfall"].interpolate(method="time")

    return df_monthly


# ── Load data ──────────────────────────────────────────────────
if not os.path.exists(OPENMETEO_MONTHLY_PATH):
    raise FileNotFoundError(
        f"Không tìm thấy {OPENMETEO_MONTHLY_PATH}. "
        f"Hãy chạy download_openmeteo_hcmc.py trước."
    )

print(f"📄 Đang đọc dataset: {OPENMETEO_MONTHLY_PATH}")

df = pd.read_csv(OPENMETEO_MONTHLY_PATH, parse_dates=["Date"])
df = df.set_index("Date").sort_index()

if "Rainfall" not in df.columns:
    raise ValueError(f"{OPENMETEO_MONTHLY_PATH} phải có cột Rainfall.")

print("=" * 55)
print(f"TỔNG QUAN BỘ DỮ LIỆU OPEN-METEO — {city_name.upper()}")
print("=" * 55)
print(f"Kích thước        : {df.shape[0]:,} tháng × {df.shape[1]} cột")
print(
    f"Khoảng thời gian  : {df.index.min().strftime('%m/%Y')} → "
    f"{df.index.max().strftime('%m/%Y')}"
)
if VERBOSE_PHASE1:
    print(f"\nKiểu dữ liệu các cột :\n{df.dtypes.to_string()}")
    print(f"\n5 dòng đầu tiên  :\n{df.head().to_string()}")

df_monthly = df.copy()

if "ExpectedDays" not in df_monthly.columns:
    df_monthly["ExpectedDays"] = df_monthly.index.days_in_month
if "RainfallDays" in df_monthly.columns:
    df_monthly["ValidDays"] = df_monthly["RainfallDays"].fillna(0).astype(int)
else:
    df_monthly["ValidDays"] = (
        df_monthly["Rainfall"].notna().astype(int) * df_monthly["ExpectedDays"]
    )

df_monthly["RowDays"] = df_monthly["ValidDays"]
df_monthly["MissingRainValues"] = df_monthly["ExpectedDays"] - df_monthly["ValidDays"]
df_monthly["MissingRows"] = df_monthly["ExpectedDays"] - df_monthly["RowDays"]
df_monthly["Quality"] = df_monthly.apply(classify_month, axis=1)

# Biến khí tượng context
meteo_exclude = {
    "Rainfall", "Precipitation", "RainfallDays", "ExpectedDays", "Completeness",
    "RowDays", "ValidDays", "MissingRainValues", "MissingRows", "Quality",
}
available_meteo_cols = [
    c for c in df_monthly.select_dtypes(include=[np.number]).columns
    if c not in meteo_exclude
]
df_meteo_monthly_context = df_monthly[available_meteo_cols].copy()

# ── Quality report ─────────────────────────────────────────────
print("=" * 60)
print("KIỂM TRA CHẤT LƯỢNG THÁNG")
print("=" * 60)

quality_counts = df_monthly["Quality"].value_counts()
for label in ["Du", "Gan du", "Thieu nhieu", "Trong hoan toan"]:
    cnt = quality_counts.get(label, 0)
    print(f"  {label:<20}: {cnt} tháng")

for label in ["Trong hoan toan", "Thieu nhieu", "Gan du"]:
    subset = df_monthly[df_monthly["Quality"] == label]
    if len(subset) > 0:
        print(f"\nChi tiết — {label} ({len(subset)} tháng):")
        for idx, row in subset.iterrows():
            print(
                f"  {idx.strftime('%m/%Y')}  ValidDays={int(row['ValidDays'])}"
                f"  ExpectedDays={int(row['ExpectedDays'])}"
                f"  NaN={int(row['MissingRainValues'])}"
            )

df_monthly = impute_monthly_rainfall(df_monthly)
df_meteo_monthly_context = df_meteo_monthly_context.reindex(df_monthly.index)

# ── Calendar columns ───────────────────────────────────────────
df_monthly["Year"] = df_monthly.index.year.astype(int)
df_monthly["Month"] = df_monthly.index.month.astype(int)
df_monthly["Quarter"] = df_monthly.index.quarter.astype(int)

# ── Summary ────────────────────────────────────────────────────
n_du = (df_monthly["Quality"] == "Du").sum()
n_gan_du = (df_monthly["Quality"] == "Gan du").sum()
n_thieu_nhieu = (df_monthly["Quality"] == "Thieu nhieu").sum()
n_trong = (df_monthly["Quality"] == "Trong hoan toan").sum()
n_imputed = df_monthly["WasImputed"].sum()
pct_imputed = n_imputed / len(df_monthly) * 100
zero_rain = (df_monthly["Rainfall"] == 0).sum()

print("\n" + "=" * 55)
print("PHASE 1 — BÁO CÁO TÓM TẮT")
print("=" * 55)
print(f"Đề tài                          : {PROJECT_TITLE}")
print(f"Thành phố                       : {city_name}")
print(
    f"Khoảng thời gian                : {df_monthly.index.min().strftime('%m/%Y')} → "
    f"{df_monthly.index.max().strftime('%m/%Y')}"
)
print(f"Tổng số tháng dữ liệu           : {len(df_monthly)} tháng")
print(f"Biến mục tiêu                   : {TARGET_LABEL} ({TARGET_UNIT})")
print(f"Định nghĩa target               : {TARGET_DEFINITION}")
print(f"Lượng mưa tháng thấp nhất       : {df_monthly['Rainfall'].min():.1f} {TARGET_UNIT}")
print(f"Lượng mưa tháng cao nhất        : {df_monthly['Rainfall'].max():.1f} {TARGET_UNIT}")
print(f"Lượng mưa tháng trung bình      : {df_monthly['Rainfall'].mean():.1f} {TARGET_UNIT}")
print(f"Số tháng mưa bằng 0             : {zero_rain} tháng")
print(f"Biến khí tượng bối cảnh         : {len(available_meteo_cols)} biến")
print("-" * 55)
print(f"Số tháng 'Đủ'                   : {n_du}")
print(f"Số tháng 'Gần đủ' (prorate)     : {n_gan_du}")
print(f"Số tháng 'Thiếu nhiều' (median) : {n_thieu_nhieu}")
print(f"Số tháng 'Trống hoàn toàn'      : {n_trong}")
print(f"Tỷ lệ tháng đã impute           : {pct_imputed:.1f}% ({n_imputed}/{len(df_monthly)})")
print("=" * 55)

print("\n✅ Phase 1 hoàn tất — df_monthly đã sẵn sàng.")

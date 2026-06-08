# Phase 2: Phân tích khám phá dữ liệu (EDA)

from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

thang_ngan = ["T1", "T2", "T3", "T4", "T5", "T6",
              "T7", "T8", "T9", "T10", "T11", "T12"]
thang_day  = ["Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4",
              "Tháng 5", "Tháng 6", "Tháng 7", "Tháng 8",
              "Tháng 9", "Tháng 10", "Tháng 11", "Tháng 12"]

target_label = globals().get("TARGET_LABEL", "Lượng mưa trung bình tháng")
target_unit = globals().get("TARGET_UNIT", "mm/tháng")
target_axis_label = f"{target_label} ({target_unit})"
project_title = globals().get(
    "PROJECT_TITLE",
    "Phân tích và Dự báo lượng mưa trung bình của một thành phố dựa trên dữ liệu khí tượng"
)
SHOW_EXTRA_EDA_PLOTS = False


print("=" * 55)
print(f"THỐNG KÊ MÔ TẢ — {target_axis_label}")
print("=" * 55)
print(f"Đề tài: {project_title}")
print(df_monthly["Rainfall"].describe().rename({
    "count": "Số quan sát",
    "mean":  "Trung bình",
    "std":   "Độ lệch chuẩn",
    "min":   "Giá trị nhỏ nhất",
    "25%":   "Phân vị 25%",
    "50%":   "Trung vị (50%)",
    "75%":   "Phân vị 75%",
    "max":   "Giá trị lớn nhất",
}).to_string())

skew_val = df_monthly["Rainfall"].skew()
kurt_val = df_monthly["Rainfall"].kurt()

print(f"\nĐộ lệch (Skewness) : {skew_val:.3f}")
if skew_val > 0.5:
    print("  → Lệch phải: Một vài tháng có lượng mưa cực lớn làm tăng giá trị trung bình.")
elif abs(skew_val) <= 0.5:
    print("  → Phân phối gần đối xứng.")
else:
    print("  → Lệch trái: Một vài tháng khô hạn bất thường kéo giá trị trung bình xuống.")

print(f"\nĐộ nhọn (Kurtosis) : {kurt_val:.3f}")
if kurt_val > 0:
    print("  → Leptokurtic: Đuôi nặng — phân phối có một số tháng mưa lớn bất thường.")
else:
    print("  → Platykurtic: Đuôi nhẹ — ít giá trị ngoại lệ hơn so với phân phối chuẩn.")


meteo_corr = pd.Series(dtype=float)
top_meteo_correlations = pd.Series(dtype=float)

if "df_meteo_monthly_context" in globals() and not df_meteo_monthly_context.empty:
    corr_input = pd.concat(
        [df_monthly["Rainfall"], df_meteo_monthly_context],
        axis=1
    ).dropna()

    if corr_input.shape[1] > 1 and len(corr_input) >= 12:
        meteo_corr = (
            corr_input
            .corr(numeric_only=True)["Rainfall"]
            .drop("Rainfall")
            .dropna()
        )
        meteo_corr = meteo_corr.reindex(
            meteo_corr.abs().sort_values(ascending=False).index
        )
        top_meteo_correlations = meteo_corr.head(8)

        print("\n" + "=" * 55)
        print(f"TƯƠNG QUAN VỚI LƯỢNG MƯA — BIẾN KHÍ TƯỢNG {globals().get('city_name', 'THANH PHO').upper()}")
        print("=" * 55)
        print(top_meteo_correlations.rename("corr").to_string(float_format=lambda x: f"{x:.3f}"))
        print("Ghi chú: tương quan chỉ mô tả quan hệ tuyến tính, không chứng minh nhân quả.")

        fig, ax = plt.subplots(figsize=(10, 4), dpi=100)
        colors = ["#2166ac" if v >= 0 else "#b2182b" for v in top_meteo_correlations.values]
        ax.barh(top_meteo_correlations.index[::-1], top_meteo_correlations.values[::-1],
                color=colors[::-1], edgecolor="white", linewidth=0.8)
        ax.axvline(0, color="black", linewidth=0.9)
        ax.set_title("Tương Quan Biến Khí Tượng Với Lượng Mưa",
                     fontsize=13, fontweight="bold")
        ax.set_xlabel("Hệ số tương quan Pearson", fontsize=11)
        ax.grid(axis="x", alpha=0.3)
        plt.tight_layout()
        plt.show()
else:
    print("\n[Lưu ý] Không có biến khí tượng bổ sung để phân tích tương quan.")


fig, ax = plt.subplots(figsize=(14, 5), dpi=100)

ax.plot(df_monthly.index, df_monthly["Rainfall"],
        color="steelblue", linewidth=1.2, alpha=0.7, label=target_label)

rolling_avg = df_monthly["Rainfall"].rolling(window=12, center=True).mean()
ax.plot(df_monthly.index, rolling_avg,
        color="red", linewidth=2, label="Trung bình động 12 tháng")

peak_date  = df_monthly["Rainfall"].idxmax()
peak_value = df_monthly["Rainfall"].max()
ax.annotate(
    f"Đỉnh: {peak_value:.0f} mm\n{peak_date.strftime('%m/%Y')}",
    xy=(peak_date, peak_value),
    xytext=(peak_date + pd.DateOffset(months=14), peak_value * 0.88),
    arrowprops=dict(arrowstyle="->", color="black"),
    fontsize=9, color="darkred"
)

ax.set_title(f"{target_label} Theo Thời Gian — {city_name}",
             fontsize=14, fontweight="bold")
ax.set_xlabel("Thời gian", fontsize=11)
ax.set_ylabel(target_axis_label, fontsize=11)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()


monthly_stats = df_monthly.groupby("Month")["Rainfall"].agg(["mean", "std"]).reset_index()

norm_values = (monthly_stats["mean"] - monthly_stats["mean"].min()) / \
              (monthly_stats["mean"].max() - monthly_stats["mean"].min())
colors = plt.cm.Blues(0.3 + 0.65 * norm_values)

fig, ax = plt.subplots(figsize=(12, 5), dpi=100)

ax.bar(
    monthly_stats["Month"],
    monthly_stats["mean"],
    yerr=monthly_stats["std"],
    color=colors,
    edgecolor="white",
    linewidth=0.8,
    capsize=4,
    error_kw=dict(elinewidth=1.2, ecolor="gray", capthick=1.2)
)

ax.set_xticks(range(1, 13))
ax.set_xticklabels(thang_ngan, fontsize=10)
ax.set_title("Lượng Mưa Trung Bình Theo Tháng (Quy Luật Mùa Vụ)",
             fontsize=14, fontweight="bold")
ax.set_xlabel("Tháng", fontsize=11)
ax.set_ylabel(target_axis_label, fontsize=11)
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.show()


overall_mean = df_monthly["Rainfall"].mean()

df_monthly["NhanThang"] = df_monthly.index.month.map(
    dict(zip(range(1, 13), thang_ngan))
)
thu_tu_thang = thang_ngan

fig, ax = plt.subplots(figsize=(14, 6), dpi=100)

sns.boxplot(
    data=df_monthly,
    x="NhanThang",
    y="Rainfall",
    order=thu_tu_thang,
    palette="Blues",
    linewidth=1.2,
    flierprops=dict(marker="o", markerfacecolor="steelblue", markersize=4, alpha=0.5),
    ax=ax
)

ax.axhline(overall_mean, color="red", linestyle="--", linewidth=1.5,
           label=f"Trung bình tổng thể ({overall_mean:.2f} {target_unit})")

ax.set_title("Phân Phối Lượng Mưa Theo Tháng (Tất Cả Các Năm)",
             fontsize=14, fontweight="bold")
ax.set_xlabel("Tháng", fontsize=11)
ax.set_ylabel(target_axis_label, fontsize=11)
ax.legend(fontsize=10)
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.show()


df_monthly.drop(columns=["NhanThang"], inplace=True)


if SHOW_EXTRA_EDA_PLOTS:
    heatmap_data = df_monthly.pivot_table(
        index="Year", columns="Month", values="Rainfall", aggfunc="mean"
    )
    heatmap_data.columns = thang_ngan

    fig, ax = plt.subplots(figsize=(14, 7), dpi=100)
    sns.heatmap(
        heatmap_data,
        cmap="YlGnBu",
        annot=True,
        fmt=".0f",
        linewidths=0.4,
        linecolor="white",
        cbar_kws={"label": target_axis_label},
        ax=ax
    )
    ax.set_title(f"Bản Đồ Nhiệt {target_label} — Năm × Tháng",
                 fontsize=14, fontweight="bold")
    ax.set_xlabel("Tháng", fontsize=11)
    ax.set_ylabel("Năm", fontsize=11)
    ax.tick_params(axis="x", rotation=0)
    ax.tick_params(axis="y", rotation=0)
    plt.tight_layout()
    plt.show()


if SHOW_EXTRA_EDA_PLOTS:
    nhan_quy = {1: "Quý 1\n(T1–T3)", 2: "Quý 2\n(T4–T6)",
                3: "Quý 3\n(T7–T9)", 4: "Quý 4\n(T10–T12)"}
    quarterly_avg = df_monthly.groupby("Quarter")["Rainfall"].mean()

    fig, ax = plt.subplots(figsize=(8, 5), dpi=100)
    bar_colors = ["#4393c3", "#2166ac", "#92c5de", "#d1e5f0"]
    bars = ax.bar(
        [nhan_quy[q] for q in quarterly_avg.index],
        quarterly_avg.values,
        color=bar_colors,
        edgecolor="white",
        linewidth=0.8,
        width=0.55
    )
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + 0.8,
            f"{height:.1f} mm",
            ha="center", va="bottom", fontsize=11, fontweight="bold"
        )
    ax.set_title("Lượng Mưa Trung Bình Theo Quý", fontsize=14, fontweight="bold")
    ax.set_xlabel("Quý", fontsize=11)
    ax.set_ylabel(target_axis_label, fontsize=11)
    ax.set_ylim(0, quarterly_avg.max() * 1.18)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.show()


decomposition = seasonal_decompose(df_monthly["Rainfall"], model="additive", period=12)

ten_thanh_phan = [
    (decomposition.observed, "Quan sát thực tế", "steelblue"),
    (decomposition.trend,    "Xu hướng",          "firebrick"),
    (decomposition.seasonal, "Mùa vụ",            "seagreen"),
    (decomposition.resid,    "Phần dư",            "darkorange"),
]

fig, axes = plt.subplots(4, 1, figsize=(14, 10), dpi=100, sharex=True)

for ax, (data, nhan, mau) in zip(axes, ten_thanh_phan):
    ax.plot(data, color=mau, linewidth=1.4)
    ax.set_ylabel(nhan, fontsize=10, fontweight="bold")
    ax.grid(True, alpha=0.25)
    if nhan == "Phần dư":
        ax.axhline(0, color="black", linewidth=0.8, linestyle="--")

axes[0].set_title(
    f"Phân Rã Chuỗi Thời Gian — {city_name} (Mô hình cộng, Chu kỳ=12 tháng)",
    fontsize=13, fontweight="bold"
)
axes[-1].set_xlabel("Thời gian", fontsize=11)
plt.tight_layout()
plt.show()


series_ts = df_monthly["Rainfall"].asfreq("MS").dropna()

print("\n" + "=" * 70)
print("KIỂM ĐỊNH STATIONARITY — ADF & KPSS")
print("=" * 70)

adf_stat, adf_pvalue, *_ = adfuller(series_ts)
try:
    kpss_stat, kpss_pvalue, *_ = kpss(series_ts, regression="c", nlags="auto")
except Exception as _kpss_exc:
    print(f"[KPSS lỗi] {_kpss_exc}")
    kpss_stat, kpss_pvalue = np.nan, np.nan

adf_conclusion = "Chuỗi có tính dừng" if adf_pvalue < 0.05 else "Chuỗi có thể không dừng"
if np.isnan(kpss_pvalue):
    kpss_conclusion = "Không tính được"
elif kpss_pvalue < 0.05:
    kpss_conclusion = "Chuỗi có thể không dừng"
else:
    kpss_conclusion = "Chuỗi có tính dừng"

stationarity_summary_df = pd.DataFrame([
    {
        "Test": "ADF",
        "H0": "Chuỗi không dừng / có unit root",
        "Statistic": adf_stat,
        "p-value": adf_pvalue,
        "Kết luận": adf_conclusion,
    },
    {
        "Test": "KPSS",
        "H0": "Chuỗi dừng quanh mức/trend",
        "Statistic": kpss_stat,
        "p-value": kpss_pvalue,
        "Kết luận": kpss_conclusion,
    },
])

print(stationarity_summary_df.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
if adf_conclusion != kpss_conclusion and not np.isnan(kpss_pvalue):
    print("\nGiải thích: ADF và KPSS cho kết luận khác nhau. Với chuỗi lượng mưa có mùa vụ mạnh,")
    print("cần xem thêm decomposition, ACF/PACF và có thể cân nhắc differencing/mùa vụ trong mô hình.")

fig, axes = plt.subplots(1, 2, figsize=(14, 4), dpi=100)
plot_acf(series_ts, lags=48, ax=axes[0])
plot_pacf(series_ts, lags=48, ax=axes[1], method="ywm")
axes[0].set_title("ACF — Rainfall (48 lags)", fontsize=12, fontweight="bold")
axes[1].set_title("PACF — Rainfall (48 lags)", fontsize=12, fontweight="bold")
plt.tight_layout()
plt.show()

seasonal_plot_data = df_monthly.pivot_table(
    index="Month", columns="Year", values="Rainfall", aggfunc="mean"
)
years_for_seasonal_plot = list(seasonal_plot_data.columns[-15:])

fig, ax = plt.subplots(figsize=(13, 5), dpi=100)
for year in years_for_seasonal_plot:
    ax.plot(seasonal_plot_data.index, seasonal_plot_data[year],
            linewidth=1.2, alpha=0.75, label=str(year))
ax.plot(seasonal_plot_data[years_for_seasonal_plot].mean(axis=1),
        color="black", linewidth=2.5, linestyle="--", label="TB 15 năm gần nhất")
ax.set_xticks(range(1, 13))
ax.set_xticklabels(thang_ngan)
ax.set_title("Seasonal Plot — Lượng Mưa Theo Tháng Qua Các Năm Gần Đây",
             fontsize=13, fontweight="bold")
ax.set_xlabel("Tháng")
ax.set_ylabel(target_axis_label)
ax.grid(True, alpha=0.25)
ax.legend(fontsize=8, ncol=4)
plt.tight_layout()
plt.show()


month_avg       = df_monthly.groupby("Month")["Rainfall"].mean()
thang_mua_nhat  = month_avg.idxmax()
thang_kho_nhat  = month_avg.idxmin()

resid_dropna    = decomposition.resid.dropna()
seas_aligned    = decomposition.seasonal.loc[resid_dropna.index]
season_strength = max(0.0, 1.0 - resid_dropna.var() / (seas_aligned + resid_dropna).var())

if season_strength > 0.6:
    muc_mua_vu = "Mạnh"
elif season_strength > 0.35:
    muc_mua_vu = "Trung bình"
else:
    muc_mua_vu = "Yếu"

print("\n" + "=" * 55)
print("PHASE 2 — TÓM TẮT NHẬN XÉT EDA")
print("=" * 55)
print(f"Tháng có lượng mưa TB cao nhất : {thang_day[thang_mua_nhat - 1]} "
      f"({month_avg[thang_mua_nhat]:.2f} {target_unit})")
print(f"Tháng có lượng mưa TB thấp nhất: {thang_day[thang_kho_nhat - 1]} "
      f"({month_avg[thang_kho_nhat]:.2f} {target_unit})")
print(f"Độ mạnh mùa vụ                 : {muc_mua_vu} ({season_strength:.2f}) "
      f"— công thức Hyndman")
if len(top_meteo_correlations) > 0:
    bien_khi_tuong_top = top_meteo_correlations.index[0]
    corr_top = top_meteo_correlations.iloc[0]
    print(f"Biến khí tượng liên hệ mạnh nhất: {bien_khi_tuong_top} "
          f"(corr={corr_top:.2f}, chỉ mang tính mô tả)")
print("=" * 55)


if SHOW_EXTRA_EDA_PLOTS:
    yoy_pivot = df_monthly.pivot_table(
        index="Month", columns="Year", values="Rainfall", aggfunc="mean"
    )
    yearly_count = df_monthly.groupby("Year").size()
    nam_day_du = yearly_count[yearly_count == 12].index
    years_to_plot = [y for y in yoy_pivot.columns if y in nam_day_du]

    cmap = plt.cm.get_cmap("tab20", len(years_to_plot))
    fig, ax = plt.subplots(figsize=(13, 5), dpi=100)
    for i, yr in enumerate(years_to_plot):
        ax.plot(yoy_pivot.index, yoy_pivot[yr],
                color=cmap(i), linewidth=1.4, alpha=0.8, label=str(yr))
    ax.plot(yoy_pivot[years_to_plot].mean(axis=1),
            color="black", linewidth=2.5, linestyle="--", label="Trung bình nhiều năm")
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(thang_ngan, fontsize=10)
    ax.set_title("Year-on-Year: Lượng Mưa Từng Tháng Qua Các Năm",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("Tháng", fontsize=11)
    ax.set_ylabel(target_axis_label, fontsize=11)
    ax.legend(loc="upper right", fontsize=7.5, ncol=3, title="Năm")
    ax.grid(True, alpha=0.25)
    plt.tight_layout()
    plt.show()


seasonality_is_reliable = (season_strength > 0.30)

if seasonality_is_reliable:
    print("\n✅ Mùa vụ đủ tin cậy cho mô hình "
          f"(season_strength = {season_strength:.3f} > 0.30)")
else:
    print("\n⚠️  Mùa vụ YẾU — kỳ vọng Phase 3 SARIMA/HW khó vượt baseline "
          f"(season_strength = {season_strength:.3f} ≤ 0.30)")

print("\n" + "=" * 60)
print("KẾT LUẬN PHASE 2")
print("=" * 60)
print("Mùa mưa TP.HCM: T5–T11; mùa khô: T12–T4; đỉnh mưa trung bình vào tháng 9.")
print(f"Season strength = {season_strength:.3f} -> mùa vụ mạnh.")
print(f"ADF: {adf_conclusion}; KPSS: {kpss_conclusion}.")
print("Các biến khí tượng tương quan mạnh với Rainfall chỉ dùng để phân tích/giải thích,")
print("không chứng minh nhân quả và không được dùng như dữ liệu tương lai thật khi forecast.")
print("=" * 60)

print("\n✅ Phase 2 hoàn tất — EDA đã xong.")

print("=" * 70)
print("PHASE 8 — BÁO CÁO KẾT LUẬN")
print("=" * 70)

dataset_start = df_monthly.index.min().strftime("%m/%Y")
dataset_end = df_monthly.index.max().strftime("%m/%Y")
n_months = len(df_monthly)
n_context_features = len(globals().get("available_meteo_cols", []))

month_avg_report = df_monthly.groupby("Month")["Rainfall"].mean()
overall_month_mean = float(df_monthly["Rainfall"].mean())
peak_month = int(month_avg_report.idxmax())
low_month = int(month_avg_report.idxmin())
peak_value = float(month_avg_report.loc[peak_month])
low_value = float(month_avg_report.loc[low_month])


def month_name(month_num):
    names = globals().get("thang_day")
    if names and 1 <= month_num <= len(names):
        return names[month_num - 1]
    return f"Tháng {month_num}"


def month_list(months):
    return ", ".join(f"T{int(m)}" for m in months)


above_mean_months = month_avg_report[month_avg_report > overall_month_mean].index.tolist()
below_mean_months = month_avg_report[month_avg_report <= overall_month_mean].index.tolist()

season_strength_value = globals().get("season_strength", float("nan"))
if not np.isnan(season_strength_value):
    if season_strength_value >= 0.6:
        season_text = "mạnh"
    elif season_strength_value >= 0.35:
        season_text = "vừa"
    else:
        season_text = "yếu"
else:
    season_text = "chưa tính"

trend_text = "Không đủ kết quả ADF/KPSS để nhận xét xu hướng."
if "adf_pvalue" in globals() and "kpss_pvalue" in globals():
    if adf_pvalue < 0.05 and kpss_pvalue >= 0.05:
        trend_text = (
            "ADF và KPSS cùng ủng hộ nhận xét: chuỗi mưa chủ yếu dao động theo mùa; "
            "chưa thấy xu hướng tăng hoặc giảm đều trong toàn kỳ dữ liệu."
        )
    elif adf_pvalue < 0.05:
        trend_text = "ADF cho tín hiệu chuỗi khá ổn định, nhưng KPSS chưa đồng thuận rõ."
    elif kpss_pvalue >= 0.05:
        trend_text = "KPSS cho tín hiệu chuỗi khá ổn định, nhưng ADF chưa đồng thuận rõ."
    else:
        trend_text = "ADF và KPSS chưa đủ đồng thuận để nhận xét chuỗi ổn định."

cv_mean = globals().get("_cv_mean", {})
cv_rmse = cv_mean.get(forecast_model_name, float("nan"))
holdout_rmse = (
    metrics_df.loc[forecast_model_name, "RMSE"]
    if "metrics_df" in globals() and forecast_model_name in metrics_df.index
    else float("nan")
)
holdout_wape = (
    metrics_df.loc[forecast_model_name, "WAPE (%)"]
    if "metrics_df" in globals() and forecast_model_name in metrics_df.index
    else float("nan")
)

top_corr_names = []
if "top_meteo_correlations" in globals() and len(top_meteo_correlations) > 0:
    top_corr_names = top_meteo_correlations.head(6).index.tolist()

print("\n1. TỔNG QUAN DỮ LIỆU")
print("-" * 70)
print(f"Đề tài                 : {PROJECT_TITLE}")
print("Nguồn dữ liệu          : Open-Meteo Historical Weather API (ERA5 reanalysis)")
print("Phương pháp không gian : Trung bình 7 tọa độ đại diện TP.HCM")
print(f"Thành phố              : {city_name}")
print(f"Thời gian              : {dataset_start} → {dataset_end}")
print(f"Số quan sát            : {n_months} tháng")
print(f"Biến mục tiêu          : {TARGET_LABEL} ({TARGET_UNIT})")
print(f"Số biến khí tượng/context trong phân tích: {n_context_features}")

print("\n2. NHỮNG GÌ SỐ LIỆU CHO THẤY")
print("-" * 70)
print(f"Lượng mưa TB toàn kỳ   : {overall_month_mean:.2f} {target_unit}")
print(f"Tháng TB cao nhất      : {month_name(peak_month)} ({peak_value:.2f} {target_unit})")
print(f"Tháng TB thấp nhất     : {month_name(low_month)} ({low_value:.2f} {target_unit})")
print(f"Tháng cao hơn TB chung : {month_list(above_mean_months)}")
print(f"Tháng thấp/bằng TB chung: {month_list(below_mean_months)}")
if not np.isnan(season_strength_value):
    print(f"Độ mạnh mùa vụ         : {season_strength_value:.3f} → {season_text}")
print(trend_text)

print("\n3. BIẾN THỜI TIẾT ĐI CÙNG MƯA")
print("-" * 70)
if top_corr_names:
    print(f"Top biến tương quan với Rainfall: {', '.join(top_corr_names)}")
print("Tương quan chỉ nói các biến đi cùng nhau, không chứng minh nguyên nhân.")
print("Khi dự báo, code chỉ dùng dữ liệu quá khứ/rolling để tránh nhìn trước tương lai.")

print("\n4. SO SÁNH MÔ HÌNH")
print("-" * 70)
if "metrics_df" in globals():
    print(metrics_df.to_string())
if cv_mean:
    print("\nCV-RMSE trung bình qua nhiều cửa sổ:")
    for name, value in sorted(cv_mean.items(), key=lambda item: item[1]):
        print(f"  {name:<20}: {value:.2f} {target_unit}")

print("\n5. MÔ HÌNH ĐƯỢC CHỌN")
print("-" * 70)
print(f"Mô hình được chọn      : {forecast_model_name}")
if not np.isnan(holdout_rmse):
    print(f"Hold-out RMSE          : {holdout_rmse:.2f} {target_unit}")
if not np.isnan(holdout_wape):
    print(f"Hold-out WAPE          : {holdout_wape:.2f}%")
if not np.isnan(cv_rmse):
    print(f"CV-RMSE trung bình     : {cv_rmse:.2f} {target_unit}")
if "best_accuracy_model" in globals():
    print(f"Mô hình tốt nhất trên hold-out: {best_accuracy_model}")
print("Cách hiểu              : đây là mô hình tốt nhất trong 4 mô hình đã thử, không phải bảo đảm đúng tuyệt đối.")

print("\n6. DỰ BÁO")
print("-" * 70)
if "future_index" in globals() and "future_forecast" in globals():
    print(f"Giai đoạn dự báo       : {future_index[0]:%m/%Y} → {future_index[-1]:%m/%Y}")
    if "forecast_period_sum" in globals():
        print(f"Tổng mưa dự báo        : {forecast_period_sum:.1f} mm")
    forecast_peak = future_forecast.idxmax()
    forecast_low = future_forecast.idxmin()
    print(
        f"Tháng dự báo cao nhất  : {forecast_peak:%m/%Y} "
        f"({future_forecast.loc[forecast_peak]:.2f} {target_unit})"
    )
    print(
        f"Tháng dự báo thấp nhất : {forecast_low:%m/%Y} "
        f"({future_forecast.loc[forecast_low]:.2f} {target_unit})"
    )

print("\n7. HẠN CHẾ")
print("-" * 70)
print("- ERA5 là dữ liệu tái phân tích, có thể khác số đo trạm thực địa.")
print("- Dự báo 12 tháng dùng proxy/climatology cho thời tiết tương lai, không có số thời tiết tương lai thật.")
print("- Sai số theo tháng còn lớn, nhất là mùa mưa.")
print("- Trung bình 7 tọa độ chỉ là đại diện toàn thành phố ở mức xấp xỉ.")

print("\n8. HƯỚNG PHÁT TRIỂN")
print("-" * 70)
print("- Thêm ENSO/ONI/Nino3.4, SST, MJO rồi kiểm tra xem sai số có giảm không.")
print("- Nếu có dự báo thời tiết tháng tới thật, đưa vào làm biến hỗ trợ và đánh giá lại.")
print("- Kiểm tra khoảng dự báo thấp/cao trên dữ liệu quá khứ để biết khoảng đó có đáng tin không.")
print("- Chỉ thử Deep Learning khi có thêm dữ liệu hoặc có mục tiêu so sánh rõ ràng.")

print("=" * 70)
print("✅ Phase 8 hoàn tất — kết luận đã bám theo số liệu đang chạy.")
print("=" * 70)

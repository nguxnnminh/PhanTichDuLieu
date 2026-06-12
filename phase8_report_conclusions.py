print("=" * 70)
print("PHASE 9 — BÁO CÁO KẾT LUẬN")
print("=" * 70)

dataset_start = df_monthly.index.min().strftime("%m/%Y")
dataset_end = df_monthly.index.max().strftime("%m/%Y")
n_months = len(df_monthly)
n_weather_features = len(globals().get("available_meteo_cols", []))

cv_mean = globals().get("_cv_mean", {})
cv_rmse = cv_mean.get(forecast_model_name, float("nan"))
holdout_rmse = (
    metrics_df.loc[forecast_model_name, "RMSE"]
    if forecast_model_name in metrics_df.index
    else float("nan")
)

top_corr_names = []
if "top_meteo_correlations" in globals() and len(top_meteo_correlations) > 0:
    top_corr_names = top_meteo_correlations.head(6).index.tolist()

print("\n1. TỔNG QUAN DỮ LIỆU")
print("-" * 70)
print(f"Đề tài              : {PROJECT_TITLE}")
print(f"Nguồn dữ liệu       : Open-Meteo Historical Weather API (ERA5 reanalysis)")
print(f"Phương pháp không gian: Trung bình 7 tọa độ đại diện TP.HCM")
print(f"Thành phố            : {city_name}")
print(f"Thời gian            : {dataset_start} → {dataset_end}")
print(f"Số quan sát          : {n_months} tháng")
print(f"Biến mục tiêu        : {TARGET_LABEL} ({TARGET_UNIT})")
print(f"Số biến khí tượng    : {n_weather_features}")

print("\n2. ĐẶC ĐIỂM CHUỖI THỜI GIAN")
print("-" * 70)
print("TP.HCM có mùa mưa rõ rệt từ T5–T11 và mùa khô từ T12–T4.")
print("Đỉnh mưa tập trung quanh tháng 9; phù hợp khí hậu nhiệt đới gió mùa.")
if "season_strength" in globals():
    print(f"Season strength     : {season_strength:.3f} → mùa vụ mạnh.")
print("ADF/KPSS/ACF/PACF được dùng để kiểm tra stationarity và autocorrelation.")

print("\n3. PHÂN TÍCH BIẾN KHÍ TƯỢNG")
print("-" * 70)
if top_corr_names:
    print(f"Biến tương quan mạnh với Rainfall: {', '.join(top_corr_names)}")
print("Các biến khí tượng chỉ dùng dạng lag/rolling quá khứ trong forecast.")
print("Không dùng giá trị cùng tháng để tránh data leakage.")

print("\n4. SO SÁNH MÔ HÌNH")
print("-" * 70)
if "metrics_df" in globals():
    print(metrics_df.to_string())
print("\nRolling-Origin CV được ưu tiên hơn hold-out đơn lẻ.")

print("\n5. LỰA CHỌN MÔ HÌNH")
print("-" * 70)
print(f"Mô hình được chọn    : {forecast_model_name}")
if not np.isnan(cv_rmse):
    print(f"CV-RMSE              : {cv_rmse:.2f} {target_unit}")
if not np.isnan(holdout_rmse):
    print(f"Hold-out RMSE        : {holdout_rmse:.2f} {target_unit}")
if "best_accuracy_model" in globals() and best_accuracy_model != forecast_model_name:
    print(f"Best hold-out model  : {best_accuracy_model}")
    print("Lý do không chọn    : hold-out chỉ là một cửa sổ; ưu tiên CV-RMSE.")

print("\n6. DỰ BÁO")
print("-" * 70)
if "future_index" in globals() and "future_forecast" in globals():
    print(f"Giai đoạn forecast   : {future_index[0]:%m/%Y} → {future_index[-1]:%m/%Y}")
    if "forecast_period_sum" in globals():
        print(f"Tổng mưa dự báo      : {forecast_period_sum:.1f} mm")
    thang_mua = future_forecast.idxmax()
    thang_kho = future_forecast.idxmin()
    print(
        f"Tháng mưa nhiều nhất : {thang_mua:%m/%Y} "
        f"({future_forecast.loc[thang_mua]:.2f} {target_unit})"
    )
    print(
        f"Tháng mưa ít nhất    : {thang_kho:%m/%Y} "
        f"({future_forecast.loc[thang_kho]:.2f} {target_unit})"
    )

print("\n7. HẠN CHẾ")
print("-" * 70)
print("- Open-Meteo là dữ liệu tái phân tích (ERA5), có thể khác số liệu trạm thực địa.")
print("- Không dùng dữ liệu khí tượng tương lai thật; các model weather dùng proxy/climatology.")
print("- Sai số dự báo mùa tháng vẫn cao do mưa chịu ảnh hưởng nhiều hiện tượng khí hậu.")
print("- Trung bình 7 tọa độ là xấp xỉ, không thay thế được mạng lưới đo thực địa dày đặc.")

print("\n8. HƯỚNG PHÁT TRIỂN")
print("-" * 70)
print("- Thêm ENSO/ONI/Nino3.4, SST, MJO để có tín hiệu khí hậu dự báo trước.")
print("- Nếu có dữ liệu dự báo khí tượng tháng tới thật, có thể dùng làm exogenous hợp lệ.")
print("- Kiểm định thêm prediction interval coverage trên rolling-origin CV.")
print("- Thử nghiệm Deep Learning (LSTM, Temporal Fusion Transformer) nếu có đủ dữ liệu.")

print("=" * 70)
print("✅ Phase 9 hoàn tất — kết luận sẵn sàng đưa vào report/slide.")
print("=" * 70)

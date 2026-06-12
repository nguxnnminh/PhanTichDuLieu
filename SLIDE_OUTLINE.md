# Khung slide: Phân tích và dự báo lượng mưa TP.HCM

Khung này rút còn **12 slide**, bám đúng số liệu log chạy `python run_all_phases.py`.

---

## Slide 1 — Mục tiêu và dữ liệu

- Đề tài: phân tích và dự báo lượng mưa trung bình tháng tại TP.HCM.
- Nguồn: Open-Meteo ERA5 reanalysis.
- Thời gian dữ liệu: **01/1979 → 05/2026**.
- Mục tiêu:
  - kiểm tra dữ liệu mưa tháng,
  - xem quy luật mưa theo mùa,
  - so sánh 4 mô hình dự báo,
  - dự báo 12 tháng tiếp theo.

Lời nói: dữ liệu đại diện cho TP.HCM bằng cách trung bình 7 tọa độ, không phải số đo riêng của một trạm.

---

## Slide 2 — Chất lượng và quy mô dữ liệu

Số liệu từ Phase 1:

| Mục | Giá trị |
|---|---:|
| Số tháng | 569 |
| Số cột số liệu sau khi dùng `Date` làm index | 26 |
| Khoảng thời gian | 01/1979 → 05/2026 |
| Tháng đủ dữ liệu | 569 |
| Tháng phải impute | 0 |
| Lượng mưa trung bình | 162.3 mm/tháng |
| Lượng mưa thấp nhất / cao nhất | 0.0 / 473.5 mm/tháng |
| Số tháng mưa bằng 0 | 2 |
| Biến khí tượng/context | 21 |

Lời nói: dữ liệu tháng đủ, không phải bù mưa bằng nội suy, prorate hay median.

---

## Slide 3 — Các cột và biến quan trọng

| Nhóm cột | Ví dụ | Vai trò |
|---|---|---|
| Thời gian | `Date` | Làm index, nhóm theo tháng, chia train/test |
| Mục tiêu | `Rainfall` | Cột cần phân tích và dự báo |
| Mưa/nước | `PrecipitationHours`, `Evapotranspiration` | Phân tích tương quan, tạo feature quá khứ |
| Nhiệt độ | `TempMean`, `TempMin`, `TempMax` | Tạo feature lag/rolling |
| Độ ẩm/điểm sương | `HumidityMean`, `DewPointMean` | Đi cùng mưa khá rõ, dùng trong mô hình |
| Mây | `CloudCoverMean`, `CloudCoverHighMean` | Đi cùng mưa khá rõ, dùng trong mô hình |
| Áp suất | `SurfacePressureMean`, `PressureMSLMean` | Biến bối cảnh thời tiết |
| Chất lượng | `RainfallDays`, `ExpectedDays`, `Completeness` | Chỉ kiểm tra dữ liệu, không dùng dự báo |

Lưu ý:

- Phân tích tương quan được dùng biến cùng tháng.
- Dự báo chỉ dùng dữ liệu quá khứ, không dùng thời tiết của tháng tương lai.
- Phase 1 có 21 context = 20 biến thời tiết chính + `ValidHourlyRows`.

---

## Slide 4 — Thống kê, mùa vụ và kiểm định chuỗi

Số liệu từ Phase 2:

| Chỉ số | Giá trị |
|---|---:|
| Trung bình | 162.315 mm/tháng |
| Độ lệch chuẩn | 127.319 |
| Trung vị | 168.557 |
| Nhỏ nhất / lớn nhất | 0.000 / 473.529 |
| Skewness | 0.206 |
| Kurtosis | -1.233 |
| Tháng mưa TB cao nhất | Tháng 9, 325.77 |
| Tháng mưa TB thấp nhất | Tháng 2, 12.30 |
| Độ mạnh mùa vụ | 0.85 |

Kiểm định chuỗi:

| Test | Statistic | p-value | Kết luận log |
|---|---:|---:|---|
| ADF | -4.6186 | 0.0001 | Chuỗi có tính dừng |
| KPSS | 0.2042 | 0.1000 | Chuỗi có tính dừng |

Lời nói: mưa thay đổi mạnh theo tháng trong năm. Hai kiểm định không cho thấy xu hướng tăng/giảm một chiều rõ trong toàn kỳ.

Hình gợi ý: `output_fig_02.png`, `output_fig_03.png`, `output_fig_06.png`.

---

## Slide 5 — Biến thời tiết đi cùng mưa

Tương quan cùng tháng từ Phase 2:

| Biến | Tương quan |
|---|---:|
| PrecipitationHours | 0.970 |
| HumidityMean | 0.886 |
| CloudCoverHighMean | 0.842 |
| CloudCoverMean | 0.839 |
| DewPointMean | 0.824 |
| CloudCoverMidMean | 0.739 |
| CloudCoverLowMean | 0.722 |
| SurfacePressureMean | -0.721 |

Lời nói: đây là quan hệ đi cùng nhau, không phải bằng chứng nguyên nhân. Khi dự báo, các biến này chỉ được dùng dưới dạng quá khứ/rolling.

Hình gợi ý: `output_fig_01.png`.

---

## Slide 6 — Tạo feature cho mô hình

Số liệu từ Phase 3:

| Nhóm feature | Số cột | Cách hiểu |
|---|---:|---|
| time | 4 | tháng, quý, sin/cos của tháng |
| fourier | 6 | sóng mùa vụ chu kỳ 12 tháng |
| rainfall_lag | 7 | mưa 1,2,3,6,12,24,36 tháng trước |
| rainfall_rolling | 8 | trung bình/std mưa 3,6,12,24 tháng trước |
| weather_lag | 40 | 20 biến thời tiết lag 1 và lag 3 |
| weather_rolling | 40 | 20 biến thời tiết rolling 3 và 12 |
| Tổng | 105 | `X_ml` sau xử lý |

Sau tạo feature:

- `X_ml`: **533 dòng × 105 cột**.
- Thời gian còn lại: **01/1982 → 05/2026**.

Lời nói: mất các tháng đầu vì cần dữ liệu quá khứ để tạo lag/rolling. Feature dự báo không nhìn vào tháng tương lai.

---

## Slide 7 — Chia dữ liệu và 4 mô hình

Số liệu từ Phase 4:

| Tập | Thời gian | Số tháng |
|---|---|---:|
| Train | 01/1979 → 05/2024 | 545 |
| Test | 06/2024 → 05/2026 | 24 |

4 mô hình:

| Mô hình | Cách hiểu |
|---|---|
| Seasonal Naive | Copy lượng mưa cùng tháng năm trước |
| SARIMAX | Chuỗi thời gian có mùa vụ, dùng thêm 6 biến lag-1 |
| Prophet | Mô hình chuỗi thời gian có mùa vụ |
| XGBoost | Mô hình cây, dùng 103 features khi dự báo |

SARIMAX được auto_arima chọn: `SARIMAX(3, 0, 0)x(1, 0, 1, 12)`.

Hình gợi ý: `output_fig_08.png`.

---

## Slide 8 — Kết quả đánh giá mô hình

Hold-out 24 tháng:

| Mô hình | MAE | RMSE | WAPE (%) | MASE |
|---|---:|---:|---:|---:|
| SARIMAX | 52.64 | 59.47 | 25.53 | 0.9756 |
| Prophet | 55.48 | 66.69 | 26.91 | 1.0281 |
| Seasonal Naive | 57.58 | 66.96 | 27.93 | 1.0672 |
| XGBoost | 64.15 | 76.89 | 31.11 | 1.1888 |

Rolling-origin CV:

| Mô hình | CV-RMSE TB | CV_std |
|---|---:|---:|
| SARIMAX | 68.23 | 14.17 |
| Prophet | 72.76 | 17.03 |
| XGBoost | 76.70 | 19.37 |
| Seasonal Naive | 84.60 | 20.24 |

Lời nói: SARIMAX có sai số thấp nhất trên cả hold-out và rolling CV, nên được chọn để dự báo.

Hình gợi ý: `output_fig_09.png`, `output_fig_10.png`.

---

## Slide 9 — Sai số theo mùa và kiểm tra phần dư

Sai số theo mùa từ Phase 5:

| Mô hình | RMSE mưa | WAPE mưa | RMSE khô | WAPE khô |
|---|---:|---:|---:|---:|
| SARIMAX | 69.5 | 19.8 | 41.5 | 71.8 |
| Prophet | 79.6 | 22.1 | 42.4 | 65.5 |
| Seasonal Naive | 74.2 | 21.0 | 55.2 | 83.5 |
| XGBoost | 91.9 | 26.0 | 48.5 | 71.7 |

Kiểm tra phần dư từ Phase 6:

| Mô hình | Mean residual | Std residual | p-value nhỏ nhất |
|---|---:|---:|---:|
| Seasonal Naive | 7.554 | 67.959 | 0.2950 |
| SARIMAX | 15.366 | 58.690 | 0.6479 |
| Prophet | 16.739 | 65.947 | 0.3671 |
| XGBoost | 37.384 | 68.635 | 0.4797 |

Lời nói: WAPE mùa khô cao vì lượng mưa thật nhỏ. Ljung-Box p-value đều > 0.05, nên chưa phát hiện tự tương quan đáng kể trong phần dư.

Hình gợi ý: `output_fig_11.png`.

---

## Slide 10 — Dự báo SARIMAX 12 tháng

Số liệu từ Phase 7:

| Tháng | Dự báo | Cận dưới | Cận trên |
|---|---:|---:|---:|
| 06/2026 | 248.19 | 97.45 | 398.92 |
| 07/2026 | 270.87 | 120.14 | 421.60 |
| 08/2026 | 280.36 | 129.63 | 431.10 |
| 09/2026 | 327.48 | 176.75 | 478.21 |
| 10/2026 | 279.49 | 128.76 | 430.22 |
| 11/2026 | 141.90 | 0.00 | 292.63 |
| 12/2026 | 56.33 | 0.00 | 207.06 |
| 01/2027 | 20.83 | 0.00 | 171.56 |
| 02/2027 | 13.53 | 0.00 | 164.26 |
| 03/2027 | 26.00 | 0.00 | 176.73 |
| 04/2027 | 78.04 | 0.00 | 228.78 |
| 05/2027 | 212.31 | 61.58 | 363.04 |

Tóm tắt:

- Tổng 12 tháng: **1955.3 mm**.
- Cao nhất: **09/2026**, **327.48 mm**.
- Thấp nhất: **02/2027**, **13.53 mm**.
- Cận dưới/cận trên là khoảng tham khảo từ sai số cũ, không phải cam kết chắc chắn.

Hình gợi ý: `output_fig_12.png`.

---

## Slide 11 — So sánh dự báo 4 mô hình

| Tháng | Seasonal Naive | SARIMAX | Prophet | XGBoost |
|---|---:|---:|---:|---:|
| 06/2026 | 348.8 | 248.2 | 292.0 | 273.2 |
| 07/2026 | 326.0 | 270.9 | 316.9 | 260.2 |
| 08/2026 | 426.8 | 280.4 | 322.6 | 307.7 |
| 09/2026 | 473.5 | 327.5 | 362.8 | 307.7 |
| 10/2026 | 301.5 | 279.5 | 311.0 | 267.9 |
| 11/2026 | 227.6 | 141.9 | 179.5 | 100.7 |
| 12/2026 | 122.0 | 56.3 | 90.6 | 41.8 |
| 01/2027 | 28.2 | 20.8 | 59.7 | 11.1 |
| 02/2027 | 58.6 | 13.5 | 51.4 | 11.6 |
| 03/2027 | 30.3 | 26.0 | 71.3 | 13.8 |
| 04/2027 | 7.7 | 78.0 | 112.9 | 56.0 |
| 05/2027 | 134.6 | 212.3 | 232.7 | 234.3 |

Lời nói: các mô hình cùng cho mùa mưa cao hơn mùa khô, nhưng mức từng tháng khác nhau. SARIMAX được chọn vì sai số kiểm tra trước đó thấp nhất.

Hình gợi ý: `output_fig_13.png`.

---

## Slide 12 — Hạn chế, hướng phát triển và kết luận

Hạn chế:

- ERA5 không phải số đo trực tiếp từ trạm mưa địa phương.
- Dự báo 12 tháng dùng proxy/climatology cho thời tiết tương lai.
- Sai số theo tháng còn lớn, nhất là mùa mưa.
- 7 tọa độ chỉ đại diện xấp xỉ cho toàn TP.HCM.
- Tương quan không chứng minh nguyên nhân.

Hướng phát triển:

- Thêm ENSO/ONI/Nino3.4, SST, MJO rồi kiểm tra sai số có giảm không.
- Nếu có dự báo thời tiết thật, đưa vào làm biến hỗ trợ và đánh giá lại.
- Kiểm tra độ tin cậy của cận dưới/cận trên trên dữ liệu quá khứ.
- Thử Deep Learning chỉ khi có thêm dữ liệu hoặc có mục tiêu so sánh rõ.

Kết luận ngắn:

- Dữ liệu tháng đầy đủ, không phải impute.
- Lượng mưa có mùa vụ mạnh, season strength **0.85**.
- SARIMAX có sai số thấp nhất trong 4 mô hình đã thử.
- Dự báo 06/2026 → 05/2027: tổng **1955.3 mm**, cao nhất **09/2026**, thấp nhất **02/2027**.
- Kết quả phù hợp để tham khảo theo mùa; muốn dùng thực tế cần kiểm tra thêm với dữ liệu trạm và biến khí hậu lớn.

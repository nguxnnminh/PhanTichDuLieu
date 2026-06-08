# Phân Tích và Dự Báo Lượng Mưa TP.HCM

Dự án phân tích chuỗi thời gian lượng mưa tháng tại **Thành phố Hồ Chí Minh** (1979–2026) sử dụng dữ liệu Open-Meteo, xây dựng pipeline đầy đủ từ tiền xử lý đến dự báo 12 tháng tương lai.

---

## Mục tiêu

- Phân tích đặc trưng mùa vụ và tính dừng của chuỗi lượng mưa tháng tại TP.HCM
- Xây dựng và so sánh 3 nhóm mô hình: Baseline, Statistical, Machine Learning
- Đánh giá mô hình bằng Rolling-Origin Cross-Validation (tin cậy hơn hold-out đơn lẻ)
- Dự báo lượng mưa 12 tháng tiếp theo (06/2026 – 05/2027)

---

## Dữ liệu

| Thuộc tính | Giá trị |
|---|---|
| Nguồn | [Open-Meteo Historical Weather API](https://open-meteo.com/) |
| Thành phố | Ho Chi Minh City |
| Khoảng thời gian | 01/1979 – 05/2026 |
| Số quan sát | 569 tháng |
| Biến mục tiêu | `Rainfall` — lượng mưa trung bình tháng (mm/tháng) |
| Biến khí tượng | 21 biến (nhiệt độ, độ ẩm, áp suất, mây, gió, bức xạ, ...) |

> **Lưu ý:** Open-Meteo là dữ liệu tái phân tích lịch sử (reanalysis), không phải đo trực tiếp tại trạm khí tượng.

### Thống kê mô tả lượng mưa

| Chỉ số | Giá trị |
|---|---|
| Trung bình | 159.2 mm/tháng |
| Trung vị | 166.7 mm/tháng |
| Độ lệch chuẩn | 124.3 mm/tháng |
| Nhỏ nhất | 0.0 mm/tháng |
| Lớn nhất | 451.0 mm/tháng |
| Độ mạnh mùa vụ | 0.852 (mạnh) |

---

## Cấu trúc dự án

```
PhanTichDuLieu/
├── run_all_phases.py               # Runner: chạy toàn bộ pipeline Phase 1–9
├── download_openmeteo_hcmc.py      # Script tải dữ liệu từ Open-Meteo API
│
├── hcmc_openmeteo_daily.csv        # Dữ liệu ngày gốc
├── hcmc_openmeteo_hourly.csv       # Dữ liệu giờ gốc
├── hcmc_openmeteo_monthly.csv      # Dữ liệu đã resample theo tháng
│
├── phase1_rainfall_preprocessing.py   # Tiền xử lý & kiểm tra chất lượng
├── phase2_eda.py                      # Phân tích khám phá dữ liệu (EDA)
├── phase3_feature_engineering.py      # Tạo features cho ML
├── phase4_modeling.py                 # Xây dựng mô hình
├── phase5_feature_selection.py        # Chọn feature & feature importance
├── phase6_evaluation.py               # Đánh giá & Rolling-Origin CV
├── phase7_residual_diagnostics.py     # Kiểm tra phần dư
├── phase8_forecast.py                 # Dự báo 12 tháng tương lai
├── phase9_report_conclusions.py       # Kết luận tổng hợp
│
└── run_out.txt                        # Log output toàn bộ pipeline
```

---

## Pipeline chi tiết

### Phase 1 — Tiền xử lý (`phase1_rainfall_preprocessing.py`)
- Đọc dữ liệu CSV, resample về tần suất tháng (`MS`)
- Kiểm tra chất lượng: tháng đủ / gần đủ / thiếu nhiều / trống hoàn toàn
- Imputation bằng median hoặc prorate nếu cần (bộ dữ liệu này: 0% missing)
- Xuất `df_monthly` (569 tháng × 36 cột) và `df_meteo_monthly_context` (21 biến khí tượng)

### Phase 2 — EDA (`phase2_eda.py`)
- Thống kê mô tả, phân phối, boxplot theo tháng, heatmap tương quan
- Phân tích mùa vụ: mùa mưa T5–T11, mùa khô T12–T4, đỉnh mưa tháng 9
- Kiểm định tính dừng: ADF (p < 0.001) và KPSS — chuỗi có tính dừng
- Tính độ mạnh mùa vụ theo công thức Hyndman: **0.852** (ngưỡng tin cậy > 0.30)
- Tương quan Pearson với biến khí tượng: `PrecipitationHours` (0.967), `HumidityMean` (0.892), `CloudCoverHighMean` (0.842)

### Phase 3 — Feature Engineering (`phase3_feature_engineering.py`)
Tạo 105 features cho mô hình ML, chia thành 6 nhóm:

| Nhóm | Số features | Mô tả |
|---|---|---|
| `time` | 4 | month, quarter, month_sin, month_cos |
| `fourier` | 6 | sin/cos với k=1,2,3 |
| `rainfall_lag` | 7 | lag 1, 2, 3, 6, 12, 24, 36 tháng |
| `rainfall_rolling` | 8 | rolling mean/std window 3, 6, 12, 24 |
| `weather_lag` | 40 | lag 1 của 20 biến khí tượng |
| `weather_rolling` | 40 | rolling 3 tháng của 20 biến khí tượng |

> **Chống data leakage:** tất cả weather features chỉ dùng giá trị quá khứ (lag/rolling), không dùng giá trị cùng tháng đang dự báo. Rolling features dùng `shift(1).rolling(...)`.

### Phase 4 — Modeling (`phase4_modeling.py`)
Ba mô hình được xây dựng đại diện cho 3 nhóm:

| Mô hình | Nhóm | Mô tả |
|---|---|---|
| **Seasonal Mean** | Baseline | Trung bình lịch sử theo từng tháng trong năm |
| **Holt-Winters** | Statistical | Exponential Smoothing với trend cộng + mùa vụ cộng, period=12 |
| **Random Forest Weather** | Machine Learning | RandomForestRegressor (300 cây, max_depth=8) với 138 features lag/rolling khí tượng |

Tập train: 01/1979 – 05/2024 (545 tháng) | Tập test: 06/2024 – 05/2026 (24 tháng)

> Random Forest Weather không sử dụng dữ liệu khí tượng tương lai thật; khi dự báo dùng **climatology proxy** (trung bình cùng tháng từ lịch sử).

### Phase 5 — Feature Selection (`phase5_feature_selection.py`)
- Tương quan Pearson tuyệt đối với Rainfall: top features là `rain_lag_36` (0.836), `rain_lag_12` (0.828), `rain_lag_24` (0.816)
- Random Forest Feature Importance: `rain_lag_36` chiếm 39.6%, `PressureMSLMean_lag1` 16.5%
- 10 selected features phục vụ báo cáo/slide (không dùng để tuyệt đối hoá CV)

### Phase 6 — Evaluation (`phase6_evaluation.py`)

**Kết quả hold-out 24 tháng:**

| Mô hình | MAE | RMSE | WAPE (%) |
|---|---|---|---|
| Holt-Winters | 53.17 | 62.72 | 26.64 |
| Seasonal Mean | ~55 | ~66 | ~27 |
| Random Forest Weather | 61.18 | 73.60 | 30.65 |

**Rolling-Origin Cross-Validation (6 cửa sổ × 12 tháng):**

| Mô hình | CV-RMSE TB | CV Std |
|---|---|---|
| **Holt-Winters** | **65.87** | 16.73 |
| Seasonal Mean | ~66 | ~17 |
| Random Forest Weather | 68.82 | 17.10 |

> **Mô hình được chọn: Holt-Winters** — CV-RMSE tốt nhất và ổn định nhất qua nhiều cửa sổ thời gian. Rolling-Origin CV đáng tin hơn một hold-out đơn lẻ.

### Phase 7 — Residual Diagnostics (`phase7_residual_diagnostics.py`)
- Kiểm tra phần dư của mô hình Holt-Winters trên 24 tháng test
- Ljung-Box test: lag 6 (p=0.467), lag 12 (p=0.210) → không còn autocorrelation đáng kể
- Phần dư mean ≈ 10.2, std ≈ 63.2 — phân phối gần cân xứng

### Phase 8 — Forecast (`phase8_forecast.py`)
Refit Holt-Winters trên toàn bộ 569 tháng, dự báo 12 tháng tới:

| Tháng | Dự báo (mm) | Khoảng tin cậy 95% |
|---|---|---|
| 06/2026 | 288.4 | [187.5 – 389.3] |
| 07/2026 | 301.9 | [201.0 – 402.8] |
| 08/2026 | 310.9 | [210.0 – 411.8] |
| **09/2026** | **353.2** | [252.3 – 454.1] |
| 10/2026 | 305.5 | [204.6 – 406.4] |
| 11/2026 | 173.7 | [72.8 – 274.6] |
| 12/2026 | 91.5 | [0.0 – 192.4] |
| 01/2027 | 54.9 | [0.0 – 155.8] |
| **02/2027** | **47.1** | [0.0 – 148.0] |
| 03/2027 | 59.2 | [0.0 – 160.1] |
| 04/2027 | 108.7 | [7.8 – 209.6] |
| 05/2027 | 240.1 | [139.2 – 341.0] |

**Tổng lượng mưa dự báo 12 tháng: 2335.3 mm**

### Phase 9 — Report Conclusions (`phase9_report_conclusions.py`)
Tổng hợp toàn bộ kết quả pipeline thành báo cáo có cấu trúc: dataset summary, time series characteristics, weather feature insights, model comparison, final model selection, forecast summary, limitations, future work.

---

## Cách chạy

### Yêu cầu
```
Python >= 3.10
pandas
numpy
matplotlib
statsmodels
scikit-learn
pmdarima
```

Cài đặt:
```bash
pip install pandas numpy matplotlib statsmodels scikit-learn pmdarima
```

### Chạy toàn bộ pipeline
```bash
python run_all_phases.py
```

Pipeline sẽ tự động:
- Chạy Phase 1–9 tuần tự trong cùng namespace (các biến được chia sẻ giữa các phase)
- Lưu tất cả biểu đồ ra `output_fig_01.png` đến `output_fig_20.png`
- In log chi tiết ra stdout

### Tải lại dữ liệu từ API
```bash
python download_openmeteo_hcmc.py
```

---

## Kết quả chính

| Chỉ số | Giá trị |
|---|---|
| Mô hình được chọn | Holt-Winters |
| CV-RMSE (Rolling-Origin, 6 cửa sổ) | **65.87 mm/tháng** |
| Hold-out RMSE (24 tháng) | 62.72 mm/tháng |
| WAPE hold-out | 26.64% |
| Giai đoạn dự báo | 06/2026 – 05/2027 |
| Tổng mưa dự báo | 2335.3 mm |

---

## Hạn chế

- Open-Meteo là dữ liệu reanalysis, có thể sai lệch so với đo trực tiếp tại trạm
- Các mô hình Weather không dùng được dự báo khí tượng thật cho tương lai, phải dùng climatology proxy
- Sai số dự báo mưa tháng vẫn cao (~65 mm) do mưa chịu ảnh hưởng của nhiều hiện tượng đối lưu khó mô hình hoá

## Hướng phát triển

- Thêm tín hiệu ENSO/ONI, SST, MJO làm biến ngoại sinh để cải thiện dự báo dài hạn
- Nếu có dự báo khí tượng tháng tới thật, dùng làm exogenous input cho SARIMAX một cách hợp lệ
- Kiểm định thêm prediction interval coverage trên rolling-origin CV

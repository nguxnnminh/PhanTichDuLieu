# Dự án: Phân tích và dự báo lượng mưa trung bình tháng tại TP. Hồ Chí Minh

README này viết theo log chạy `python run_all_phases.py` mới nhất. Các con số trong tài liệu lấy từ log và từ code đang chạy, không thêm kết luận ngoài dữ liệu.

Mục tiêu của dự án:

- Kiểm tra dữ liệu mưa tháng của TP.HCM có đủ không.
- Xem lượng mưa thay đổi theo tháng, theo mùa như thế nào.
- Xem các biến thời tiết nào thường đi cùng tháng mưa nhiều.
- Thử 4 mô hình dự báo và so sánh bằng số.
- Dùng mô hình có sai số thấp nhất để dự báo 12 tháng tiếp theo.

## 1. Kết quả ngắn gọn

| Nội dung | Kết quả |
|---|---:|
| Thời gian dữ liệu | 01/1979 → 05/2026 |
| Số tháng dữ liệu | 569 |
| Kích thước sau khi đọc `Date` làm index | 569 tháng × 26 cột |
| Tháng đủ dữ liệu | 569/569 |
| Tháng phải impute | 0 |
| Lượng mưa trung bình | 162.3 mm/tháng |
| Lượng mưa thấp nhất | 0.0 mm/tháng |
| Lượng mưa cao nhất | 473.5 mm/tháng |
| Tháng mưa TB cao nhất | Tháng 9, 325.77 mm/tháng |
| Tháng mưa TB thấp nhất | Tháng 2, 12.30 mm/tháng |
| Độ mạnh mùa vụ | 0.85 |
| Mô hình được chọn | SARIMAX |
| RMSE hold-out của SARIMAX | 59.47 mm/tháng |
| CV-RMSE trung bình của SARIMAX | 68.23 mm/tháng |
| Dự báo 12 tháng | 06/2026 → 05/2027 |
| Tổng mưa dự báo 12 tháng | 1955.3 mm |

Khi chạy có vài cảnh báo:

- `InterpolationWarning` ở KPSS: p-value thực tế lớn hơn mức bảng tra cứu trả về. Log vẫn trả `p-value = 0.1000`.
- `Importing plotly failed`: không ảnh hưởng kết quả vì biểu đồ đang được lưu bằng matplotlib ra PNG.
- `cmdstanpy INFO`: log của Prophet khi fit mô hình, không phải lỗi.

## 2. Dữ liệu lấy từ đâu

Dữ liệu lấy từ Open-Meteo Historical Weather API, dạng ERA5 reanalysis. Hiểu đơn giản: đây là dữ liệu thời tiết được tổng hợp/tái phân tích từ nhiều nguồn, không phải số đo trực tiếp từ một trạm mưa trong thành phố.

Cách tạo dữ liệu TP.HCM:

- Lấy 7 tọa độ đại diện trong TP.HCM.
- Mỗi ngày tính trung bình mưa của 7 điểm.
- Mỗi tháng cộng các giá trị mưa trung bình ngày để ra `Rainfall` theo mm/tháng.

Vì vậy `Rainfall` trong dự án là **lượng mưa trung bình tháng đại diện cho TP.HCM**, không phải số đo riêng của một quận.

## 3. Dữ liệu có những cột nào

Trong file CSV có `Date` và 26 cột số liệu. Khi code đọc file, `Date` được đưa thành index thời gian, nên log in ra:

```text
569 tháng × 26 cột
```

26 cột số liệu gồm:

- 1 cột mục tiêu cần dự báo: `Rainfall`.
- 21 cột thời tiết/context.
- 4 cột kiểm tra chất lượng dữ liệu: `ValidHourlyRows`, `RainfallDays`, `ExpectedDays`, `Completeness`.

### 3.1. Cột thời gian

| Cột | Ý nghĩa | Dùng để làm gì |
|---|---|---|
| `Date` | Tháng/năm của dòng dữ liệu | Làm index, nhóm theo tháng, chia train/test, tạo biến mùa vụ |

`Date` không phải biến dự báo trực tiếp. Code dùng nó để biết dòng dữ liệu thuộc tháng nào, rồi tạo các cột như `month`, `quarter`, `month_sin`, `month_cos`.

### 3.2. Cột mục tiêu

| Cột | Ý nghĩa | Vai trò |
|---|---|---|
| `Rainfall` | Lượng mưa trung bình tháng, mm/tháng | Cột cần phân tích và cần dự báo |

`Rainfall` là cột quan trọng nhất. Mọi mô hình đều dự báo giá trị này.

Trong dự đoán, code không chỉ dùng `Rainfall` hiện tại. Code tạo thêm lịch sử mưa:

- `rain_lag_1`: mưa tháng trước.
- `rain_lag_2`: mưa 2 tháng trước.
- `rain_lag_3`: mưa 3 tháng trước.
- `rain_lag_6`: mưa 6 tháng trước.
- `rain_lag_12`: mưa cùng kỳ năm trước.
- `rain_lag_24`: mưa cùng kỳ 2 năm trước.
- `rain_lag_36`: mưa cùng kỳ 3 năm trước.

Và các cột rolling:

- `rain_roll_mean_3`, `rain_roll_mean_6`, `rain_roll_mean_12`, `rain_roll_mean_24`.
- `rain_roll_std_3`, `rain_roll_std_6`, `rain_roll_std_12`, `rain_roll_std_24`.

Nói dễ hiểu: mô hình nhìn lại các tháng cũ và mức dao động gần đây để đoán tháng tiếp theo.

### 3.3. Nhóm mưa/nước

| Cột | Ý nghĩa dễ hiểu | Dùng trong phân tích | Dùng trong dự đoán |
|---|---|---|---|
| `Precipitation` | Tổng giáng thủy trong tháng | Có trong dữ liệu gốc | Không dùng trong feature chính hiện tại |
| `PrecipitationHours` | Tổng số giờ có mưa trong tháng | Có, corr với `Rainfall` = 0.970 | Có, dạng lag/rolling |
| `Evapotranspiration` | Lượng nước bốc hơi/thoát hơi | Biến bối cảnh | Có, dạng lag/rolling |

`PrecipitationHours` là biến đi cùng `Rainfall` mạnh nhất trong log. Nhưng khi dự báo, code chỉ dùng dữ liệu quá khứ của biến này, không dùng số giờ mưa của chính tháng đang cần dự báo.

### 3.4. Nhóm nhiệt độ

| Cột | Ý nghĩa dễ hiểu | Dùng trong dự đoán |
|---|---|---|
| `TempMean` | Nhiệt độ trung bình tháng | Có |
| `TempMin` | Trung bình nhiệt độ thấp nhất ngày | Có |
| `TempMax` | Trung bình nhiệt độ cao nhất ngày | Có |
| `ApparentTempMean` | Nhiệt độ cảm nhận | Có |

Trong SARIMAX, chỉ `TempMean` được dùng trong nhóm biến hỗ trợ lag-1. Trong XGBoost và feature engineering chung, cả 4 biến nhiệt độ được tạo lag/rolling.

### 3.5. Nhóm độ ẩm và điểm sương

| Cột | Ý nghĩa dễ hiểu | Số trong log | Dùng trong dự đoán |
|---|---|---:|---|
| `HumidityMean` | Độ ẩm trung bình | Corr = 0.886 | Có |
| `HumidityMax` | Độ ẩm cao nhất | Không nằm top 8 corr | Có |
| `DewPointMean` | Điểm sương trung bình | Corr = 0.824 | Có |

Các biến này đi cùng tháng mưa nhiều khá rõ. SARIMAX dùng `HumidityMean` và `DewPointMean` dạng lag-1.

### 3.6. Nhóm mây

| Cột | Ý nghĩa dễ hiểu | Số trong log | Dùng trong dự đoán |
|---|---|---:|---|
| `CloudCoverMean` | Mây toàn phần | Corr = 0.839 | Có |
| `CloudCoverLowMean` | Mây tầng thấp | Corr = 0.722 | Có |
| `CloudCoverMidMean` | Mây tầng giữa | Corr = 0.739 | Có |
| `CloudCoverHighMean` | Mây tầng cao | Corr = 0.842 | Có |

Nhóm mây xuất hiện nhiều trong top tương quan với mưa. Điều này chỉ nói tháng mưa nhiều thường đi cùng nhiều mây trong dữ liệu, không chứng minh nguyên nhân.

### 3.7. Nhóm áp suất

| Cột | Ý nghĩa dễ hiểu | Số trong log | Dùng trong dự đoán |
|---|---|---:|---|
| `PressureMSLMean` | Áp suất quy về mực nước biển | Không nằm top 8 corr | Có |
| `SurfacePressureMean` | Áp suất mặt đất | Corr = -0.721 | Có |

`SurfacePressureMean` có tương quan âm với mưa. Nghĩa là trong dữ liệu này, tháng áp suất mặt đất thấp thường đi cùng tháng mưa nhiều hơn.

### 3.8. Nhóm gió và bức xạ

| Cột | Ý nghĩa dễ hiểu | Dùng trong dự đoán |
|---|---|---|
| `WindSpeedMax` | Tốc độ gió mạnh nhất trung bình | Có |
| `WindGustMax` | Gió giật mạnh nhất trung bình | Có |
| `WindSpeedHourlyMean` | Gió trung bình theo giờ | Có |
| `WindGustHourlyMean` | Gió giật trung bình theo giờ | Có |
| `ShortwaveRadiation` | Năng lượng bức xạ mặt trời | Có |

Nhóm này không đứng đầu bảng tương quan trong log, nhưng vẫn được dùng làm biến quá khứ trong mô hình.

### 3.9. Nhóm kiểm tra chất lượng dữ liệu

| Cột | Ý nghĩa | Dùng dự đoán không |
|---|---|---|
| `ValidHourlyRows` | Số dòng dữ liệu theo giờ hợp lệ trong tháng | Không dùng trong Phase 3 feature chính |
| `RainfallDays` | Số ngày có dữ liệu mưa hợp lệ | Không |
| `ExpectedDays` | Số ngày đúng của tháng | Không |
| `Completeness` | Tỷ lệ đầy đủ dữ liệu | Không |

Log Phase 1 cho thấy dữ liệu mưa đủ 569/569 tháng. Vì vậy nhóm này chủ yếu để chứng minh dữ liệu sạch, không phải tín hiệu dự báo mưa.

## 4. Biến nào dùng cho phân tích, biến nào dùng cho dự đoán

| Mục đích | Biến/cột dùng | Cách dùng |
|---|---|---|
| Kiểm tra dữ liệu | `RainfallDays`, `ExpectedDays`, `Completeness`, `ValidHourlyRows` | Xem tháng có đủ dữ liệu không |
| Thống kê lượng mưa | `Rainfall`, `Date` | Tính trung bình, min, max, mùa vụ |
| Tương quan | `Rainfall` + biến thời tiết cùng tháng | Xem biến nào đi cùng mưa |
| SARIMAX | `Rainfall` + 6 biến thời tiết lag-1 | Dự báo chuỗi tháng |
| XGBoost | lịch sử mưa + mùa vụ + 20 biến thời tiết quá khứ | Tạo 103 features |
| Feature engineering chung | lịch sử mưa + 20 biến thời tiết chính + thời gian | Tạo `X_ml` 533 × 105 |

Điểm quan trọng:

- Khi **phân tích**, dùng biến cùng tháng là được, vì chỉ đang mô tả dữ liệu đã biết.
- Khi **dự báo**, không được dùng biến cùng tháng, vì ngoài thực tế ta chưa biết thời tiết của tháng tương lai.

## 5. Vì sao log có 21 context nhưng mô hình dùng 20 biến thời tiết

Phase 1 in ra:

```text
Biến khí tượng bối cảnh: 21 biến
```

Con số 21 này gồm 20 biến thời tiết chính và `ValidHourlyRows`.

Phase 3 dùng danh sách `WEATHER_BASE_COLS` gồm 20 biến thời tiết chính:

```text
PrecipitationHours, ShortwaveRadiation, Evapotranspiration,
TempMean, TempMin, TempMax, ApparentTempMean,
WindSpeedMax, WindGustMax,
HumidityMean, HumidityMax, DewPointMean,
PressureMSLMean, SurfacePressureMean,
CloudCoverMean, CloudCoverLowMean, CloudCoverMidMean, CloudCoverHighMean,
WindSpeedHourlyMean, WindGustHourlyMean
```

Vì vậy hai con số không mâu thuẫn:

- **21 context** trong Phase 1 = 20 biến thời tiết chính + `ValidHourlyRows`.
- **20 biến thời tiết chính** trong Phase 3 = biến thật sự được tạo lag/rolling cho mô hình.

## 6. Luồng xử lý toàn bộ dự án

```text
hcmc_openmeteo_monthly.csv
        ↓
Phase 1: đọc dữ liệu, kiểm tra đủ/thiếu
        ↓
Phase 2: thống kê, tương quan, mùa vụ
        ↓
Phase 3: tạo feature quá khứ cho mô hình
        ↓
Phase 4: huấn luyện 4 mô hình
        ↓
Phase 5: đánh giá hold-out, rolling CV, sai số theo mùa
        ↓
Phase 6: kiểm tra phần dư
        ↓
Phase 7: dự báo 12 tháng
        ↓
Phase 8: tổng hợp kết luận
```

## 7. Phase 1: Đọc và kiểm tra dữ liệu

File: `phase1_rainfall_preprocessing.py`

Phase này làm 3 việc:

- Đọc `hcmc_openmeteo_monthly.csv`.
- Kiểm tra tháng nào đủ dữ liệu, tháng nào thiếu.
- Chuẩn bị `df_monthly` và `df_meteo_monthly_context` cho các phase sau.

Số thật từ log:

| Mục | Giá trị |
|---|---:|
| Kích thước dữ liệu | 569 tháng × 26 cột |
| Thời gian | 01/1979 → 05/2026 |
| Tháng đủ dữ liệu | 569 |
| Tháng gần đủ | 0 |
| Tháng thiếu nhiều | 0 |
| Tháng trống hoàn toàn | 0 |
| Tỷ lệ tháng đã impute | 0.0% |
| Lượng mưa thấp nhất | 0.0 mm/tháng |
| Lượng mưa cao nhất | 473.5 mm/tháng |
| Lượng mưa trung bình | 162.3 mm/tháng |
| Số tháng mưa bằng 0 | 2 |
| Biến khí tượng/context | 21 |

Cách hiểu: dữ liệu tháng đang sạch để chạy tiếp. Không có tháng nào phải bù bằng prorate, median hay nội suy.

## 8. Phase 2: Tìm hiểu dữ liệu

File: `phase2_eda.py`

Phase này không dự báo. Nó chỉ trả lời:

- Lượng mưa thường nằm ở mức nào?
- Tháng nào mưa nhiều, tháng nào mưa ít?
- Biến thời tiết nào đi cùng mưa nhiều?
- Chuỗi có dấu hiệu tăng/giảm một chiều rõ không?

### 8.1. Thống kê lượng mưa

| Chỉ số | Giá trị |
|---|---:|
| Số quan sát | 569 |
| Trung bình | 162.315164 |
| Độ lệch chuẩn | 127.318588 |
| Nhỏ nhất | 0.000000 |
| Phân vị 25% | 29.414286 |
| Trung vị | 168.557143 |
| Phân vị 75% | 271.114286 |
| Lớn nhất | 473.528571 |
| Skewness | 0.206 |
| Kurtosis | -1.233 |

Cách hiểu:

- Trung bình khoảng **162.3 mm/tháng**.
- Độ lệch chuẩn **127.3** cho thấy mưa thay đổi khá mạnh giữa các tháng.
- Skewness **0.206**: phân phối không lệch mạnh.
- Kurtosis **-1.233**: phân phối không quá nhọn; tháng cực lớn không xuất hiện quá dày.

### 8.2. Tương quan với mưa

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

Cách hiểu:

- `PrecipitationHours` đi cùng `Rainfall` mạnh nhất.
- Độ ẩm, mây và điểm sương cũng đi cùng mưa khá rõ.
- `SurfacePressureMean` có dấu âm, nghĩa là áp suất mặt đất thấp thường đi cùng tháng mưa nhiều hơn.
- Tương quan chỉ mô tả quan hệ đi cùng nhau, không chứng minh nguyên nhân.

### 8.3. Kiểm định chuỗi

| Test | Statistic | p-value | Kết luận trong log |
|---|---:|---:|---|
| ADF | -4.6186 | 0.0001 | Chuỗi có tính dừng |
| KPSS | 0.2042 | 0.1000 | Chuỗi có tính dừng |

Cách hiểu dễ nói: theo hai kiểm định này, chuỗi mưa trong bộ dữ liệu không cho thấy xu hướng tăng dần hoặc giảm dần một chiều quá rõ. Phần nổi bật hơn là quy luật theo mùa.

### 8.4. Mùa vụ

| Mục | Giá trị |
|---|---:|
| Tháng mưa TB cao nhất | Tháng 9, 325.77 mm/tháng |
| Tháng mưa TB thấp nhất | Tháng 2, 12.30 mm/tháng |
| Độ mạnh mùa vụ | 0.85 |
| Biến liên hệ mạnh nhất | PrecipitationHours, corr = 0.97 |

Cách hiểu: lượng mưa TP.HCM phụ thuộc mạnh vào tháng trong năm. Điều này là lý do các mô hình có yếu tố mùa vụ như SARIMAX/Prophet được đưa vào thử.

## 9. Phase 3: Tạo dữ liệu cho mô hình

File: `phase3_feature_engineering.py`

Phase này biến dữ liệu tháng thành bảng mà mô hình có thể học được.

Số thật từ log:

| Nhóm feature | Số cột |
|---|---:|
| time | 4 |
| fourier | 6 |
| rainfall_lag | 7 |
| rainfall_rolling | 8 |
| weather_lag | 40 |
| weather_rolling | 40 |
| Tổng | 105 |

Sau khi tạo feature:

- `X_ml`: **533 dòng × 105 cột**.
- Thời gian còn lại: **01/1982 → 05/2026**.

Vì sao còn 533 dòng? Vì các feature như lag 24 hoặc lag 36 cần dữ liệu quá khứ. Những tháng đầu chưa có đủ lịch sử nên bị bỏ.

Chi tiết feature:

| Nhóm | Cách tạo | Ý nghĩa |
|---|---|---|
| `time` | `month`, `quarter`, `month_sin`, `month_cos` | Cho mô hình biết tháng/quý và vòng mùa |
| `fourier` | sin/cos chu kỳ 12 tháng với k = 1, 2, 3 | Mô tả mùa vụ mượt hơn |
| `rainfall_lag` | mưa 1, 2, 3, 6, 12, 24, 36 tháng trước | Nhìn lại lịch sử mưa |
| `rainfall_rolling` | mean/std của 3, 6, 12, 24 tháng trước | Nhìn mức mưa gần đây và độ dao động |
| `weather_lag` | 20 biến thời tiết lag 1 và lag 3 | Dùng thời tiết quá khứ |
| `weather_rolling` | 20 biến thời tiết rolling 3 và 12 | Dùng trung bình thời tiết gần đây |

Điểm quan trọng: feature dự đoán chỉ dùng dữ liệu đã xảy ra trước tháng cần dự báo.

## 10. Phase 4: Huấn luyện 4 mô hình

File: `phase4_modeling.py`

Phase này chia dữ liệu và thử 4 mô hình.

Chia dữ liệu:

| Tập | Thời gian | Số tháng |
|---|---|---:|
| Train | 01/1979 → 05/2024 | 545 |
| Test | 06/2024 → 05/2026 | 24 |

4 mô hình:

| Mô hình | Cách hiểu đơn giản |
|---|---|
| Seasonal Naive | Dự báo tháng này bằng cùng tháng năm trước |
| SARIMAX | Mô hình chuỗi thời gian có mùa vụ, có thêm vài biến thời tiết quá khứ |
| Prophet | Mô hình chuỗi thời gian có mùa vụ |
| XGBoost | Mô hình cây quyết định, dùng nhiều feature quá khứ |

Kết quả hold-out RMSE:

| Mô hình | RMSE |
|---|---:|
| SARIMAX | 59.47 |
| Prophet | 66.69 |
| Seasonal Naive | 66.96 |
| XGBoost | 76.89 |

Thông tin riêng:

- SARIMAX chọn được công thức: `SARIMAX(3, 0, 0)x(1, 0, 1, 12)`.
- SARIMAX dùng 6 biến lag-1: `HumidityMean`, `CloudCoverMean`, `DewPointMean`, `PrecipitationHours`, `TempMean`, `ShortwaveRadiation`.
- XGBoost trong phần dự báo dùng **103 features**.

Cách hiểu: trên tập kiểm tra 24 tháng, SARIMAX có RMSE thấp nhất. Đây là kết quả trong bộ dữ liệu và cách chia này, không phải bảo đảm luôn đúng với mọi dữ liệu khác.

## 11. Phase 5: Đánh giá mô hình

File: `phase5_evaluation.py`

Phase này kiểm tra mô hình kỹ hơn, không chỉ nhìn một con số RMSE.

### 11.1. Các chỉ số nghĩa là gì

| Chỉ số | Hiểu đơn giản |
|---|---|
| MAE | Sai trung bình bao nhiêu mm/tháng |
| RMSE | Cũng là sai số mm/tháng, nhưng phạt mạnh các tháng sai lớn |
| WAPE | Sai số tính theo phần trăm tổng lượng mưa thật |
| sMAPE | Một kiểu sai số phần trăm khác |
| MASE | So với mô hình đơn giản; nhỏ hơn 1 là tốt hơn mốc so sánh |

Code không dùng MAPE thường vì mùa khô có tháng mưa gần 0, phần trăm sai số dễ bị thổi quá lớn.

### 11.2. Kết quả trên tập test 24 tháng

| Mô hình | MAE | RMSE | WAPE (%) | sMAPE (%) | MASE |
|---|---:|---:|---:|---:|---:|
| SARIMAX | 52.64 | 59.47 | 25.53 | 48.71 | 0.9756 |
| Prophet | 55.48 | 66.69 | 26.91 | 41.51 | 1.0281 |
| Seasonal Naive | 57.58 | 66.96 | 27.93 | 72.27 | 1.0672 |
| XGBoost | 64.15 | 76.89 | 31.11 | 56.70 | 1.1888 |

SARIMAX có MAE, RMSE, WAPE thấp nhất trong bảng này.

### 11.3. Rolling-origin cross-validation

Thay vì chỉ kiểm tra 1 lần, code kiểm tra 6 cửa sổ 12 tháng:

```text
06/20–05/21
06/21–05/22
06/22–05/23
06/23–05/24
06/24–05/25
06/25–05/26
```

Kết quả:

| Mô hình | CV-RMSE trung bình | CV_std | Hold-out |
|---|---:|---:|---:|
| SARIMAX | 68.23 | 14.17 | 59.47 |
| Prophet | 72.76 | 17.03 | 66.69 |
| XGBoost | 76.70 | 19.37 | 76.89 |
| Seasonal Naive | 84.60 | 20.24 | 66.96 |

Cách hiểu:

- SARIMAX có CV-RMSE thấp nhất.
- `CV_std` của SARIMAX cũng thấp nhất, nghĩa là sai số qua 6 lần kiểm tra dao động ít nhất trong 4 mô hình.
- Đây là lý do code chọn SARIMAX để dự báo 12 tháng.

### 11.4. Sai số theo mùa

| Mô hình | RMSE_all | WAPE_all | RMSE_mưa | WAPE_mưa | RMSE_khô | WAPE_khô |
|---|---:|---:|---:|---:|---:|---:|
| SARIMAX | 59.5 | 25.5 | 69.5 | 19.8 | 41.5 | 71.8 |
| Prophet | 66.7 | 26.9 | 79.6 | 22.1 | 42.4 | 65.5 |
| Seasonal Naive | 67.0 | 27.9 | 74.2 | 21.0 | 55.2 | 83.5 |
| XGBoost | 76.9 | 31.1 | 91.9 | 26.0 | 48.5 | 71.7 |

Cách hiểu:

- Mùa mưa có RMSE cao hơn vì lượng mưa lớn và biến động mạnh hơn.
- Mùa khô có WAPE cao vì mẫu số là lượng mưa thật rất nhỏ. Chỉ lệch vài mm cũng thành phần trăm lớn.
- Với SARIMAX, RMSE mùa khô **41.5** thấp hơn RMSE mùa mưa **69.5**.

## 12. Phase 6: Kiểm tra phần dư

File: `phase6_residual_diagnostics.py`

Phần dư là:

```text
phần dư = giá trị thật - giá trị dự báo
```

Nếu phần dư vẫn có quy luật rõ, nghĩa là mô hình còn bỏ sót thông tin nào đó.

Kết quả từ log:

| Mô hình | Mean residual | Std residual | p-value nhỏ nhất |
|---|---:|---:|---:|
| Seasonal Naive | 7.554 | 67.959 | 0.2950 |
| SARIMAX | 15.366 | 58.690 | 0.6479 |
| Prophet | 16.739 | 65.947 | 0.3671 |
| XGBoost | 37.384 | 68.635 | 0.4797 |

Cách hiểu:

- p-value nhỏ nhất của các mô hình đều lớn hơn 0.05.
- Theo kiểm định Ljung-Box trong code, chưa phát hiện tự tương quan đáng kể trong phần dư.
- Điều này không có nghĩa mô hình hoàn hảo. Nó chỉ nói phần sai số còn lại chưa lặp theo mẫu rõ trong kiểm định này.

## 13. Phase 7: Dự báo 12 tháng tiếp theo

File: `phase7_forecast.py`

Các mô hình được refit trên toàn bộ dữ liệu lịch sử, rồi dự báo 12 tháng tiếp theo.

Mô hình chính để trình bày: **SARIMAX**.

| Tháng | Dự báo | Cận dưới | Cận trên |
|---|---:|---:|---:|
| Tháng 6/2026 | 248.19 | 97.45 | 398.92 |
| Tháng 7/2026 | 270.87 | 120.14 | 421.60 |
| Tháng 8/2026 | 280.36 | 129.63 | 431.10 |
| Tháng 9/2026 | 327.48 | 176.75 | 478.21 |
| Tháng 10/2026 | 279.49 | 128.76 | 430.22 |
| Tháng 11/2026 | 141.90 | 0.00 | 292.63 |
| Tháng 12/2026 | 56.33 | 0.00 | 207.06 |
| Tháng 1/2027 | 20.83 | 0.00 | 171.56 |
| Tháng 2/2027 | 13.53 | 0.00 | 164.26 |
| Tháng 3/2027 | 26.00 | 0.00 | 176.73 |
| Tháng 4/2027 | 78.04 | 0.00 | 228.78 |
| Tháng 5/2027 | 212.31 | 61.58 | 363.04 |

Tóm tắt:

- Tổng mưa dự báo 12 tháng: **1955.3 mm**.
- Tháng dự báo cao nhất: **Tháng 9/2026**, **327.48 mm/tháng**.
- Tháng dự báo thấp nhất: **Tháng 2/2027**, **13.53 mm/tháng**.
- Cận dưới/cận trên là khoảng tham khảo tính từ sai số cũ, không phải cam kết chắc chắn.

So sánh dự báo 4 mô hình:

| Tháng | Seasonal Naive | SARIMAX | Prophet | XGBoost |
|---|---:|---:|---:|---:|
| Tháng 6/2026 | 348.8 | 248.2 | 292.0 | 273.2 |
| Tháng 7/2026 | 326.0 | 270.9 | 316.9 | 260.2 |
| Tháng 8/2026 | 426.8 | 280.4 | 322.6 | 307.7 |
| Tháng 9/2026 | 473.5 | 327.5 | 362.8 | 307.7 |
| Tháng 10/2026 | 301.5 | 279.5 | 311.0 | 267.9 |
| Tháng 11/2026 | 227.6 | 141.9 | 179.5 | 100.7 |
| Tháng 12/2026 | 122.0 | 56.3 | 90.6 | 41.8 |
| Tháng 1/2027 | 28.2 | 20.8 | 59.7 | 11.1 |
| Tháng 2/2027 | 58.6 | 13.5 | 51.4 | 11.6 |
| Tháng 3/2027 | 30.3 | 26.0 | 71.3 | 13.8 |
| Tháng 4/2027 | 7.7 | 78.0 | 112.9 | 56.0 |
| Tháng 5/2027 | 134.6 | 212.3 | 232.7 | 234.3 |

Cách hiểu:

- Các mô hình đều cho mùa mưa cao hơn mùa khô.
- Seasonal Naive thường cao ở các tháng mưa mạnh vì nó copy cùng tháng năm trước.
- SARIMAX là mô hình được chọn vì sai số kiểm tra trước đó thấp nhất, không phải vì dự báo tương lai chắc chắn đúng nhất.

## 14. Phase 8: Tổng hợp báo cáo

File: `phase8_report_conclusions.py`

Phase này không tạo số mới. Nó gom lại:

- dữ liệu đầu vào,
- đặc điểm theo mùa,
- tương quan thời tiết,
- so sánh mô hình,
- mô hình được chọn,
- dự báo 12 tháng,
- hạn chế và hướng phát triển.

Report cuối hiện đã được sửa để lấy chữ theo số đang chạy. Ví dụ:

- Tháng cao hơn trung bình chung được tính từ `month_avg_report`, không ghi cứng.
- Mô hình tốt nhất được lấy từ bảng sai số, không ghi cứng.
- Nhận xét về ADF/KPSS dựa trên p-value đang có.

## 15. Hạn chế

Các hạn chế nói đúng mức:

- ERA5 là dữ liệu tái phân tích, có thể khác số đo trạm thực địa.
- Dự báo 12 tháng dùng proxy/climatology cho thời tiết tương lai, không có số thời tiết tương lai thật.
- Sai số theo tháng còn lớn, nhất là mùa mưa.
- Trung bình 7 tọa độ chỉ là đại diện toàn thành phố ở mức xấp xỉ.
- Tương quan trong Phase 2 không chứng minh nguyên nhân.

## 16. Hướng phát triển

Nếu làm tiếp, nên kiểm tra bằng số chứ không chỉ thêm cho đẹp:

- Thêm ENSO/ONI/Nino3.4, SST, MJO rồi so sánh sai số trước/sau.
- Nếu có dự báo thời tiết tháng tới thật, dùng làm biến hỗ trợ và đánh giá lại.
- Kiểm tra cận dưới/cận trên trên dữ liệu quá khứ để biết khoảng dự báo có đáng tin không.
- Chỉ thử Deep Learning khi có thêm dữ liệu hoặc có mục tiêu so sánh rõ ràng.

## 17. File biểu đồ

| File | Nội dung |
|---|---|
| `output_fig_01.png` | Tương quan biến thời tiết với mưa |
| `output_fig_02.png` | Lượng mưa theo thời gian |
| `output_fig_03.png` | Lượng mưa trung bình theo tháng |
| `output_fig_04.png` | Boxplot lượng mưa theo tháng |
| `output_fig_05.png` | Phân rã chuỗi thời gian |
| `output_fig_06.png` | ACF/PACF |
| `output_fig_07.png` | Seasonal plot |
| `output_fig_08.png` | Chia train/test |
| `output_fig_09.png` | So sánh 4 mô hình |
| `output_fig_10.png` | So sánh mô hình trên tập test |
| `output_fig_11.png` | Kiểm tra phần dư |
| `output_fig_12.png` | Dự báo SARIMAX 12 tháng |
| `output_fig_13.png` | So sánh dự báo 4 mô hình |
09/2026 và thấp nhất ở 02/2027. Kết quả nên dùng như tham khảo theo mùa; nếu muốn dùng thực tế cần kiểm tra thêm bằng dữ liệu trạm và biến khí hậu lớn.

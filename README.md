# Dự án: Phân tích và dự báo lượng mưa trung bình tháng tại TP. Hồ Chí Minh

## 1. Mục tiêu

Dự án dùng dữ liệu khí tượng lịch sử (1979–2026) để:
- Phân tích đặc điểm lượng mưa theo tháng tại TP.HCM (mùa mưa, mùa khô, xu hướng).
- So sánh 4 mô hình dự báo khác nhau.
- Dự báo lượng mưa trung bình cho 12 tháng tiếp theo (06/2026 → 05/2027).

---

## 2. Dữ liệu dùng trong dự án

### 2.1. Nguồn dữ liệu

- Nguồn: **Open-Meteo Historical Weather API** (dữ liệu tái phân tích ERA5 — không phải số liệu đo trực tiếp từ trạm khí tượng, mà là dữ liệu mô hình hóa lại từ vệ tinh + trạm + mô hình khí hậu toàn cầu).
- Khoảng thời gian: **01/1979 → 05/2026** (569 tháng dữ liệu).
- Vì TP.HCM khá rộng, dữ liệu được lấy tại **7 tọa độ đại diện** trải khắp thành phố (trung tâm Q1/Q3, Củ Chi, Thủ Đức, Bình Chánh, Nhà Bè, Q9, Tân Bình), sau đó **tính trung bình của 7 điểm** này cho mỗi ngày để ra một con số đại diện cho toàn thành phố.

### 2.2. Biến mục tiêu (cái cần dự báo)

- **Rainfall (Lượng mưa trung bình tháng)** — đơn vị mm/tháng.
- Cách tính: mỗi ngày lấy lượng mưa trung bình của 7 điểm tọa độ → cộng tất cả các ngày trong tháng → ra lượng mưa của tháng đó.
- Đây là cột mà tất cả mô hình cố gắng dự báo.

### 2.3. Danh sách toàn bộ các biến trong bộ dữ liệu (26 cột)

Dữ liệu hàng tháng gồm 26 cột, gồm 1 cột ngày, 1 cột mục tiêu (Rainfall), và 21 biến khí tượng "bối cảnh" (context variables) dùng để hỗ trợ giải thích/dự báo lượng mưa.

**Cột thời gian:**
- `Date` — Tháng/năm của dòng dữ liệu (ví dụ 2026-05-01 = tháng 5/2026).

**Biến mục tiêu:**
- `Rainfall` — Lượng mưa trung bình tháng (mm/tháng). Đây là biến cần dự báo.

**Nhóm lượng mưa / lượng nước:**
- `Precipitation` — Tổng lượng giáng thủy trong tháng (mm), gồm cả mưa, mưa đá, tuyết (ở HCM chủ yếu là mưa, gần giống Rainfall nhưng tính theo công thức khác của Open-Meteo).
- `PrecipitationHours` — Tổng số giờ có mưa trong tháng. Biến này có tương quan rất cao với lượng mưa (0.97) — tháng nào mưa nhiều giờ thì lượng mưa cũng nhiều.
- `Evapotranspiration` — Tổng lượng bốc hơi + thoát hơi nước (ET0) trong tháng (mm). Liên quan đến độ "khô" của không khí và đất.

**Nhóm nhiệt độ:**
- `TempMean` — Nhiệt độ không khí trung bình trong tháng (°C).
- `TempMin` — Nhiệt độ thấp nhất trung bình mỗi ngày, gộp lại lấy trung bình tháng (°C).
- `TempMax` — Nhiệt độ cao nhất trung bình mỗi ngày, gộp lại lấy trung bình tháng (°C).
- `ApparentTempMean` — Nhiệt độ "cảm nhận được" trung bình (có tính cả độ ẩm, gió — tức là nhiệt độ cơ thể người cảm nhận, không chỉ là nhiệt độ không khí thật).

**Nhóm gió:**
- `WindSpeedMax` — Tốc độ gió tối đa trung bình trong tháng (km/h).
- `WindGustMax` — Tốc độ gió giật (gió mạnh đột ngột) tối đa trung bình trong tháng (km/h).
- `WindSpeedHourlyMean` — Tốc độ gió trung bình tính theo dữ liệu từng giờ (km/h).
- `WindGustHourlyMean` — Tốc độ gió giật trung bình tính theo dữ liệu từng giờ (km/h).

**Nhóm độ ẩm:**
- `HumidityMean` — Độ ẩm không khí tương đối trung bình trong tháng (%). Tương quan cao với lượng mưa (0.886) — không khí ẩm hơn thường đi kèm mưa nhiều hơn.
- `HumidityMax` — Độ ẩm không khí tương đối cao nhất trong tháng (%).
- `DewPointMean` — Điểm sương trung bình (°C) — nhiệt độ mà không khí cần hạ xuống để hơi nước bắt đầu ngưng tụ thành sương/mưa. Điểm sương cao = không khí chứa nhiều hơi nước = dễ mưa. Tương quan với mưa: 0.824.

**Nhóm áp suất khí quyển:**
- `PressureMSLMean` — Áp suất khí quyển trung bình quy về mực nước biển (hPa).
- `SurfacePressureMean` — Áp suất khí quyển trung bình tại mặt đất (hPa). Tương quan **âm** với mưa (-0.721) — áp suất thấp thường gắn với thời tiết xấu, nhiều mưa.

**Nhóm mây che phủ (rất quan trọng với mưa):**
- `CloudCoverMean` — Tỷ lệ mây che phủ trung bình toàn bầu trời (%). Tương quan với mưa: 0.839.
- `CloudCoverLowMean` — Tỷ lệ mây tầng thấp (gần mặt đất) (%). Tương quan: 0.722.
- `CloudCoverMidMean` — Tỷ lệ mây tầng giữa (%). Tương quan: 0.739.
- `CloudCoverHighMean` — Tỷ lệ mây tầng cao (%). Tương quan cao nhất trong nhóm mây: 0.842.

**Nhóm năng lượng mặt trời:**
- `ShortwaveRadiation` — Tổng năng lượng bức xạ mặt trời (sóng ngắn) chiếu xuống mặt đất trong tháng. Tháng nhiều mây/mưa thì giá trị này thường thấp hơn.

**Nhóm chất lượng dữ liệu (kỹ thuật, không phải khí tượng):**
- `RainfallDays` — Số ngày trong tháng có dữ liệu mưa hợp lệ.
- `ExpectedDays` — Số ngày thực tế của tháng đó (28-31 ngày).
- `Completeness` — Tỷ lệ hoàn thiện dữ liệu = RainfallDays / ExpectedDays. Trong dự án này tất cả các tháng đều đạt 100% (đủ dữ liệu, không có tháng nào bị thiếu hoặc phải tự ước lượng/impute).
- `ValidHourlyRows` — Số dòng dữ liệu theo giờ hợp lệ trong tháng (dùng để tính các biến trung bình theo giờ như Humidity, CloudCover...).

> **Tóm lại**: Có 21 biến khí tượng "giải thích" (Precipitation, PrecipitationHours, Evapotranspiration, TempMean/Min/Max, ApparentTempMean, gió (4 biến), độ ẩm (3 biến), áp suất (2 biến), mây (4 biến), ShortwaveRadiation) cộng với 1 biến mục tiêu (Rainfall) và 4 cột kỹ thuật về chất lượng dữ liệu.

---

## 3. Quy trình xử lý (9 phase)

Toàn bộ pipeline chạy qua file `run_all_phases.py`, gồm 9 bước:

### Phase 1 — Tiền xử lý dữ liệu mưa
- Đọc file `hcmc_openmeteo_monthly.csv` (569 tháng × 26 cột).
- Kiểm tra chất lượng từng tháng: tháng nào đủ dữ liệu, tháng nào thiếu.
- **Kết quả**: 569/569 tháng đều "Đủ" dữ liệu (0% phải ước lượng/impute).
- Thống kê nhanh: lượng mưa tháng thấp nhất = 0.0 mm, cao nhất = 473.5 mm, trung bình = 162.3 mm/tháng. Có 2 tháng lượng mưa = 0.

### Phase 2 — Phân tích thăm dò dữ liệu (EDA)
- Tính các chỉ số thống kê mô tả: trung bình (162.3), độ lệch chuẩn (127.3), trung vị (168.6), v.v.
- **Skewness = 0.206**: phân phối lượng mưa khá đối xứng (không lệch nhiều).
- **Kurtosis = -1.233**: phân phối "bẹt" (platykurtic), ít giá trị ngoại lệ cực đoan.
- Tính tương quan giữa lượng mưa và 21 biến khí tượng. Các biến tương quan mạnh nhất:
  - PrecipitationHours: 0.970
  - HumidityMean: 0.886
  - CloudCoverHighMean: 0.842
  - CloudCoverMean: 0.839
  - DewPointMean: 0.824
  - CloudCoverMidMean: 0.739
  - CloudCoverLowMean: 0.722
  - SurfacePressureMean: -0.721 (tương quan nghịch)
- Kiểm định tính dừng (stationarity) của chuỗi thời gian bằng 2 phép kiểm:
  - **ADF test**: statistic = -4.6186, p-value = 0.0001 → chuỗi **có tính dừng** (không có xu hướng tăng/giảm dài hạn rõ rệt).
  - **KPSS test**: statistic = 0.2042, p-value = 0.10 → cũng cho thấy chuỗi **có tính dừng**.
  - Hai kết quả đồng thuận → lượng mưa TP.HCM dao động theo mùa nhưng không có xu hướng tăng/giảm dài hạn rõ rệt qua 47 năm.
- Phát hiện theo mùa:
  - Tháng mưa nhiều nhất: **Tháng 9** (trung bình 325.77 mm/tháng).
  - Tháng mưa ít nhất: **Tháng 2** (trung bình 12.30 mm/tháng).
  - **Season strength = 0.854** (theo công thức Hyndman) → tính mùa vụ **rất mạnh**. Nói cách khác, gần như toàn bộ biến động lượng mưa là do yếu tố mùa (mùa mưa T5-T11 vs mùa khô T12-T4), chứ không phải ngẫu nhiên.
- Tạo ra 7 biểu đồ (output_fig_01 đến output_fig_07): phân phối lượng mưa, biểu đồ theo mùa, ma trận tương quan, ACF/PACF (biểu đồ tự tương quan để xem mưa tháng này liên quan thế nào đến các tháng trước).

### Phase 3 — Feature Engineering (tạo biến đầu vào cho mô hình)
- Từ 26 cột gốc, tạo ra **105 features (biến đầu vào)** cho mô hình machine learning, gồm 6 nhóm:
  - **time (4 biến)**: thông tin thời gian như tháng, năm...
  - **fourier (6 biến)**: các hàm sin/cos để mô hình "hiểu" được tính tuần hoàn theo mùa (12 tháng/chu kỳ).
  - **rainfall_lag (7 biến)**: lượng mưa của các tháng trước (ví dụ mưa tháng trước, mưa cùng kỳ năm trước...).
  - **rainfall_rolling (8 biến)**: trung bình/tổng lượng mưa trượt qua nhiều tháng (ví dụ trung bình 3 tháng gần nhất).
  - **weather_lag (40 biến)**: giá trị của 21 biến khí tượng ở các tháng **trước** (không dùng giá trị tháng hiện tại để tránh "nhìn trước tương lai").
  - **weather_rolling (40 biến)**: trung bình trượt của các biến khí tượng qua nhiều tháng trước.
- **Nguyên tắc chống rò rỉ dữ liệu (data leakage)**: Tất cả biến khí tượng chỉ dùng giá trị của **các tháng trong quá khứ** (lag) hoặc trung bình trượt **đã shift 1 tháng**, không bao giờ dùng số liệu khí tượng của chính tháng đang dự báo — vì trong thực tế, khi dự báo tương lai, ta không biết trước thời tiết tháng tới sẽ như thế nào.
- Sau khi loại bỏ các dòng bị thiếu do tính lag/rolling, còn lại **533 tháng** dữ liệu (từ 01/1982 đến 05/2026) để huấn luyện mô hình.

### Phase 3.5 — Diễn giải sâu hơn về 105 features

Để hình dung rõ hơn 105 features được tạo ra như thế nào, dưới đây là ví dụ cụ thể cho từng nhóm:

- **time (4 biến)**: ví dụ — số thứ tự tháng trong năm (1-12), năm, chỉ số thời gian tuyến tính (1, 2, 3... tăng dần theo tháng để mô hình nhận biết xu hướng dài hạn nếu có).
- **fourier (6 biến)**: gồm 3 cặp sin/cos với các chu kỳ khác nhau (thường là chu kỳ 12 tháng và bội số của nó). Đây là cách "mã hóa" tính tuần hoàn cho các mô hình không tự hiểu được khái niệm "tháng" — ví dụ XGBoost không biết tháng 12 và tháng 1 là liền kề nhau nếu chỉ nhìn số 12 và 1, nhưng sin/cos sẽ thể hiện đúng tính liên tục đó.
- **rainfall_lag (7 biến)**: lượng mưa của 1, 2, 3, 6, 9, 12, 24 tháng trước (lag-1, lag-2... lag-24). Ví dụ lag-12 = lượng mưa cùng tháng năm ngoái — rất quan trọng vì mưa có tính mùa mạnh.
- **rainfall_rolling (8 biến)**: trung bình/tổng/độ lệch chuẩn của lượng mưa trong 3, 6, 12 tháng gần nhất (tính bằng `shift(1).rolling()` để không dùng tháng hiện tại).
- **weather_lag (40 biến)**: với mỗi biến khí tượng (21 biến), lấy giá trị lag-1 và lag-12 (giá trị tháng trước và giá trị cùng tháng năm trước) → 21 × ~2 ≈ 40 biến.
- **weather_rolling (40 biến)**: trung bình trượt 3 tháng và 12 tháng của mỗi biến khí tượng (21 biến × ~2 ≈ 40 biến), cũng dùng shift(1) để tránh leakage.

**Tại sao phải làm phức tạp như vậy?** Vì các mô hình machine learning (XGBoost) và thống kê (SARIMAX) không "nhìn thấy" được lịch sử theo cách tự nhiên như con người — chúng cần được "mô tả" lịch sử dưới dạng các cột số cụ thể (lag, rolling, fourier...). Việc tạo features tốt thường ảnh hưởng đến chất lượng dự báo nhiều hơn cả việc chọn mô hình.

---

### Phase 4 — Xây dựng 4 mô hình dự báo
- Chia dữ liệu: **545 tháng huấn luyện** (01/1979 → 05/2024) và **24 tháng kiểm tra** (06/2024 → 05/2026, tức 2 năm gần nhất).
- 4 mô hình được xây dựng:

  1. **Seasonal Naive** (mô hình cơ sở, đơn giản nhất): dự báo tháng này = giá trị thực tế của **cùng tháng năm trước** (y(t) = y(t-12)). Dùng để làm "đường chuẩn" so sánh — nếu mô hình phức tạp không đánh bại được cách dự báo ngây thơ này thì không đáng dùng.
     - RMSE hold-out: 66.96 mm/tháng.

  2. **SARIMAX** (mô hình thống kê chuỗi thời gian có tính mùa vụ + biến ngoại sinh):
     - Tự động tìm ra cấu hình tốt nhất: SARIMAX(3,0,0)x(1,0,1,12) — nghĩa là mô hình dùng 3 tháng trước gần nhất + 1 thành phần mùa vụ theo chu kỳ 12 tháng.
     - Dùng thêm 6 biến khí tượng (lấy giá trị tháng trước, lag-1) làm biến ngoại sinh hỗ trợ: HumidityMean, CloudCoverMean, DewPointMean, PrecipitationHours, TempMean, ShortwaveRadiation.
     - RMSE hold-out: **59.47 mm/tháng** (tốt nhất).

  3. **Prophet** (mô hình chuỗi thời gian của Meta/Facebook, chuyên xử lý tính mùa vụ và xu hướng):
     - RMSE hold-out: 66.69 mm/tháng.

  4. **XGBoost** (mô hình machine learning dạng cây quyết định, dùng toàn bộ 103 features đã tạo ở Phase 3):
     - RMSE hold-out: 76.89 mm/tháng (kém nhất trong 4 mô hình).

**Tại sao XGBoost lại kém hơn SARIMAX trong bài toán này?**
- Dữ liệu chỉ có 533 tháng (~44 năm) — đối với machine learning hiện đại, đây là một bộ dữ liệu **nhỏ**. XGBoost cần nhiều dữ liệu để "học" được pattern phức tạp từ 103 features.
- Lượng mưa TP.HCM có tính mùa vụ rất mạnh và khá ổn định qua các năm (season strength 0.854) — đây chính là loại bài toán mà các mô hình thống kê chuyên về mùa vụ như SARIMAX có lợi thế tự nhiên.
- XGBoost dễ bị "quá khớp" (overfit) với 103 features trên dữ liệu ít, dẫn đến dự báo kém ổn định hơn trên dữ liệu mới.

**Vì sao chọn SARIMAX(3,0,0)x(1,0,1,12)?**
- `(3,0,0)` — phần không theo mùa: mô hình dùng 3 tháng gần nhất (AR bậc 3) để dự báo, không cần lấy sai phân (d=0) vì chuỗi đã có tính dừng (theo ADF/KPSS ở Phase 2), không có thành phần trung bình trượt (MA=0).
- `(1,0,1,12)` — phần theo mùa với chu kỳ 12 tháng: có 1 thành phần tự hồi quy theo mùa (cùng tháng năm trước ảnh hưởng đến tháng này), không lấy sai phân theo mùa, có 1 thành phần trung bình trượt theo mùa.
- Cấu hình này được tìm ra tự động bằng `auto_arima` — thử nhiều tổ hợp (p,d,q)(P,D,Q,12) và chọn ra cấu hình có độ phù hợp tốt nhất với dữ liệu.

### Phase 5 — Đánh giá mô hình chi tiết
- Bảng so sánh đầy đủ các chỉ số trên 24 tháng kiểm tra:

| Mô hình | MAE | RMSE | WAPE (%) | sMAPE (%) | MASE |
|---|---|---|---|---|---|
| SARIMAX | 52.64 | 59.47 | 25.53 | 48.71 | 0.9756 |
| Prophet | 55.48 | 66.69 | 26.91 | 41.51 | 1.0281 |
| Seasonal Naive | 57.58 | 66.96 | 27.93 | 72.27 | 1.0672 |
| XGBoost | 64.15 | 76.89 | 31.11 | 56.70 | 1.1888 |

  - **MAE** (Mean Absolute Error): sai số tuyệt đối trung bình (mm/tháng) — càng nhỏ càng tốt.
  - **RMSE** (Root Mean Squared Error): sai số bình phương trung bình, phạt nặng các sai số lớn — càng nhỏ càng tốt.
  - **WAPE** (Weighted Absolute Percentage Error): sai số tính theo % so với tổng thực tế — càng nhỏ càng tốt.
  - **sMAPE** (symmetric Mean Absolute Percentage Error): sai số % đối xứng, xử lý tốt hơn khi giá trị thực tế gần 0.
  - **MASE** (Mean Absolute Scaled Error): so sánh sai số của mô hình với sai số của Seasonal Naive. MASE < 1 nghĩa là mô hình **tốt hơn** so với dự báo ngây thơ "lấy y hệt năm trước".
  - Ghi chú: **MAPE không được dùng** vì một số tháng mùa khô có lượng mưa gần 0, làm MAPE bị "nổ" (chia cho số gần 0).

- **Rolling-Origin Cross-Validation (kiểm định chéo theo thời gian)**:
  - Thay vì chỉ kiểm tra trên 1 giai đoạn 24 tháng (có thể là "may" hoặc "rủi"), kiểm tra trên **6 cửa sổ 12 tháng khác nhau**: 06/2020-05/2021, 06/2021-05/2022, 06/2022-05/2023, 06/2023-05/2024, 06/2024-05/2025, 06/2025-05/2026.
  - Kết quả CV-RMSE trung bình (và độ lệch chuẩn):

| Mô hình | CV-RMSE trung bình | CV độ lệch chuẩn | Hold-out RMSE |
|---|---|---|---|
| Seasonal Naive | 84.60 | 20.24 | 66.96 |
| SARIMAX | **68.23** | 14.17 | 59.47 |
| Prophet | 72.76 | 17.03 | 66.69 |
| XGBoost | 76.70 | 19.37 | 76.89 |

  - **SARIMAX thắng cả 2 tiêu chí** (CV-RMSE và Hold-out RMSE) → được chọn làm mô hình chính cho dự báo cuối cùng.
  - Nhận xét thêm về độ lệch chuẩn CV (CV_std): SARIMAX có CV_std thấp nhất (14.17), nghĩa là sai số của SARIMAX **ổn định nhất** qua 6 cửa sổ kiểm tra khác nhau — không có giai đoạn nào dự báo "trượt" quá nặng. Ngược lại, Seasonal Naive có CV_std cao nhất (20.24), cho thấy độ tin cậy không đều giữa các năm.
  - So với baseline Seasonal Naive (CV-RMSE 84.60), SARIMAX cải thiện khoảng **19.4%** (giảm từ 84.60 xuống 68.23 mm/tháng) — đây là mức cải thiện thực chất nhờ mô hình thống kê có tính mùa vụ + biến khí tượng hỗ trợ, không chỉ là "copy năm trước".

- **Phân tích sai số theo mùa** (mùa mưa T5-T11 vs mùa khô T12-T4):

| Mô hình | RMSE tổng | WAPE tổng | RMSE mùa mưa | WAPE mùa mưa | RMSE mùa khô | WAPE mùa khô |
|---|---|---|---|---|---|---|
| SARIMAX | 59.5 | 25.5% | 69.5 | 19.8% | 41.5 | 71.8% |
| Prophet | 66.7 | 26.9% | 79.6 | 22.1% | 42.4 | 65.5% |
| Seasonal Naive | 67.0 | 27.9% | 74.2 | 21.0% | 55.2 | 83.5% |
| XGBoost | 76.9 | 31.1% | 91.9 | 26.0% | 48.5 | 71.7% |

  - Nhận xét quan trọng: WAPE mùa khô luôn cao hơn nhiều so với mùa mưa (ví dụ SARIMAX: 71.8% vs 19.8%). Điều này **không có nghĩa mô hình tệ** — vì mùa khô lượng mưa thực tế rất nhỏ (gần 0), nên chỉ một sai số nhỏ về mm cũng tạo ra tỷ lệ % sai số rất lớn. RMSE tuyệt đối (mm) ở mùa khô vẫn nhỏ hơn mùa mưa.

### Phase 6 — Kiểm tra phần dư (Residual Diagnostics)
- Mục đích: kiểm tra xem sau khi mô hình dự báo, phần "sai số còn lại" (residual = thực tế - dự báo) có còn chứa quy luật/thông tin nào chưa được mô hình nắm bắt hay không. Nếu residual vẫn có tự tương quan (autocorrelation) thì mô hình chưa "khai thác hết" thông tin trong dữ liệu.
- Dùng phép kiểm **Ljung-Box** trên 24 residual của mỗi mô hình (kiểm tra ở lag 6 và lag 12 tháng):

| Mô hình | Mean residual | Std residual | Ljung-Box p-value (lag 6 / lag 12) | Kết luận |
|---|---|---|---|---|
| Seasonal Naive | 7.554 | 67.959 | 0.295 / 0.758 | Không còn tự tương quan đáng kể |
| SARIMAX | 15.366 | 58.690 | 0.648 / 0.662 | Không còn tự tương quan đáng kể |
| Prophet | 16.739 | 65.947 | 0.525 / 0.367 | Không còn tự tương quan đáng kể |
| XGBoost | 37.384 | 68.635 | 0.542 / 0.480 | Không còn tự tương quan đáng kể |

  - Tất cả p-value > 0.05 → phần dư của cả 4 mô hình đều **giống nhiễu ngẫu nhiên** (white noise), không còn quy luật rõ rệt nào bị "bỏ sót". Đây là dấu hiệu tốt — mô hình đã khai thác hợp lý cấu trúc dữ liệu.
  - Lưu ý: SARIMAX có **Mean residual = 15.366** (dương) — mô hình có xu hướng dự báo **thấp hơn thực tế một chút** trung bình ~15mm/tháng, nhưng đây vẫn là mức sai lệch chấp nhận được so với độ lệch chuẩn lượng mưa (~127mm).
  - 1 biểu đồ được tạo (output_fig_11) minh họa phân phối và ACF của residual từng mô hình.

### Phase 7 — Dự báo 12 tháng tới (06/2026 → 05/2027)
- Tất cả 4 mô hình được **huấn luyện lại trên toàn bộ dữ liệu** (569 tháng, không chỉ phần train cũ) để tận dụng tối đa thông tin, rồi dự báo 12 tháng tiếp theo.
- Kết quả dự báo của mô hình được chọn (**SARIMAX**), kèm khoảng tin cậy (cận dưới — cận trên):

| Tháng | Dự báo (mm) | Cận dưới | Cận trên |
|---|---|---|---|
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

  - **Tổng lượng mưa dự báo cả năm**: 1955.3 mm.
  - **Tháng mưa nhiều nhất**: Tháng 9/2026 (327.48 mm).
  - **Tháng mưa ít nhất**: Tháng 2/2027 (13.53 mm).
  - Cận dưới = 0.00 ở các tháng mùa khô vì khoảng tin cậy thống kê tính ra số âm, được "cắt" về 0 (lượng mưa không thể âm).

**Đọc bảng dự báo như thế nào?**
- Mỗi dòng là 1 tháng, với 3 con số: **Dự báo** (giá trị mô hình cho là khả năng cao nhất), **Cận dưới/Cận trên** (khoảng tin cậy 95% — mô hình "tin" rằng giá trị thực tế sẽ rơi vào khoảng này với độ tin cậy 95%).
- Khoảng tin cậy ở các tháng mùa mưa (06-10/2026) khá rộng (~150-300mm), nghĩa là mô hình vẫn còn nhiều bất định ở các tháng mưa nhiều — phù hợp với nhận xét ở Phase 5 rằng RMSE tuyệt đối mùa mưa cao hơn mùa khô.
- Khoảng tin cậy ở mùa khô (11/2026-04/2027) bị cắt về 0 ở cận dưới — về mặt thống kê nghĩa là "có khả năng tháng đó gần như không mưa", điều này phù hợp với thực tế khí hậu TP.HCM.

**Đối chiếu xu hướng theo mùa của dự báo với dữ liệu lịch sử (Phase 2):**
- Lịch sử: tháng mưa nhiều nhất trung bình là **Tháng 9** (325.77mm) — dự báo cũng cho Tháng 9/2026 là tháng mưa nhiều nhất (327.48mm). Khớp với quy luật lịch sử.
- Lịch sử: tháng mưa ít nhất trung bình là **Tháng 2** (12.30mm) — dự báo cũng cho Tháng 2/2027 là tháng mưa ít nhất (13.53mm). Khớp với quy luật lịch sử.
- → Mô hình SARIMAX đã "học" đúng được tính mùa vụ đặc trưng của TP.HCM, không chỉ là một con số dự báo ngẫu nhiên.

**So sánh 4 mô hình trong bảng dự báo:**
- Các mô hình khá đồng thuận về **xu hướng** (tháng nào mưa nhiều, tháng nào mưa ít) nhưng khác nhau về **biên độ** cụ thể.
- Seasonal Naive luôn cho biên độ lớn nhất ở các tháng cao điểm (vì nó "copy y hệt" năm trước, không làm mượt) — ví dụ Tháng 9/2026 Seasonal Naive dự báo 473.5mm (chính là giá trị thực tế Tháng 9/2025), cao hơn nhiều so với SARIMAX (327.5mm).
- SARIMAX và Prophet cho kết quả gần nhau hơn ở các tháng mùa mưa, trong khi XGBoost thường cho giá trị thấp hơn ở các tháng cao điểm.

- So sánh dự báo của cả 4 mô hình cho 12 tháng:

| Tháng | Seasonal Naive | SARIMAX | Prophet | XGBoost |
|---|---|---|---|---|
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

  - 2 biểu đồ được tạo (output_fig_12, output_fig_13) để minh họa trực quan dự báo của các mô hình.

### Phase 8 — Báo cáo kết luận tổng hợp
Tổng hợp lại toàn bộ kết quả dưới dạng báo cáo, gồm các phần:

1. **Tổng quan dữ liệu**: TP.HCM, 569 tháng (01/1979-05/2026), 21 biến khí tượng, nguồn ERA5.
2. **Đặc điểm chuỗi thời gian**: mùa mưa T5-T11, mùa khô T12-T4, đỉnh mưa tháng 9, season strength 0.854 (rất mạnh).
3. **Phân tích biến khí tượng**: các biến tương quan mạnh nhất với mưa là PrecipitationHours, HumidityMean, CloudCoverHighMean, CloudCoverMean, DewPointMean, CloudCoverMidMean. Tất cả chỉ dùng dạng lag/rolling quá khứ, không dùng giá trị cùng tháng (tránh leakage).
4. **So sánh mô hình**: bảng 4 mô hình như Phase 5.
5. **Lựa chọn mô hình**: SARIMAX (CV-RMSE 68.23, Hold-out RMSE 59.47).
6. **Dự báo**: 06/2026-05/2027, tổng 1955.3mm, tháng mưa nhiều nhất 09/2026 (327.48mm), ít nhất 02/2027 (13.53mm).

7. **Hạn chế của dự án**:
   - Dữ liệu Open-Meteo là tái phân tích (ERA5), có thể khác với số liệu đo thực tế tại trạm.
   - Không có dữ liệu khí tượng thật của tương lai; các mô hình dùng giá trị lag/proxy.
   - Sai số dự báo theo mùa vẫn còn cao vì lượng mưa bị ảnh hưởng bởi nhiều yếu tố khí hậu phức tạp (El Nino, La Nina, v.v. — chưa được đưa vào mô hình).
   - Trung bình 7 tọa độ chỉ là một cách xấp xỉ, chưa thể thay thế mạng lưới trạm đo dày đặc thực tế.

8. **Hướng phát triển tiếp theo**:
   - Thêm các chỉ số khí hậu lớn như ENSO/ONI/Nino3.4, nhiệt độ mặt biển (SST), MJO để có tín hiệu dự báo dài hạn hơn.
   - Nếu có dữ liệu dự báo khí tượng thật cho tháng tới, có thể dùng làm biến ngoại sinh hợp lệ hơn.
   - Kiểm định thêm độ phủ của khoảng tin cậy dự báo (prediction interval coverage) trên rolling-origin CV.
   - Thử nghiệm các mô hình Deep Learning (LSTM, Temporal Fusion Transformer) nếu có thêm dữ liệu.

---

## 4. Danh sách các file output

- `output_fig_01.png` đến `output_fig_07.png`: các biểu đồ EDA (phân phối, theo mùa, tương quan, ACF/PACF, stationarity).
- `output_fig_08.png`: biểu đồ chia tập train/test.
- `output_fig_09.png`: biểu đồ liên quan đến XGBoost.
- `output_fig_10.png`: biểu đồ so sánh các mô hình ở Phase 5.
- `output_fig_11.png`: biểu đồ residual diagnostics.
- `output_fig_12.png`, `output_fig_13.png`: biểu đồ dự báo 12 tháng của các mô hình.

---

## 5. Tóm tắt số liệu quan trọng nhất (để làm slide)

- **569 tháng dữ liệu** (01/1979 → 05/2026), 100% đầy đủ, không cần ước lượng/impute.
- **Lượng mưa trung bình**: 162.3 mm/tháng (thấp nhất 0.0, cao nhất 473.5).
- **Mùa vụ rất mạnh** (season strength 0.854): mưa nhiều T5-T11, đỉnh điểm T9 (325.77mm); khô T12-T4, thấp điểm T2 (12.30mm).
- **Chuỗi có tính dừng** (theo cả ADF và KPSS) — không có xu hướng tăng/giảm dài hạn rõ rệt qua 47 năm.
- **4 mô hình được so sánh**: Seasonal Naive, SARIMAX, Prophet, XGBoost.
- **SARIMAX thắng** với RMSE hold-out 59.47mm, CV-RMSE 68.23mm, WAPE 25.53%.
- **Dự báo 12 tháng tới (06/2026-05/2027)**: tổng 1955.3mm, đỉnh T9/2026 (327.48mm), đáy T2/2027 (13.53mm).
- Tất cả mô hình đều "qua" kiểm tra residual (Ljung-Box p > 0.05) — không còn quy luật bị bỏ sót trong sai số.

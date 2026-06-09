# Phân Tích và Dự Báo Lượng Mưa TP.HCM

Dự án phân tích dữ liệu lượng mưa theo tháng tại **Thành phố Hồ Chí Minh** từ năm 1979 đến 2026, sau đó dự báo 12 tháng tiếp theo. Toàn bộ pipeline chạy tự động từ bước đọc dữ liệu cho đến khi ra kết quả dự báo cuối cùng.

---

## Dữ liệu

- **Nguồn:** Open-Meteo Historical Weather API — dữ liệu khí tượng lịch sử miễn phí
- **Thời gian:** 01/1979 đến 05/2026 — tổng cộng **569 tháng**
- **Biến cần dự báo:** Lượng mưa trung bình mỗi tháng (mm/tháng)
- **Biến khí tượng đi kèm:** 21 biến như nhiệt độ, độ ẩm, áp suất, lượng mây, tốc độ gió, bức xạ mặt trời...

> Lưu ý: đây là dữ liệu tái phân tích (reanalysis) — tức là máy tính tổng hợp lại từ nhiều nguồn, không phải đo trực tiếp từ trạm khí tượng thực địa nên có thể có sai lệch nhỏ so với thực tế.

**Một vài con số đáng chú ý:**

| | Giá trị |
|---|---|
| Trung bình | 159.2 mm/tháng |
| Tháng mưa nhiều nhất (trung bình) | Tháng 9 — 318.6 mm |
| Tháng mưa ít nhất (trung bình) | Tháng 2 — 12.5 mm |
| Mùa mưa | Tháng 5 đến tháng 11 |
| Mùa khô | Tháng 12 đến tháng 4 |

---

## Cấu trúc thư mục

```
PhanTichDuLieu/
│
├── run_all_phases.py                  # Chạy toàn bộ pipeline 1 lần duy nhất
├── download_openmeteo_hcmc.py         # Tải dữ liệu từ API
│
├── hcmc_openmeteo_daily.csv           # Dữ liệu thô theo ngày
├── hcmc_openmeteo_hourly.csv          # Dữ liệu thô theo giờ
├── hcmc_openmeteo_monthly.csv         # Dữ liệu đã gộp theo tháng
│
├── phase1_rainfall_preprocessing.py   # Đọc & làm sạch dữ liệu
├── phase2_eda.py                      # Phân tích khám phá dữ liệu
├── phase3_feature_engineering.py      # Tạo các đặc trưng cho mô hình ML
├── phase4_modeling.py                 # Xây dựng 3 mô hình dự báo
├── phase5_feature_selection.py        # Chọn đặc trưng quan trọng
├── phase6_evaluation.py               # Đánh giá & so sánh mô hình
├── phase7_residual_diagnostics.py     # Kiểm tra sai số của mô hình tốt nhất
├── phase8_forecast.py                 # Dự báo 12 tháng tương lai
├── phase9_report_conclusions.py       # Tổng kết toàn bộ
│
├── output_fig_01.png ~ output_fig_23.png   # Các biểu đồ được lưu tự động
└── run_out.txt                             # Log toàn bộ output khi chạy
```

---

## Các bước thực hiện

### Bước 1 — Làm sạch dữ liệu (`phase1`)
Đọc file CSV, gộp dữ liệu ngày thành tháng, kiểm tra xem tháng nào bị thiếu số liệu. Bộ dữ liệu này may mắn là **không có tháng nào bị thiếu** nên không cần điền giá trị thay thế.

### Bước 2 — Phân tích dữ liệu (`phase2`)
Vẽ biểu đồ, tính thống kê mô tả, kiểm tra xem dữ liệu có tính mùa vụ rõ không. Kết quả: **mùa vụ rất mạnh** (chỉ số 0.852/1.0), chuỗi có tính dừng (không drift theo thời gian) — đây là điều kiện tốt để dự báo.

### Bước 3 — Tạo đặc trưng (`phase3`)
Từ dữ liệu lượng mưa và khí tượng lịch sử, tạo ra **105 đặc trưng** cho mô hình học máy, chia thành 6 nhóm:
- Thông tin về tháng (sin/cos để biểu diễn chu kỳ tròn)
- Lượng mưa của các tháng trước (lag 1, 2, 3, 6, 12, 24 tháng)
- Trung bình lượng mưa theo cửa sổ thời gian (3, 6, 12, 24 tháng gần nhất)
- Lag và trung bình của 20 biến khí tượng

> Tất cả đặc trưng đều chỉ dùng dữ liệu **quá khứ**, tuyệt đối không dùng dữ liệu của tháng đang cần dự báo để tránh gian lận (data leakage).

### Bước 4 — Xây dựng mô hình (`phase4`)
Ba mô hình được xây dựng — xem giải thích chi tiết ở phần dưới.

### Bước 5 — Chọn đặc trưng (`phase5`)
Dùng tương quan và Random Forest để xếp hạng 105 đặc trưng, chọn ra top 10 quan trọng nhất để báo cáo. Đặc trưng quan trọng nhất là `rain_lag_36` (lượng mưa cùng tháng 3 năm trước) với mức ảnh hưởng 39.6%.

### Bước 6 — Đánh giá mô hình (`phase6`)
So sánh 3 mô hình trên 24 tháng dữ liệu thực tế mà mô hình chưa được thấy. Ngoài ra còn chạy **Rolling-Origin CV** — chia nhiều cửa sổ kiểm tra khác nhau để chắc chắn mô hình không chỉ may mắn trên một giai đoạn.

### Bước 7 — Kiểm tra sai số (`phase7`)
Nhìn vào phần sai số của mô hình được chọn: sai số có ngẫu nhiên không, hay có quy luật bị bỏ sót? Kiểm định Ljung-Box cho thấy **sai số ngẫu nhiên** → mô hình đã nắm bắt được hết cấu trúc chính.

### Bước 8 — Dự báo (`phase8`)
Cho mô hình học lại toàn bộ 569 tháng rồi dự báo 12 tháng tiếp theo (06/2026 – 05/2027).

### Bước 9 — Tổng kết (`phase9`)
In báo cáo đầy đủ gồm: tóm tắt dữ liệu, nhận xét EDA, bảng so sánh mô hình, kết quả dự báo, hạn chế và hướng phát triển.

---

## Ba mô hình được dùng

### Mô hình 1 — Seasonal Mean (Baseline — mức tham chiếu)

**Cách hoạt động:** Cực kỳ đơn giản — với mỗi tháng cần dự báo, chỉ lấy **trung bình lịch sử của đúng tháng đó** trong toàn bộ dữ liệu quá khứ. Ví dụ dự báo tháng 6/2026 thì lấy trung bình của tất cả tháng 6 từ 1979 đến 2024.

**Lý do có mặt:** Đây là mức sàn — nếu mô hình phức tạp hơn mà không thắng được cái này thì không đáng dùng. Mô hình này không học gì cả, chỉ ghi nhớ trung bình.

**Kết quả:** RMSE = 74.42 mm — tệ nhất trong 3 mô hình, nhưng không quá xa, chứng tỏ tính mùa vụ là yếu tố chính chi phối lượng mưa.

---

### Mô hình 2 — Holt-Winters (Mô hình thống kê — được chọn làm mô hình chính)

**Cách hoạt động:** Mô hình nhìn vào **xu hướng** (lượng mưa đang tăng hay giảm dài hạn) và **mùa vụ** (tháng nào thường mưa nhiều, tháng nào ít) rồi kết hợp cả hai để dự báo. Nó dùng kỹ thuật "làm mịn theo hàm mũ" — tức là dữ liệu gần đây được coi trọng hơn dữ liệu xa xưa, thay vì cho tất cả trọng số bằng nhau.

Cụ thể trong code:
```python
ExponentialSmoothing(
    train,
    trend="add",        # có thành phần xu hướng cộng
    seasonal="add",     # có thành phần mùa vụ cộng
    seasonal_periods=12 # chu kỳ 12 tháng
).fit(optimized=True)   # tự động tìm tham số tốt nhất
```

**Lý do chọn làm mô hình chính:**
- CV-RMSE tốt nhất trong 3 mô hình: **65.87 mm** qua 6 cửa sổ kiểm tra khác nhau
- Ổn định — độ lệch chuẩn thấp (16.73), nghĩa là không bị may mắn ở một giai đoạn rồi tệ ở giai đoạn khác
- Dễ giải thích — mô hình thống kê cổ điển, dễ trình bày trong báo cáo học thuật
- Phù hợp với dữ liệu mùa vụ mạnh (season strength = 0.852)

**Kết quả hold-out 24 tháng:** RMSE = 62.72 mm, WAPE = 26.64%

---

### Mô hình 3 — Random Forest Weather (Mô hình học máy)

**Cách hoạt động:** Xây dựng **300 cây quyết định** song song, mỗi cây học từ một mẫu ngẫu nhiên khác nhau của dữ liệu. Kết quả cuối là trung bình dự báo của tất cả 300 cây. Mỗi cây nhìn vào 138 đặc trưng (lượng mưa các tháng trước + các chỉ số khí tượng) để đưa ra quyết định.

Quá trình dự báo từng bước:
1. Nhìn vào lịch sử lượng mưa và khí tượng đã biết
2. Vì không có dữ liệu khí tượng tương lai thật, dùng **trung bình cùng tháng từ lịch sử** thay thế (ví dụ: dự báo tháng 6 thì dùng trung bình nhiệt độ, độ ẩm... của tất cả các tháng 6 trong quá khứ)
3. Sau khi dự báo xong tháng này, kết quả đó được thêm vào lịch sử để dự báo tháng tiếp theo

Cụ thể trong code:
```python
RandomForestRegressor(
    n_estimators=300,      # 300 cây
    max_depth=8,           # mỗi cây tối đa 8 tầng sâu
    min_samples_leaf=5,    # mỗi lá cần ít nhất 5 mẫu, tránh học tủ
    random_state=42,
    n_jobs=-1              # dùng toàn bộ CPU để chạy song song
)
```

**Lý do có mặt:** Đại diện cho nhóm học máy, cho thấy rằng kể cả khi thêm nhiều biến khí tượng vào, mô hình phức tạp không nhất thiết thắng mô hình thống kê đơn giản hơn.

**Kết quả hold-out 24 tháng:** RMSE = 73.60 mm — kém hơn Holt-Winters, nhưng CV-RMSE (68.82 mm) vẫn ổn định.

---

## Kết quả so sánh

### Trên 24 tháng thực tế chưa thấy (hold-out)

| Mô hình | Sai số TB tuyệt đối | RMSE | WAPE |
|---|---|---|---|
| **Holt-Winters** | 53.17 mm | **62.72 mm** | 26.64% |
| Random Forest Weather | 61.18 mm | 73.60 mm | 30.65% |
| Seasonal Mean | 58.83 mm | 74.42 mm | 29.47% |

### Trên 6 cửa sổ kiểm tra khác nhau (Rolling-Origin CV — đáng tin hơn)

| Mô hình | CV-RMSE trung bình | Độ lệch |
|---|---|---|
| **Holt-Winters** | **65.87 mm** | 16.73 |
| Random Forest Weather | 68.82 mm | 17.10 |
| Seasonal Mean | 73.80 mm | 13.99 |

> **Tại sao dùng Rolling-Origin CV thay vì chỉ nhìn hold-out?**
> Hold-out chỉ kiểm tra mô hình trên **một giai đoạn duy nhất** (06/2024–05/2026). Nếu giai đoạn đó tình cờ dễ dự báo thì kết quả sẽ đẹp giả tạo. Rolling-Origin CV chia thành **6 cửa sổ khác nhau** rải đều từ 2020 đến 2026, mô hình nào thắng ở đây mới thực sự đáng tin.

---

## Dự báo 12 tháng (06/2026 – 05/2027)

Dùng Holt-Winters fit lại trên toàn bộ 569 tháng:

| Tháng | Dự báo | Khoảng tin cậy 95% |
|---|---|---|
| 06/2026 | 288 mm | [188 – 389] |
| 07/2026 | 302 mm | [201 – 403] |
| 08/2026 | 311 mm | [210 – 412] |
| **09/2026** | **353 mm** | [252 – 454] |
| 10/2026 | 306 mm | [205 – 406] |
| 11/2026 | 174 mm | [73 – 275] |
| 12/2026 | 92 mm | [0 – 192] |
| 01/2027 | 55 mm | [0 – 156] |
| **02/2027** | **47 mm** | [0 – 148] |
| 03/2027 | 59 mm | [0 – 160] |
| 04/2027 | 109 mm | [8 – 210] |
| 05/2027 | 240 mm | [139 – 341] |

**Tổng dự báo cả năm: 2335 mm** — tháng 9/2026 mưa nhiều nhất, tháng 2/2027 ít nhất. Hoàn toàn phù hợp với đặc trưng khí hậu nhiệt đới gió mùa của TP.HCM.

---

## Cách chạy

**Yêu cầu:**
```
Python >= 3.10
pandas, numpy, matplotlib, statsmodels, scikit-learn, pmdarima
```

**Cài thư viện:**
```bash
pip install pandas numpy matplotlib statsmodels scikit-learn pmdarima seaborn
```

**Chạy toàn bộ:**
```bash
python run_all_phases.py
```

Khi chạy xong, các biểu đồ sẽ được lưu tự động ra `output_fig_01.png` đến `output_fig_23.png`. Không cần mở từng file phase riêng — `run_all_phases.py` lo hết.

**Tải lại dữ liệu mới từ API (nếu cần):**
```bash
python download_openmeteo_hcmc.py
```

---

## Hạn chế

- Dữ liệu reanalysis có thể sai lệch so với trạm đo thực tế
- Mô hình Random Forest không dùng được dữ liệu khí tượng tương lai thật nên phải dùng trung bình lịch sử thay thế — điều này làm giảm lợi thế của nó so với lý thuyết
- Sai số dự báo ~65 mm vẫn còn khá cao — mưa bị ảnh hưởng nhiều bởi các hiện tượng đối lưu cục bộ khó mô hình hóa

## Hướng cải thiện

- Thêm dữ liệu ENSO (El Niño / La Niña) — ảnh hưởng rõ đến lượng mưa TP.HCM
- Nếu có dự báo khí tượng tháng tới từ cơ quan khí tượng, dùng trực tiếp làm đầu vào cho mô hình
- Thử thêm mô hình LSTM (deep learning) để so sánh

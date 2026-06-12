# Dự án: Phân tích và dự báo lượng mưa trung bình tháng tại TP. Hồ Chí Minh

## 1. Dự án này làm gì

Nói ngắn gọn: lấy số liệu thời tiết gần **50 năm** (1979–2026) của TP.HCM, rồi:
- Xem lượng mưa "lên xuống" theo tháng/theo mùa như thế nào — có quy luật gì không.
- Thử 4 cách dự báo khác nhau, "đấu" với nhau để xem cách nào đoán đúng hơn.
- Dùng cách thắng để dự báo lượng mưa cho **12 tháng tới** (06/2026 → 05/2027).

### Kết quả nhanh (xem chi tiết ở mục 8)

- **569 tháng dữ liệu** (01/1979 → 05/2026), 100% đầy đủ, không phải đoán bù.
- **Lượng mưa trung bình**: 162.3 mm/tháng (thấp nhất 0.0, cao nhất 473.5). Mùa vụ rất mạnh (0.854/1): đỉnh điểm Tháng 9 (325.77mm), thấp điểm Tháng 2 (12.30mm).
- **SARIMAX** là mô hình dự báo tốt nhất trong 4 mô hình thử nghiệm (sai số ~59-68mm/tháng, ~25.5%).
- **Dự báo 12 tháng tới (06/2026-05/2027)**: tổng 1955.3mm, đỉnh Tháng 9/2026 (327.48mm), đáy Tháng 2/2027 (13.53mm).

---

## 2. Vì sao lại chọn đề tài này

- **Sát với cuộc sống thật**: Sài Gòn cứ đến mùa mưa (T5-T11) là dễ ngập, còn mùa khô (T12-T4) thì có lúc lại thiếu nước. Nếu biết trước tháng nào mưa nhiều/ít, người ta có thể chuẩn bị sớm hơn — chống ngập, trữ nước, lên kế hoạch trồng trọt...
- **Có dữ liệu sẵn, dài, miễn phí**: Open-Meteo cho 47 năm dữ liệu liên tục, không tốn tiền. Dữ liệu dài như vậy mới đủ để nhìn ra xu hướng thật và kiểm tra mô hình một cách đáng tin, không phải "đoán mò".
- **Bài toán vừa đủ "khó"**: mưa ở đây theo mùa rất rõ, nhưng từng năm cũng lệch nhau khá nhiều — không quá dễ để chỉ cần 1 công thức đơn giản là xong, nhưng cũng không hỗn loạn đến mức không đoán được gì. Đây là kiểu bài toán hợp lý để so sánh nhiều cách dự báo (từ thống kê cổ điển đến machine learning) và xem cách nào hợp với kiểu dữ liệu này.
- **Có nhiều biến thời tiết đi kèm** (độ ẩm, mây, nhiệt độ, áp suất...) — vừa để xem cái gì "báo hiệu" mưa, vừa có thể dùng làm thông tin hỗ trợ cho mô hình dự báo.

---

## 3. Dữ liệu dùng trong dự án

### 3.1. Dữ liệu lấy từ đâu

- Nguồn: **Open-Meteo**, dùng dữ liệu **ERA5** — đây là dữ liệu được "tính toán lại" từ vệ tinh kết hợp mô hình khí hậu toàn cầu, **không phải số đo trực tiếp từ một trạm khí tượng cụ thể**. Vì vậy có thể hơi khác với số đo thực tế tại một điểm nào đó trong thành phố, nhưng xu hướng chung (mùa nào mưa nhiều/ít) thì vẫn phản ánh đúng.
- Khoảng thời gian: **01/1979 → 05/2026**, tổng **569 tháng**.
- Vì TP.HCM khá rộng, dữ liệu được lấy ở **7 điểm khác nhau** rải khắp thành phố (trung tâm Q1/Q3, Củ Chi, Thủ Đức, Bình Chánh, Nhà Bè, Q9, Tân Bình), sau đó **lấy trung bình của 7 điểm** mỗi ngày để ra một con số đại diện chung cho cả thành phố.

### 3.2. Cái cần dự báo là gì

- **Rainfall (lượng mưa trung bình tháng)** — đơn vị mm/tháng.
- Cách tính: mỗi ngày tính mưa trung bình của 7 điểm → cộng tất cả các ngày trong tháng → ra lượng mưa của tháng đó.
- Đây chính là con số mà cả 4 mô hình trong dự án đang cố gắng đoán cho 12 tháng tới.

### 3.3. Toàn bộ 26 cột dữ liệu — từng cột nghĩa là gì

Mỗi tháng có 26 cột số liệu: 1 cột thời gian, 1 cột mục tiêu (Rainfall), 21 cột thời tiết, và 4 cột để kiểm tra chất lượng dữ liệu.

**Cột thời gian:**
- `Date` — Tháng/năm của dòng dữ liệu (ví dụ 2026-05-01 nghĩa là tháng 5/2026).

**Cột mục tiêu — cái cần dự báo:**
- `Rainfall` — Lượng mưa trung bình tháng (mm/tháng).

**Nhóm mưa/nước:**
- `Precipitation` — Tổng lượng mưa và các dạng giáng thủy khác trong tháng (mm). Ở TP.HCM gần như chỉ là mưa, nên số này khá gần với Rainfall, chỉ là Open-Meteo tính theo công thức khác.
- `PrecipitationHours` — Tổng số giờ có mưa trong tháng. Biến này "ăn theo" lượng mưa rất sát (tương quan 0.97) — tháng nào mưa nhiều giờ thì lượng mưa cũng nhiều, gần như chắc chắn.
- `Evapotranspiration` — Tổng lượng nước "bốc hơi" khỏi đất và cây trong tháng (mm). Phản ánh độ khô của đất/không khí.

**Nhóm nhiệt độ:**
- `TempMean` — Nhiệt độ không khí trung bình trong tháng (°C).
- `TempMin` — Trung bình của nhiệt độ thấp nhất mỗi ngày trong tháng (°C).
- `TempMax` — Trung bình của nhiệt độ cao nhất mỗi ngày trong tháng (°C).
- `ApparentTempMean` — Nhiệt độ "cảm nhận được" (có tính cả độ ẩm, gió) — gần với cảm giác nóng/lạnh thật của con người hơn là số trên nhiệt kế.

**Nhóm gió:**
- `WindSpeedMax` — Tốc độ gió mạnh nhất trung bình trong tháng (km/h).
- `WindGustMax` — Tốc độ gió giật (cơn gió mạnh bất ngờ) lớn nhất trung bình trong tháng (km/h).
- `WindSpeedHourlyMean` — Tốc độ gió trung bình, tính từ dữ liệu theo từng giờ (km/h).
- `WindGustHourlyMean` — Tốc độ gió giật trung bình, tính từ dữ liệu theo từng giờ (km/h).

**Nhóm độ ẩm:**
- `HumidityMean` — Độ ẩm không khí trung bình trong tháng (%). Đi khá sát với mưa (tương quan 0.886) — không khí ẩm hơn thì thường mưa nhiều hơn.
- `HumidityMax` — Độ ẩm không khí cao nhất trong tháng (%).
- `DewPointMean` — Điểm sương trung bình (°C). Hiểu nôm na: số này càng cao thì không khí đang "ngậm" càng nhiều hơi nước, dễ ngưng tụ thành mưa. Tương quan với mưa: 0.824.

**Nhóm áp suất không khí:**
- `PressureMSLMean` — Áp suất không khí trung bình, quy đổi về mực nước biển (hPa).
- `SurfacePressureMean` — Áp suất không khí trung bình tại mặt đất (hPa). Biến này có quan hệ **ngược chiều** với mưa (-0.721) — áp suất thấp thường đi cùng thời tiết xấu, dễ mưa nhiều.

**Nhóm mây — nhóm ảnh hưởng rõ nhất đến mưa:**
- `CloudCoverMean` — Tỷ lệ mây che phủ trung bình toàn bầu trời (%). Tương quan với mưa: 0.839.
- `CloudCoverLowMean` — Tỷ lệ mây tầng thấp, gần mặt đất (%). Tương quan: 0.722.
- `CloudCoverMidMean` — Tỷ lệ mây tầng giữa (%). Tương quan: 0.739.
- `CloudCoverHighMean` — Tỷ lệ mây tầng cao (%). Tương quan cao nhất trong nhóm mây: 0.842.

**Nhóm năng lượng mặt trời:**
- `ShortwaveRadiation` — Tổng năng lượng ánh nắng chiếu xuống mặt đất trong tháng. Tháng nào nhiều mây/mưa thì số này thường thấp hơn.

**Nhóm kiểm tra chất lượng dữ liệu (không phải số liệu thời tiết):**
- `RainfallDays` — Số ngày trong tháng có dữ liệu mưa hợp lệ.
- `ExpectedDays` — Số ngày thực tế của tháng đó (28-31 ngày).
- `Completeness` — Tỷ lệ đầy đủ dữ liệu = RainfallDays / ExpectedDays. Trong dự án này, **tất cả các tháng đều đạt 100%** — không có tháng nào thiếu hay phải tự đoán bù.
- `ValidHourlyRows` — Số dòng dữ liệu theo giờ hợp lệ trong tháng (dùng để tính các số trung bình theo giờ như độ ẩm, mây...).

> **Tóm lại**: 21 biến thời tiết (mưa/nước, nhiệt độ, gió, độ ẩm, áp suất, mây, năng lượng mặt trời) + 1 biến mục tiêu (Rainfall) + 4 cột kiểm tra chất lượng dữ liệu = 26 cột.

---

## 4. Mỗi cột dữ liệu được dùng vào việc gì — phân tích hay dự đoán?

Dự án có 2 loại câu hỏi khác nhau, và mỗi loại dùng dữ liệu theo cách khác nhau:
- **(A) Phân tích/giải thích**: tháng nào mưa nhiều, vì sao lại thế?
- **(B) Dự đoán**: tháng tới sẽ mưa bao nhiêu?

### (A) Dùng để phân tích, giải thích (Phase 2 - EDA)

Ở phần này, các cột được dùng **trực tiếp, cùng tháng** để xem yếu tố nào "đi cùng" với mưa nhiều/ít:

- `Rainfall` — dùng để tính trung bình, độ lệch, vẽ biểu đồ theo mùa, kiểm tra có xu hướng tăng/giảm dài hạn không.
- `PrecipitationHours`, `HumidityMean`, `CloudCoverHighMean`, `CloudCoverMean`, `DewPointMean`, `CloudCoverMidMean`, `CloudCoverLowMean`, `SurfacePressureMean` — dùng để tính mức độ "đi cùng nhau" (tương quan) với Rainfall, trả lời câu "tháng nào mưa nhiều thường kèm theo điều gì". Đây chỉ là **quan sát/mô tả** — không đưa trực tiếp vào mô hình dự báo, vì đây là số liệu *cùng tháng* (nếu dùng sẽ thành "gian lận", vì thực tế không ai biết trước thời tiết tháng tới sẽ ra sao).
- `Date` — dùng để nhóm theo tháng (1-12), tính độ mạnh mùa vụ, vẽ biểu đồ theo mùa.

### (B) Dùng để dự đoán bằng mô hình (Phase 3, 4)

Vì không ai biết trước thời tiết tháng sau, nên **không được dùng số liệu thời tiết của chính tháng đang dự báo**. Thay vào đó:

- `Rainfall` của **các tháng trước** → tạo ra các cột như "mưa tháng trước", "mưa cùng kỳ năm ngoái", "trung bình mưa 3/6/12 tháng gần nhất"... (tổng 15 cột). Đây là nhóm thông tin **quan trọng nhất**, vì mưa tháng này phụ thuộc rất nhiều vào mưa các tháng/năm trước.
- 21 biến thời tiết còn lại → mỗi biến cũng có phiên bản "tháng trước" và "trung bình trượt nhiều tháng trước" (tổng 80 cột). Các biến có tương quan cao ở phần (A) — số giờ mưa, độ ẩm, mây, điểm sương... — thường mang ảnh hưởng mạnh nhất.
- `Date` → tạo các cột tháng/năm và các cột dạng sóng (sin/cos), giúp mô hình "hiểu" được tháng 12 và tháng 1 thực ra liền kề nhau (lặp lại theo vòng 12 tháng).
- Riêng mô hình **SARIMAX** chỉ chọn ra 6 biến thời tiết (của tháng trước) để hỗ trợ: HumidityMean, CloudCoverMean, DewPointMean, PrecipitationHours, TempMean, ShortwaveRadiation — đây là những biến có quan hệ chặt với mưa và mang được thông tin "báo hiệu trước" hữu ích.
- 4 cột kiểm tra chất lượng (RainfallDays, ExpectedDays, Completeness, ValidHourlyRows) **không dùng để dự báo** — chỉ dùng ở bước đầu để xem dữ liệu có đáng tin không.

### Tóm tắt nhanh

| Mục đích | Cột dùng | Cách dùng |
|---|---|---|
| Phân tích/giải thích | Rainfall + 8 biến đi cùng mưa (cùng tháng) | Tính tương quan, vẽ biểu đồ, kiểm tra xu hướng |
| Kiểm tra chất lượng dữ liệu | RainfallDays, ExpectedDays, Completeness, ValidHourlyRows | Chỉ dùng ở bước đầu, không đưa vào mô hình |
| Dự đoán (mô hình) | Rainfall + 21 biến thời tiết (lấy của các tháng trước) + Date | Tạo 105 cột đầu vào, huấn luyện 4 mô hình |

### 3.4. Quy mô dữ liệu — vài con số cho dễ tưởng tượng

- **Dữ liệu gốc**: 569 tháng × 26 cột (01/1979 → 05/2026).
- **Dữ liệu theo ngày** (trước khi gộp theo tháng): 17.318 ngày, mỗi ngày là trung bình của 7 điểm tọa độ.
- **Sau khi tạo các cột phục vụ dự báo**: còn **533 tháng × 105 cột**. Mất 24 tháng đầu vì các cột "trượt 24 tháng" cần có đủ 24 tháng trước đó mới tính được. Khoảng thời gian còn lại: 01/1982 → 05/2026.
- **Chia dữ liệu để kiểm tra mô hình**: 545 tháng để "học" (01/1979 → 05/2024) và 24 tháng để "thi" — kiểm tra dự báo có đúng không (06/2024 → 05/2026). Tức khoảng 96% học / 4% kiểm tra.
- **Kiểm tra nhiều lần (Rolling CV)**: để chắc chắn kết quả không phải may rủi, dự án còn kiểm tra thêm **6 lần** trên 6 giai đoạn 12 tháng khác nhau (từ 2020 đến 2026).
- **Dự báo tương lai**: 12 tháng (06/2026 → 05/2027), mỗi tháng có 3 số (dự báo, mức thấp nhất có thể, mức cao nhất có thể) cho từng mô hình.
- **Đơn vị các nhóm số liệu chính**:
  - Lượng mưa, lượng bốc hơi, năng lượng mặt trời: milimét (mm) hoặc MJ/m².
  - Nhiệt độ, điểm sương: độ C (°C).
  - Độ ẩm, mây, độ đầy đủ dữ liệu: phần trăm (0-100%).
  - Áp suất không khí: hPa, dao động quanh 1000-1015.
  - Tốc độ gió: km/h.
  - Số giờ mưa: giờ (0 đến khoảng 744 giờ/tháng).
- **Vậy có cần "đưa các số về cùng thang đo" (chuẩn hóa/scale) không?** Các cột trong dữ liệu có độ lớn rất khác nhau (áp suất ~1000, độ ẩm 0-100%, mưa 0-473mm, năng lượng hàng trăm-nghìn). Nhưng 3 mô hình dùng trong dự án (SARIMAX, Prophet, XGBoost) đều **không cần** chuẩn hóa trước: SARIMAX/Prophet làm việc trực tiếp trên chuỗi mưa, còn XGBoost (dựa trên cây quyết định) chỉ chia dữ liệu theo từng ngưỡng nên không bị ảnh hưởng bởi độ lớn khác nhau giữa các cột. Vì vậy dự án **không có bước chuẩn hóa số liệu** — nhưng nếu sau này thử các mô hình khác (ví dụ mạng neural), đây sẽ là bước cần làm thêm.

---

## 5. Các bước thực hiện — đi qua từng phase một

Toàn bộ chạy qua file `run_all_phases.py`, gồm 8 bước nối tiếp nhau, mỗi bước làm xong sẽ "truyền" kết quả cho bước sau.

### Phase 1 — Kiểm tra & dọn dữ liệu

Bước đầu tiên, đơn giản nhưng quan trọng: đọc file `hcmc_openmeteo_monthly.csv` (569 tháng × 26 cột) và kiểm tra xem có tháng nào bị thiếu dữ liệu không — vì nếu dữ liệu "lủng lỗ" mà không biết, các bước sau sẽ tính sai mà không hay.

**Kết quả**: 569/569 tháng đều đủ dữ liệu, 0% phải tự đoán bù. Một vài số liệu nhanh: tháng mưa ít nhất = 0.0 mm, tháng mưa nhiều nhất = 473.5 mm, trung bình = 162.3 mm/tháng. Có 2 tháng hoàn toàn không mưa.

### Phase 2 — Tìm hiểu dữ liệu (EDA)

Đây là bước "làm quen" với dữ liệu trước khi đưa vào mô hình — giống như đọc lướt một cuốn sách trước khi phân tích sâu.

- Tính các số mô tả cơ bản: trung bình (162.3), độ lệch chuẩn (127.3), trung vị (168.6)...
- **Độ lệch (Skewness) = 0.206**: số liệu khá cân đối, không bị dồn hẳn về một phía.
- **Độ nhọn (Kurtosis) = -1.233**: phân phối "bẹt", ít có tháng nào mưa cực đoan bất thường.
- Tính mức độ "đi cùng nhau" giữa mưa và 21 biến thời tiết khác. Top các biến đi cùng mưa nhiều nhất:
  - Số giờ mưa (PrecipitationHours): 0.970
  - Độ ẩm (HumidityMean): 0.886
  - Mây tầng cao (CloudCoverHighMean): 0.842
  - Mây toàn phần (CloudCoverMean): 0.839
  - Điểm sương (DewPointMean): 0.824
  - Mây tầng giữa (CloudCoverMidMean): 0.739
  - Mây tầng thấp (CloudCoverLowMean): 0.722
  - Áp suất mặt đất (SurfacePressureMean): -0.721 (đi ngược chiều — áp suất thấp thì mưa nhiều)
- Kiểm tra xem chuỗi mưa có "trôi" dần theo thời gian không (tăng dần hoặc giảm dần qua nhiều năm), bằng 2 phép kiểm tra thống kê:
  - **ADF**: kết quả cho thấy **không có xu hướng tăng/giảm dài hạn rõ rệt** (số liệu: -4.6186, p-value 0.0001).
  - **KPSS**: cho kết quả tương tự (số liệu: 0.2042, p-value 0.10).
  - Hai kiểm tra "đồng thuận" với nhau → mưa ở TP.HCM lên xuống theo mùa nhưng không tăng/giảm dần đều qua 47 năm — tức là khí hậu mưa ở đây khá ổn định về lâu dài (chưa thấy dấu hiệu "ngày càng mưa nhiều hơn" hay ngược lại).
- Phát hiện về mùa:
  - Tháng mưa nhiều nhất trung bình: **Tháng 9** (325.77 mm/tháng).
  - Tháng mưa ít nhất trung bình: **Tháng 2** (12.30 mm/tháng).
  - **Độ mạnh mùa vụ = 0.854** (thang 0-1) → tính theo mùa **rất mạnh**. Gần như toàn bộ sự lên xuống của lượng mưa là do mùa mưa (T5-T11) và mùa khô (T12-T4), không phải ngẫu nhiên.
- Tạo ra 7 biểu đồ minh họa (`output_fig_01` đến `07`): biểu đồ tương quan, lượng mưa theo thời gian, lượng mưa theo tháng, phân phối theo tháng, phân rã xu hướng/mùa vụ, ACF/PACF, và biểu đồ theo mùa qua các năm gần đây.

### Phase 3 — Tạo các cột dữ liệu phục vụ dự báo (Feature Engineering)

Đây là bước "dịch" lịch sử thành ngôn ngữ mà mô hình hiểu được. Từ 26 cột gốc, dự án tạo ra **105 cột mới**, chia làm 6 nhóm:

- **Nhóm thời gian (4 cột)**: tháng, năm, và 1 chỉ số thời gian tăng dần (1, 2, 3...).
- **Nhóm "sóng" theo mùa — Fourier (6 cột)**: các cột dạng sin/cos giúp mô hình hiểu tháng 12 và tháng 1 thực ra liền kề nhau (lặp theo vòng 12 tháng).
- **Mưa của các tháng trước (7 cột)**: mưa của 1, 2, 3, 6, 9, 12, 24 tháng trước.
- **Trung bình/tổng mưa trượt (8 cột)**: trung bình hoặc tổng mưa của 3, 6, 12 tháng gần nhất (tính từ tháng trước, không gồm tháng đang xét).
- **Thời tiết các tháng trước (40 cột)**: mỗi biến thời tiết (21 biến) lấy giá trị của 1 tháng trước và 12 tháng trước.
- **Trung bình thời tiết trượt (40 cột)**: trung bình của mỗi biến thời tiết trong 3 và 12 tháng gần nhất (tính từ tháng trước).

**Nguyên tắc "chống gian lận"**: tất cả số liệu thời tiết đưa vào mô hình chỉ lấy từ **các tháng đã qua**, không bao giờ dùng số liệu của chính tháng đang dự báo — vì thực tế lúc dự báo, ta chưa biết trước thời tiết tháng tới sẽ ra sao.

Sau khi bỏ các dòng đầu bị thiếu (do cần đủ 24 tháng trước để tính), còn lại **533 tháng** (01/1982 → 05/2026) để huấn luyện mô hình.

**Vì sao phải làm phức tạp như vậy?** Mô hình máy tính không "nhìn" lịch sử theo cách tự nhiên như con người — nó cần được "kể lại" lịch sử dưới dạng các cột số cụ thể (mưa tháng trước, trung bình 3 tháng gần nhất...). Trên thực tế, việc tạo ra các cột này có tốt hay không thường ảnh hưởng đến độ chính xác dự báo nhiều hơn cả việc chọn mô hình nào.

### Phase 4 — Xây dựng 4 cách dự báo và để chúng "đấu" với nhau

Trước tiên, chia dữ liệu: **545 tháng để học** (01/1979 → 05/2024) và **24 tháng để thi** — tức làm bài kiểm tra mà mô hình chưa từng thấy (06/2024 → 05/2026, 2 năm gần nhất).

4 "thí sinh" được đưa vào thi:

1. **Seasonal Naive** — thí sinh "lười" nhất, đơn giản nhất: dự báo tháng này = **giá trị thật của cùng tháng năm trước**. Đây đóng vai trò "đường chuẩn" — nếu các cách phức tạp hơn không thắng được thí sinh lười này thì coi như không đáng công xây dựng.
   - Sai số (RMSE): 66.96 mm/tháng.

2. **SARIMAX** — mô hình thống kê chuyên về chuỗi thời gian có mùa vụ, có thêm "trợ lý" là vài biến thời tiết.
   - Máy tính tự tìm ra công thức phù hợp nhất: dùng 3 tháng gần nhất + 1 thành phần lặp lại theo mùa 12 tháng.
   - Có thêm 6 biến thời tiết của tháng trước hỗ trợ: độ ẩm, mây, điểm sương, số giờ mưa, nhiệt độ, năng lượng mặt trời.
   - Sai số (RMSE): **59.47 mm/tháng** — thấp nhất, tức là thắng.

3. **Prophet** — mô hình chuyên về chuỗi thời gian do Meta/Facebook phát triển, nổi tiếng giỏi xử lý dữ liệu có tính mùa vụ.
   - Sai số (RMSE): 66.69 mm/tháng.

4. **XGBoost** — mô hình machine learning kiểu "cây quyết định", được giao toàn bộ 103 cột đã tạo ở Phase 3 để tự "mò".
   - Sai số (RMSE): 76.89 mm/tháng — về cuối trong 4 thí sinh.

**Vì sao XGBoost — nghe có vẻ "hiện đại" nhất — lại về cuối?**
- Dữ liệu chỉ có 533 tháng (~44 năm) — với machine learning thì đây là dữ liệu **khá ít**. XGBoost cần nhiều dữ liệu hơn để "học" tốt từ 103 cột đầu vào.
- Mưa TP.HCM có tính mùa vụ rất mạnh và khá đều đặn qua các năm (độ mạnh mùa vụ 0.854) — đúng kiểu bài toán mà mô hình chuyên về mùa vụ như SARIMAX có lợi thế "trời sinh".
- Với ít dữ liệu mà có tới 103 cột, XGBoost dễ "học vẹt" (nhớ chi tiết dữ liệu cũ quá mức) khiến nó dự báo dữ liệu mới kém ổn định hơn.

**Vì sao SARIMAX lại chọn công thức "3 tháng gần nhất + mùa vụ 12 tháng"?**
- "3 tháng gần nhất": mô hình nhìn vào 3 tháng vừa qua để đoán tháng tiếp theo — không cần xử lý gì thêm vì chuỗi mưa đã khá ổn định (theo kết quả ADF/KPSS ở Phase 2).
- "Mùa vụ 12 tháng": một phần liên hệ với cùng tháng năm trước (vì mưa lặp lại theo mùa), một phần để điều chỉnh sai số theo mùa.
- Công thức này không phải do con người chọn tay — máy tính tự thử nhiều công thức khác nhau và chọn ra cái phù hợp nhất với dữ liệu thực tế.

### Phase 5 — Soi kỹ hơn: so sánh chi tiết 4 cách dự báo

Bảng so sánh trên 24 tháng "thi":

| Mô hình | Sai số trung bình (MAE) | Sai số RMSE | Sai số % (WAPE) | Sai số % khác (sMAPE) | So với cách đơn giản (MASE) |
|---|---|---|---|---|---|
| SARIMAX | 52.64 | 59.47 | 25.53% | 48.71% | 0.9756 |
| Prophet | 55.48 | 66.69 | 26.91% | 41.51% | 1.0281 |
| Seasonal Naive | 57.58 | 66.96 | 27.93% | 72.27% | 1.0672 |
| XGBoost | 64.15 | 76.89 | 31.11% | 56.70% | 1.1888 |

Giải thích nhanh các con số này:
- **MAE**: sai số trung bình tính bằng mm/tháng — càng nhỏ càng tốt.
- **RMSE**: cũng tính bằng mm/tháng, nhưng "phạt nặng" hơn những lần sai số lớn — càng nhỏ càng tốt.
- **WAPE**: sai số tính theo phần trăm so với tổng lượng mưa thật — càng nhỏ càng tốt.
- **sMAPE**: một cách tính sai số % khác, xử lý tốt hơn khi có tháng mưa gần 0.
- **MASE**: so với thí sinh "lười" Seasonal Naive — nhỏ hơn 1 nghĩa là **tốt hơn** cách "copy y hệt năm trước".
- Ghi chú: không dùng chỉ số MAPE thông thường, vì một số tháng mùa khô mưa gần 0, khiến % sai số bị "nổ" lên rất lớn một cách không công bằng.

**Kiểm tra nhiều lần cho chắc (Rolling CV)**

Một lần kiểm tra 24 tháng có thể chỉ là "ăn may" hoặc "xui". Nên dự án kiểm tra lại trên **6 giai đoạn 12 tháng khác nhau**, từ 06/2020 đến 05/2026 (mỗi giai đoạn cách nhau 1 năm):

| Mô hình | Sai số trung bình (6 lần) | Độ dao động sai số | Sai số lần kiểm tra cuối |
|---|---|---|---|
| Seasonal Naive | 84.60 | 20.24 | 66.96 |
| SARIMAX | **68.23** | 14.17 | 59.47 |
| Prophet | 72.76 | 17.03 | 66.69 |
| XGBoost | 76.70 | 19.37 | 76.89 |

- **SARIMAX thắng cả 2 cách kiểm tra** → được chọn làm mô hình chính để dự báo 12 tháng tới.
- SARIMAX còn có **độ dao động sai số thấp nhất** (14.17), nghĩa là kết quả của nó **ổn định nhất** qua các năm — không có năm nào dự báo "trượt" quá nặng. Ngược lại, Seasonal Naive dao động nhiều nhất (20.24).
- So với thí sinh "lười" (Seasonal Naive, sai số 84.60), SARIMAX giảm sai số được khoảng **19.4%** (xuống 68.23) — đây là cải thiện thực sự, không phải chỉ nhờ "copy năm trước" mà ăn may.

**Sai số khác nhau giữa mùa mưa và mùa khô**

| Mô hình | RMSE chung | % sai số chung | RMSE mùa mưa | % sai số mùa mưa | RMSE mùa khô | % sai số mùa khô |
|---|---|---|---|---|---|---|
| SARIMAX | 59.5 | 25.5% | 69.5 | 19.8% | 41.5 | 71.8% |
| Prophet | 66.7 | 26.9% | 79.6 | 22.1% | 42.4 | 65.5% |
| Seasonal Naive | 67.0 | 27.9% | 74.2 | 21.0% | 55.2 | 83.5% |
| XGBoost | 76.9 | 31.1% | 91.9 | 26.0% | 48.5 | 71.7% |

Nhìn vào bảng này dễ "hốt hoảng" vì % sai số mùa khô cao gấp 3-4 lần mùa mưa (ví dụ SARIMAX: 71.8% vs 19.8%). Nhưng **đây không có nghĩa là mô hình tệ ở mùa khô** — mùa khô lượng mưa thật rất nhỏ (gần 0mm), nên chỉ cần lệch vài mm thôi cũng đủ tạo ra tỷ lệ % rất lớn. Nhìn vào số mm thực tế (RMSE) thì mùa khô vẫn sai ít hơn mùa mưa.

### Phase 6 — Kiểm tra "phần dư" của mô hình (Residual Diagnostics)

Sau khi mô hình dự báo xong, sẽ luôn có một khoảng chênh lệch giữa số thật và số dự báo — gọi là "phần dư" (residual). Câu hỏi đặt ra là: phần dư này có còn ẩn chứa quy luật nào mà mô hình "bỏ sót" không? Nếu còn, nghĩa là mô hình vẫn có thể cải thiện thêm.

Dùng phép kiểm tra thống kê Ljung-Box trên 24 phần dư của mỗi mô hình:

| Mô hình | Sai số trung bình (mean) | Độ dao động (std) | Kết quả kiểm tra |
|---|---|---|---|
| Seasonal Naive | 7.554 | 67.959 | Không còn quy luật rõ rệt |
| SARIMAX | 15.366 | 58.690 | Không còn quy luật rõ rệt |
| Prophet | 16.739 | 65.947 | Không còn quy luật rõ rệt |
| XGBoost | 37.384 | 68.635 | Không còn quy luật rõ rệt |

- Cả 4 mô hình đều "qua" kiểm tra — phần chênh lệch còn lại trông giống nhiễu ngẫu nhiên, không còn quy luật rõ rệt nào bị bỏ sót. Đây là dấu hiệu **tốt**, cho thấy mỗi mô hình đã khai thác hợp lý thông tin có trong dữ liệu.
- Một điểm đáng chú ý: SARIMAX có sai số trung bình dương (15.366), nghĩa là mô hình có xu hướng dự báo **thấp hơn thực tế một chút**, trung bình khoảng 15mm/tháng. Mức này khá nhỏ so với độ dao động lượng mưa thật (~127mm), nên vẫn ở mức chấp nhận được.
- Có 1 biểu đồ minh họa (`output_fig_11`) cho phần này.

### Phase 7 — Dự báo 12 tháng tới (06/2026 → 05/2027)

Đến phần "thực chiến": cả 4 mô hình được **học lại trên toàn bộ 569 tháng dữ liệu** (không chỉ phần học trước đó nữa) để tận dụng hết thông tin hiện có, rồi đưa ra dự báo cho 12 tháng tới.

Kết quả dự báo của mô hình thắng (**SARIMAX**), kèm khoảng "có thể dao động" (mức thấp nhất — mức cao nhất, với độ tin cậy 95%):

| Tháng | Dự báo (mm) | Mức thấp nhất | Mức cao nhất |
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
- **Tháng mưa nhiều nhất dự báo**: Tháng 9/2026 (327.48 mm).
- **Tháng mưa ít nhất dự báo**: Tháng 2/2027 (13.53 mm).
- Mức thấp nhất = 0.00 ở các tháng mùa khô vì tính ra số âm (không hợp lý, mưa không thể âm), nên được làm tròn về 0.

**Cách đọc bảng dự báo:**
- Mỗi tháng có 3 số: **Dự báo** (con số mô hình cho là khả năng cao nhất), **Mức thấp nhất / cao nhất** (khoảng mà mô hình "tin" giá trị thật sẽ rơi vào, với độ tin cậy 95%).
- Các tháng mùa mưa (06-10/2026) có khoảng dao động rộng (khoảng 150-300mm) — nghĩa là mô hình còn khá "không chắc" ở những tháng mưa nhiều, đúng với việc sai số tuyệt đối mùa mưa cao hơn mùa khô (đã thấy ở Phase 5).
- Các tháng mùa khô (11/2026-04/2027) có mức thấp nhất = 0 — nghĩa là khả năng tháng đó gần như không mưa, khớp với thực tế khí hậu TP.HCM.

**Dự báo có khớp với quy luật cũ không?**
- Dữ liệu cũ (Phase 2): tháng mưa nhiều nhất trung bình là **Tháng 9** (325.77mm) — dự báo cũng cho Tháng 9/2026 là tháng mưa nhiều nhất (327.48mm). **Khớp**.
- Dữ liệu cũ: tháng mưa ít nhất trung bình là **Tháng 2** (12.30mm) — dự báo cũng cho Tháng 2/2027 là tháng mưa ít nhất (13.53mm). **Khớp**.
- → SARIMAX đã "học" đúng quy luật mùa vụ đặc trưng của TP.HCM, không phải đưa ra số ngẫu nhiên.

**4 mô hình "nhìn" tương lai khác nhau thế nào?**
- Cả 4 mô hình khá đồng ý về **xu hướng** (tháng nào mưa nhiều, tháng nào ít) nhưng khác nhau về **con số cụ thể**.
- Seasonal Naive luôn cho số lớn nhất ở các tháng cao điểm — vì nó "copy y hệt" năm trước, không làm mượt gì cả. Ví dụ Tháng 9/2026, Seasonal Naive dự báo 473.5mm (chính là số thật của Tháng 9/2025), cao hơn nhiều so với SARIMAX (327.5mm).
- SARIMAX và Prophet cho kết quả gần nhau hơn ở các tháng mùa mưa, còn XGBoost thường cho số thấp hơn ở các tháng cao điểm.

Bảng so sánh dự báo của cả 4 mô hình cho 12 tháng:

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

Có 2 biểu đồ minh họa (`output_fig_12`, `output_fig_13`) cho phần dự báo này.

### Phase 8 — Tổng hợp lại toàn bộ kết quả

Bước cuối cùng, gom hết những gì đã làm ở các bước trên lại thành một bản tóm tắt:

1. **Tổng quan dữ liệu**: TP.HCM, 569 tháng (01/1979-05/2026), 21 biến thời tiết, nguồn ERA5.
2. **Đặc điểm theo thời gian**: mùa mưa T5-T11, mùa khô T12-T4, mưa nhiều nhất tháng 9, độ mạnh mùa vụ 0.854 (rất mạnh).
3. **Các biến thời tiết liên quan đến mưa**: số giờ mưa, độ ẩm, mây tầng cao, mây toàn phần, điểm sương, mây tầng giữa — đi cùng mưa nhiều nhất. Khi đưa vào mô hình dự báo, chỉ dùng số liệu của các tháng trước, không dùng số liệu cùng tháng (tránh "gian lận").
4. **So sánh 4 mô hình**: như bảng ở Phase 5 (mục 5).
5. **Mô hình được chọn**: SARIMAX (sai số kiểm tra nhiều lần 68.23, sai số kiểm tra 1 lần 59.47).
6. **Dự báo**: 06/2026-05/2027, tổng 1955.3mm, tháng mưa nhiều nhất 09/2026 (327.48mm), ít nhất 02/2027 (13.53mm).

**Những điều dự án này chưa làm được (hạn chế):**
- Dữ liệu Open-Meteo là tính toán lại (ERA5), có thể khác với số đo thực tế tại một điểm cụ thể.
- Không có số liệu thời tiết thật của tương lai — các mô hình chỉ dùng số liệu quá khứ để suy ra.
- Sai số dự báo theo mùa vẫn còn khá cao, vì mưa còn bị ảnh hưởng bởi các yếu tố khí hậu lớn (El Nino, La Nina...) mà mô hình hiện tại chưa tính đến.
- Lấy trung bình 7 điểm chỉ là cách xấp xỉ, chưa thể thay thế cho việc đo đạc dày đặc thực tế khắp thành phố.

**Nếu làm tiếp, có thể thử:**
- Thêm các chỉ số khí hậu lớn (El Nino/La Nina, nhiệt độ mặt biển...) để có thêm tín hiệu dự báo dài hạn.
- Nếu có dự báo thời tiết thật cho tháng tới, dùng làm thông tin hỗ trợ sẽ chính xác hơn.
- Kiểm tra thêm độ tin cậy của khoảng dự báo (mức thấp nhất/cao nhất) qua nhiều lần kiểm tra.
- Thử thêm các mô hình Deep Learning (LSTM, Transformer...) nếu có thêm dữ liệu.

---

## 6. Danh sách các file kết quả (biểu đồ)

- `output_fig_01.png` đến `output_fig_07.png`: biểu đồ tìm hiểu dữ liệu — tương quan, lượng mưa theo thời gian, theo tháng, phân phối, phân rã xu hướng/mùa vụ, ACF/PACF, theo mùa qua các năm.
- `output_fig_08.png`: biểu đồ chia dữ liệu học/kiểm tra.
- `output_fig_09.png`: biểu đồ so sánh 4 mô hình trên toàn bộ chuỗi thời gian.
- `output_fig_10.png`: biểu đồ so sánh 4 mô hình, phóng to vào tập kiểm tra.
- `output_fig_11.png`: biểu đồ kiểm tra phần dư của mô hình SARIMAX.
- `output_fig_12.png`, `output_fig_13.png`: biểu đồ dự báo 12 tháng của các mô hình.

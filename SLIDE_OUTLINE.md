# DỰ ÁN: PHÂN TÍCH & DỰ BÁO LƯỢNG MƯA TP. HỒ CHÍ MINH
### Khung nội dung báo cáo / slide (mỗi mục = 1 slide)

---

## SLIDE 1 — Mở đầu & Lý do chọn đề tài
- Tên đề tài: Phân tích và dự báo lượng mưa trung bình tháng tại TP. Hồ Chí Minh
- Dữ liệu: Open-Meteo (ERA5), 01/1979 → 05/2026, 569 tháng
- Mục tiêu: phân tích quy luật mưa + so sánh 4 mô hình dự báo + dự báo 12 tháng tới

**Lý do chọn đề tài:**
- TP.HCM thường ngập vào mùa mưa (T5-T11), thiếu nước cục bộ vào mùa khô (T12-T4)
- Dữ liệu 47 năm, miễn phí, đủ dài để phân tích xu hướng và kiểm tra mô hình đáng tin
- Mưa có tính mùa rất rõ nhưng vẫn nhiều biến động → phù hợp so sánh nhiều cách dự báo
- Có nhiều biến thời tiết liên quan (độ ẩm, mây, nhiệt độ, áp suất...) để khai thác

---

## SLIDE 2 — Dữ liệu sử dụng
- Nguồn: Open-Meteo Historical Weather API (dữ liệu tái phân tích ERA5)
- Không gian: trung bình 7 điểm tọa độ trải khắp TP.HCM (Q1/Q3, Củ Chi, Thủ Đức, Bình Chánh, Nhà Bè, Q9, Tân Bình)
- Quy mô: 569 tháng × 26 cột gốc → sau xử lý còn 533 tháng × 105 cột (đầu vào mô hình)
- Biến mục tiêu: **Rainfall** (lượng mưa trung bình tháng, mm/tháng)

**26 cột gốc gồm:**
- 1 cột thời gian (Date) + 1 cột mục tiêu (Rainfall)
- 21 biến thời tiết: mưa/nước (3), nhiệt độ (4), gió (4), độ ẩm (3), áp suất (2), mây (4), năng lượng mặt trời (1)
- 4 cột kiểm tra chất lượng dữ liệu (RainfallDays, ExpectedDays, Completeness, ValidHourlyRows)
- 100% các tháng đủ dữ liệu — không cần đoán bù

---

## SLIDE 3 — Biến nào ảnh hưởng đến mưa? (Tương quan)
Top biến đi cùng lượng mưa (tính trên 569 tháng, cùng tháng):

| Biến | Tương quan | Ý nghĩa |
|---|---|---|
| Số giờ mưa (PrecipitationHours) | 0.970 | Tháng nhiều giờ mưa → mưa nhiều |
| Độ ẩm (HumidityMean) | 0.886 | Không khí ẩm hơn → dễ mưa |
| Mây tầng cao (CloudCoverHighMean) | 0.842 | Mây cao nhiều → mưa nhiều |
| Mây toàn phần (CloudCoverMean) | 0.839 | Trời nhiều mây → mưa nhiều |
| Điểm sương (DewPointMean) | 0.824 | Không khí chứa nhiều hơi nước → dễ mưa |
| Mây tầng giữa (CloudCoverMidMean) | 0.739 | — |
| Mây tầng thấp (CloudCoverLowMean) | 0.722 | — |
| Áp suất mặt đất (SurfacePressureMean) | -0.721 | Áp suất thấp → thời tiết xấu, mưa nhiều |

**Hình ảnh chèn**: `output_fig_01.png` (biểu đồ cột tương quan các biến khí tượng với lượng mưa)

---

## SLIDE 4 — Đặc điểm theo mùa & xu hướng dài hạn
**Theo mùa:**
- Mùa mưa: Tháng 5 – Tháng 11 | Mùa khô: Tháng 12 – Tháng 4
- Tháng mưa nhiều nhất: **Tháng 9** (TB 325.77 mm/tháng)
- Tháng mưa ít nhất: **Tháng 2** (TB 12.30 mm/tháng)
- Độ mạnh mùa vụ: **0.854 / 1** → tính mùa vụ rất mạnh
- Trung bình chung: 162.3 mm/tháng (thấp nhất 0.0, cao nhất 473.5)

**Xu hướng dài hạn:**
- Kiểm tra ADF & KPSS: cả 2 đều cho thấy **không có xu hướng tăng/giảm dài hạn rõ rệt** qua 47 năm
- Mưa lên xuống theo mùa nhưng ổn định, không tăng/giảm dần
- Độ lệch (Skewness) = 0.206 → phân phối khá cân đối; Độ nhọn (Kurtosis) = -1.233 → ít tháng mưa cực đoan

**Hình ảnh chèn** (chọn 2-3 ảnh phù hợp, không cần dùng hết):
- `output_fig_02.png` — lượng mưa trung bình tháng theo thời gian 1979-2026 + trung bình động 12 tháng (cho thấy tính ổn định, không có xu hướng tăng/giảm dài hạn)
- `output_fig_03.png` — biểu đồ cột lượng mưa trung bình theo tháng (quy luật mùa vụ: T9 cao nhất, T2 thấp nhất)
- `output_fig_04.png` — boxplot phân phối lượng mưa theo tháng qua tất cả các năm (thể hiện độ dao động từng tháng)
- `output_fig_07.png` — seasonal plot: lượng mưa theo tháng qua các năm gần đây (2012-2026), so với trung bình 15 năm
- `output_fig_05.png` — phân rã chuỗi thời gian (xu hướng / mùa vụ / phần dư) — minh họa cho phần ADF/KPSS

---

## SLIDE 5 — Chuẩn bị dữ liệu cho mô hình (Feature Engineering)
Từ 26 cột gốc → tạo **105 cột đầu vào**, chia 6 nhóm:

| Nhóm | Số cột | Ví dụ |
|---|---|---|
| Thời gian | 4 | tháng, năm, chỉ số thời gian tăng dần |
| Sóng theo mùa (Fourier) | 6 | sin/cos chu kỳ 12 tháng |
| Mưa các tháng trước | 7 | mưa lag 1,2,3,6,9,12,24 tháng |
| Trung bình mưa trượt | 8 | TB/tổng mưa 3,6,12 tháng gần nhất |
| Thời tiết các tháng trước | 40 | mỗi biến (21) × lag 1 + lag 12 tháng |
| Trung bình thời tiết trượt | 40 | TB 3,12 tháng của mỗi biến (21) |

**Nguyên tắc quan trọng**: chỉ dùng số liệu của các tháng ĐÃ QUA — không dùng số liệu cùng tháng đang dự báo (tránh "gian lận" vì thực tế không biết trước thời tiết tháng tới). Sau khi bỏ 24 tháng đầu thiếu dữ liệu lag, còn lại 533 tháng (01/1982 → 05/2026).

**Hình ảnh chèn** (tùy chọn): `output_fig_06.png` — biểu đồ ACF/PACF của lượng mưa (giải thích vì sao chọn các lag 1, 12, 24 tháng làm đặc trưng)

---

## SLIDE 6 — 4 mô hình dự báo được so sánh
- Chia dữ liệu: **545 tháng học** (1979-2024) / **24 tháng kiểm tra** (2024-2026, ~96%/4%)

1. **Seasonal Naive** — dự báo = giá trị thật cùng tháng năm trước (đường chuẩn để so sánh)
2. **SARIMAX** — mô hình thống kê chuỗi thời gian theo mùa, công thức tự tìm ra: 3 tháng gần nhất + thành phần mùa vụ 12 tháng + 6 biến thời tiết tháng trước hỗ trợ (độ ẩm, mây, điểm sương, số giờ mưa, nhiệt độ, năng lượng mặt trời)
3. **Prophet** — mô hình chuyên về chuỗi thời gian theo mùa (Meta/Facebook)
4. **XGBoost** — machine learning kiểu cây quyết định, dùng toàn bộ 103 features

**Hình ảnh chèn**: `output_fig_08.png` (biểu đồ chia Train/Test — 24 tháng cuối làm tập kiểm tra)

---

## SLIDE 7 — Kết quả so sánh mô hình

**Kiểm tra 1 lần (24 tháng, 06/2024-05/2026):**

| Mô hình | RMSE (mm) | % sai số (WAPE) | So với cách đơn giản (MASE) |
|---|---|---|---|
| **SARIMAX** | **59.47** | **25.53%** | **0.98** |
| Prophet | 66.69 | 26.91% | 1.03 |
| Seasonal Naive | 66.96 | 27.93% | 1.07 |
| XGBoost | 76.89 | 31.11% | 1.19 |

**Kiểm tra nhiều lần (Rolling CV — 6 giai đoạn 12 tháng, 2020-2026):**

| Mô hình | Sai số TB (6 lần) | Độ dao động |
|---|---|---|
| **SARIMAX** | **68.23** | **14.17 (thấp nhất → ổn định nhất)** |
| Prophet | 72.76 | 17.03 |
| XGBoost | 76.70 | 19.37 |
| Seasonal Naive | 84.60 | 20.24 |

→ **SARIMAX thắng cả 2 cách kiểm tra**, cải thiện ~19.4% so với cách đơn giản nhất

**Hình ảnh chèn**:
- `output_fig_09.png` — so sánh dự báo 4 mô hình trên toàn bộ chuỗi thời gian (nhìn tổng quan)
- `output_fig_10.png` — so sánh dự báo 4 mô hình, phóng to vào tập kiểm tra (dễ thấy mô hình nào sát thực tế nhất)

---

## SLIDE 8 — Vì sao chọn SARIMAX? & Kiểm tra phần dư
**Vì sao SARIMAX tốt nhất:**
- Dữ liệu chỉ 533 tháng (~44 năm) — khá ít cho machine learning, XGBoost dễ "học vẹt" với 103 features
- Mưa TP.HCM có tính mùa vụ rất mạnh & đều đặn (0.854) → đúng "sở trường" của SARIMAX
- % sai số mùa khô cao (SARIMAX 71.8%) nhưng vì mưa thật gần 0mm — sai số tuyệt đối (mm) vẫn nhỏ hơn mùa mưa

**Kiểm tra phần dư (sai số còn lại, Ljung-Box trên 24 tháng):**

| Mô hình | Sai số TB còn lại (mm) | Kết quả |
|---|---|---|
| Seasonal Naive | 7.55 | Không còn quy luật |
| SARIMAX | 15.37 | Không còn quy luật |
| Prophet | 16.74 | Không còn quy luật |
| XGBoost | 37.38 | Không còn quy luật |

→ Cả 4 mô hình đều khai thác hợp lý dữ liệu, sai số còn lại giống nhiễu ngẫu nhiên (tốt)

**Hình ảnh chèn**: `output_fig_11.png` (3 biểu đồ: phần dư SARIMAX theo thời gian, histogram phần dư, ACF phần dư — minh họa phần dư không còn quy luật)

---

## SLIDE 9 — Dự báo 12 tháng tới (06/2026 – 05/2027)

| Tháng | Dự báo (mm) | Khoảng dao động |
|---|---|---|
| 06/2026 | 248.2 | 97 – 399 |
| 07/2026 | 270.9 | 120 – 422 |
| 08/2026 | 280.4 | 130 – 431 |
| 09/2026 | **327.5 (cao nhất)** | 177 – 478 |
| 10/2026 | 279.5 | 129 – 430 |
| 11/2026 | 141.9 | 0 – 293 |
| 12/2026 | 56.3 | 0 – 207 |
| 01/2027 | 20.8 | 0 – 172 |
| 02/2027 | **13.5 (thấp nhất)** | 0 – 164 |
| 03/2027 | 26.0 | 0 – 177 |
| 04/2027 | 78.0 | 0 – 229 |
| 05/2027 | 212.3 | 62 – 363 |

**Tổng dự báo cả năm: 1955.3 mm**

**Hình ảnh chèn**: `output_fig_12.png` (biểu đồ dự báo SARIMAX 12 tháng tới trên toàn bộ chuỗi 1979-2027, có khoảng tin cậy 95%)

---

## SLIDE 10 — Đối chiếu dự báo với quy luật lịch sử

| | Lịch sử (TB nhiều năm) | Dự báo 2026-2027 |
|---|---|---|
| Tháng mưa nhiều nhất | Tháng 9 (325.77mm) | Tháng 9 (327.48mm) |
| Tháng mưa ít nhất | Tháng 2 (12.30mm) | Tháng 2 (13.53mm) |

→ Mô hình dự báo **khớp với quy luật mùa vụ thực tế** của TP.HCM, không phải số ngẫu nhiên

**So 4 mô hình:** cả 4 đồng ý về xu hướng (tháng nào mưa nhiều/ít) nhưng khác con số cụ thể. Seasonal Naive cho số cao nhất ở tháng cao điểm (vì "copy y hệt" năm trước, ví dụ T9/2026: 473.5mm so với SARIMAX 327.5mm); SARIMAX và Prophet gần nhau hơn; XGBoost thường thấp hơn ở tháng cao điểm.

**Hình ảnh chèn**: `output_fig_13.png` (phóng to 24 tháng lịch sử gần nhất + 12 tháng dự báo của cả 4 mô hình — dễ so sánh trực quan)

---

## SLIDE 11 — Hạn chế & Hướng phát triển
**Hạn chế:**
- Dữ liệu ERA5 là tính toán lại, có thể khác số đo thực tế tại 1 điểm cụ thể
- Không có dữ liệu thời tiết thật của tương lai — mô hình chỉ dựa vào quá khứ
- Trung bình 7 điểm chỉ là xấp xỉ, chưa thay được mạng lưới đo dày đặc thực tế
- Chưa tính đến các yếu tố khí hậu lớn (El Nino, La Nina...)

**Hướng phát triển:**
- Thêm chỉ số khí hậu lớn (ENSO, nhiệt độ mặt biển...) để dự báo dài hạn tốt hơn
- Dùng dự báo thời tiết thật cho tháng tới (nếu có) làm thông tin hỗ trợ
- Kiểm tra thêm độ tin cậy của khoảng dự báo qua nhiều năm
- Thử nghiệm mô hình Deep Learning (LSTM, Transformer) khi có thêm dữ liệu

---

## SLIDE 12 — Kết luận
- TP.HCM có mùa mưa/mùa khô rất rõ rệt, ổn định qua 47 năm, không có xu hướng tăng/giảm dài hạn
- Mô hình **SARIMAX** dự báo chính xác nhất (RMSE ~59-68mm/tháng, sai số % ~25%), ổn định nhất qua nhiều năm kiểm tra
- Dự báo 12 tháng tới: tổng **~1955mm**, đỉnh điểm **Tháng 9/2026**, thấp điểm **Tháng 2/2027**
- Kết quả phù hợp để hiểu xu hướng và lập kế hoạch theo mùa; cần thêm dữ liệu/yếu tố khí hậu lớn để tăng độ chính xác cho ứng dụng thực tế

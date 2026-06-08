# Phase 9: Report Conclusions

print("=" * 70)
print("PHASE 9 - REPORT CONCLUSIONS")
print("=" * 70)

dataset_start = df_monthly.index.min().strftime("%m/%Y")
dataset_end = df_monthly.index.max().strftime("%m/%Y")
n_months = len(df_monthly)
n_weather_features = len(globals().get("available_meteo_cols", []))

cv_mean = globals().get("_cv_mean", {})
cv_rmse = cv_mean.get(forecast_model_name, float("nan"))
holdout_rmse = metrics_df.loc[forecast_model_name, "RMSE"] if forecast_model_name in metrics_df.index else float("nan")

top_corr_names = []
if "top_meteo_correlations" in globals() and len(top_meteo_correlations) > 0:
    top_corr_names = top_meteo_correlations.head(6).index.tolist()

top_perm_names = []
if "perm_importance_df" in globals() and not perm_importance_df.empty:
    top_perm_names = perm_importance_df.head(8)["Feature"].tolist()
elif "feature_importance_df" in globals() and not feature_importance_df.empty:
    top_perm_names = feature_importance_df.head(8)["Feature"].tolist()

print("\n1. DATASET SUMMARY")
print("-" * 70)
print(f"Nguon du lieu       : Open-Meteo Historical Weather API")
print(f"Thanh pho           : {city_name}")
print(f"Thoi gian           : {dataset_start} -> {dataset_end}")
print(f"So quan sat         : {n_months} thang")
print(f"Bien muc tieu       : Rainfall ({target_unit})")
print(f"So bien khi tuong   : {n_weather_features}")
print("Ghi chu             : Open-Meteo la du lieu khi tuong lich su/tai phan tich,")
print("                      khong khang dinh la do truc tiep tai tram.")

print("\n2. TIME SERIES CHARACTERISTICS")
print("-" * 70)
print("TP.HCM co mua mua ro ret tu T5-T11 va mua kho tu T12-T4.")
print("Dinh mua tap trung quanh thang 9; day la diem phu hop voi khi hau nhiet doi gio mua.")
if "season_strength" in globals():
    print(f"Season strength     : {season_strength:.3f} -> mua vu manh.")
print("ADF/KPSS/ACF/PACF va decomposition duoc dung de kiem tra stationarity, autocorrelation,")
print("va xac nhan cau truc mua vu truoc khi mo hinh hoa.")

print("\n3. WEATHER FEATURE INSIGHTS")
print("-" * 70)
if top_corr_names:
    print(f"Bien khi tuong tuong quan manh voi Rainfall: {', '.join(top_corr_names)}")
if top_perm_names:
    print(f"Feature quan trong theo permutation/RF: {', '.join(top_perm_names)}")
print("Cac bien nhu PrecipitationHours, HumidityMean, CloudCover, DewPoint co lien he vat ly")
print("voi mua, nhung neu dung gia tri cung thang/tang lai that se gay data leakage.")
print("Trong forecast, chi dung lag/rolling qua khu hoac climatology proxy.")

print("\n4. MODEL COMPARISON SUMMARY")
print("-" * 70)
if "report_metrics_df" in globals():
    print(report_metrics_df.to_string())
else:
    print(metrics_df.to_string())
if "sklearn_gridsearch_results_df" in globals() and not sklearn_gridsearch_results_df.empty:
    print("\nSklearn Pipeline/GridSearchCV demo:")
    print(sklearn_gridsearch_results_df.to_string(index=False))
print("\nRolling-Origin CV duoc uu tien hon hold-out don le vi danh gia tren nhieu giai doan.")

print("\n5. FINAL MODEL SELECTION")
print("-" * 70)
print(f"Model duoc chon      : {forecast_model_name}")
if not np.isnan(cv_rmse):
    print(f"CV-RMSE              : {cv_rmse:.2f} {target_unit}")
if not np.isnan(holdout_rmse):
    print(f"Hold-out RMSE        : {holdout_rmse:.2f} {target_unit}")
if "best_accuracy_model" in globals() and best_accuracy_model != forecast_model_name:
    print(f"Best hold-out model  : {best_accuracy_model}")
    print("Ly do khong chon     : hold-out chi la mot cua so; model cuoi duoc chon theo CV-RMSE.")
print("Ly do chon model     : phu hop cau truc mua vu manh, on dinh hon qua Rolling-Origin CV,")
print("                       minh bach va de giai thich trong bao cao hoc thuat.")

print("\n6. FORECAST SUMMARY")
print("-" * 70)
if "future_index" in globals() and "future_forecast" in globals():
    print(f"Giai doan forecast   : {future_index[0]:%m/%Y} -> {future_index[-1]:%m/%Y}")
    if "forecast_period_sum" in globals():
        print(f"Tong mua du bao      : {forecast_period_sum:.1f} mm")
    thang_mua = future_forecast.idxmax()
    thang_kho = future_forecast.idxmin()
    print(f"Thang mua nhieu nhat : {thang_mua:%m/%Y} ({future_forecast.loc[thang_mua]:.2f} {target_unit})")
    print(f"Thang mua it nhat    : {thang_kho:%m/%Y} ({future_forecast.loc[thang_kho]:.2f} {target_unit})")

print("\n7. LIMITATIONS")
print("-" * 70)
print("- Open-Meteo la du lieu lich su/tai phan tich, co the khac voi so lieu tram thuc dia.")
print("- Khong dung du lieu khi tuong tuong lai that, nen cac model weather dung proxy/climatology.")
print("- Mot so bien khi tuong tuong quan cao voi Rainfall nhung co nguy co leakage neu dung sai cach.")
print("- Sai so du bao mua thang van cao do mua chiu anh huong nhieu hien tuong khi hau/doi luu kho du bao.")

print("\n8. FUTURE WORK")
print("-" * 70)
print("- Them ENSO/ONI/Nino3.4, SST, MJO de co tin hieu khi hau du bao truoc.")
print("- Neu co du bao khi tuong thang toi that, co the dung lam exogenous forecast mot cach hop le.")
print("- Kiem dinh them prediction interval coverage tren rolling-origin CV.")

print("=" * 70)
print("✅ Phase 9 hoan tat - ket luan san sang dua vao report/slide.")
print("=" * 70)

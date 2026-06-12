"""Download Open-Meteo data and aggregate 7 HCMC points to daily/monthly files."""

import calendar
import json
import os
import time
import urllib.parse
import urllib.request
from urllib.error import HTTPError, URLError
from datetime import date, timedelta

import numpy as np
import pandas as pd

HCMC_POINTS = [
    {"name": "Center_Q1Q3",    "lat": 10.7769, "lon": 106.7009},
    {"name": "NorthWest_CuChi", "lat": 11.0500, "lon": 106.5000},
    {"name": "NorthEast_ThuDuc", "lat": 10.8500, "lon": 106.7700},
    {"name": "West_BinhChanh",  "lat": 10.7000, "lon": 106.5500},
    {"name": "South_NhaBe",    "lat": 10.5500, "lon": 106.7300},
    {"name": "East_Q9",        "lat": 10.8400, "lon": 106.8300},
    {"name": "Mid_TanBinh",    "lat": 10.8000, "lon": 106.6500},
]

CITY = "Ho Chi Minh City"
TIMEZONE = "Asia/Ho_Chi_Minh"

START_DATE = date(1979, 1, 1)
END_DATE = date(2026, 5, 31)

DAILY_VARIABLES = [
    "rain_sum",
    "precipitation_sum",
    "precipitation_hours",
    "temperature_2m_mean",
    "temperature_2m_min",
    "temperature_2m_max",
    "apparent_temperature_mean",
    "wind_speed_10m_max",
    "wind_gusts_10m_max",
    "shortwave_radiation_sum",
    "et0_fao_evapotranspiration",
]

HOURLY_VARIABLES = [
    "relative_humidity_2m",
    "dew_point_2m",
    "pressure_msl",
    "surface_pressure",
    "cloud_cover",
    "cloud_cover_low",
    "cloud_cover_mid",
    "cloud_cover_high",
    "wind_speed_10m",
    "wind_gusts_10m",
]

DAILY_PATH = "hcmc_openmeteo_daily.csv"
MONTHLY_PATH = "hcmc_openmeteo_monthly.csv"
METADATA_PATH = "hcmc_openmeteo_metadata.json"
CACHE_DIR = "openmeteo_cache"

def _request_json(url: str, cache_path: str) -> dict:
    """GET JSON with caching and retry."""
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)

    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    last_error = None
    for attempt in range(1, 7):
        try:
            with urllib.request.urlopen(url, timeout=90) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False)
            return payload
        except HTTPError as exc:
            last_error = exc
            if exc.code == 429:
                wait = min(90, 10 * attempt)
                print(f"  HTTP 429 — waiting {wait}s (attempt {attempt}/6)")
                time.sleep(wait)
                continue
            raise
        except URLError as exc:
            last_error = exc
            wait = min(60, 5 * attempt)
            print(f"  Network error: {exc} — waiting {wait}s (attempt {attempt}/6)")
            time.sleep(wait)
    raise RuntimeError(f"Failed after 6 attempts: {last_error}")


def request_archive(lat: float, lon: float, start: date, end: date, point_name: str) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": ",".join(DAILY_VARIABLES),
        "hourly": ",".join(HOURLY_VARIABLES),
        "timezone": TIMEZONE,
    }
    url = "https://archive-api.open-meteo.com/v1/archive?" + urllib.parse.urlencode(params)
    safe_name = point_name.replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "")
    cache_path = os.path.join(CACHE_DIR, f"openmeteo_{safe_name}_{start.year}.json")
    return _request_json(url, cache_path)


def yearly_ranges(start_date: date, end_date: date):
    current = start_date
    while current <= end_date:
        year_end = date(current.year, 12, 31)
        chunk_end = min(year_end, end_date)
        yield current, chunk_end
        current = chunk_end + timedelta(days=1)

DAILY_COL_MAP = {
    "rain_sum": "Rainfall",
    "precipitation_sum": "Precipitation",
    "precipitation_hours": "PrecipitationHours",
    "shortwave_radiation_sum": "ShortwaveRadiation",
    "et0_fao_evapotranspiration": "Evapotranspiration",
    "temperature_2m_mean": "TempMean",
    "temperature_2m_min": "TempMin",
    "temperature_2m_max": "TempMax",
    "apparent_temperature_mean": "ApparentTempMean",
    "wind_speed_10m_max": "WindSpeedMax",
    "wind_gusts_10m_max": "WindGustMax",
}

HOURLY_COL_MAP = {
    "relative_humidity_2m": "Humidity",
    "dew_point_2m": "DewPoint",
    "pressure_msl": "PressureMSL",
    "surface_pressure": "SurfacePressure",
    "cloud_cover": "CloudCover",
    "cloud_cover_low": "CloudCoverLow",
    "cloud_cover_mid": "CloudCoverMid",
    "cloud_cover_high": "CloudCoverHigh",
    "wind_speed_10m": "WindSpeedHourly",
    "wind_gusts_10m": "WindGustHourly",
}


def daily_from_payload(payload: dict) -> pd.DataFrame:
    daily = payload["daily"]
    df = pd.DataFrame({"Date": pd.to_datetime(daily["time"])})
    for api_key, col_name in DAILY_COL_MAP.items():
        df[col_name] = daily.get(api_key)
    return df


def hourly_from_payload(payload: dict) -> pd.DataFrame:
    hourly = payload.get("hourly", {})
    if not hourly:
        return pd.DataFrame()
    df = pd.DataFrame({"DateTime": pd.to_datetime(hourly["time"])})
    for api_key, col_name in HOURLY_COL_MAP.items():
        df[col_name] = hourly.get(api_key)
    return df

def download_year_chunk(start: date, end: date) -> tuple[list[pd.DataFrame], list[pd.DataFrame]]:
    """Return (list_of_daily_dfs, list_of_hourly_dfs) — one per point."""
    daily_list, hourly_list = [], []
    for pt in HCMC_POINTS:
        payload = request_archive(pt["lat"], pt["lon"], start, end, pt["name"])
        daily_list.append(daily_from_payload(payload))
        hf = hourly_from_payload(payload)
        if not hf.empty:
            hourly_list.append(hf)
        time.sleep(0.6)  # Rate limit nhẹ cho API.
    return daily_list, hourly_list


def spatial_mean_daily(frames: list[pd.DataFrame]) -> pd.DataFrame:
    """Average daily values across all coordinate points."""
    if not frames:
        return pd.DataFrame()

    merged = frames[0][["Date"]].copy()
    numeric_cols = [c for c in frames[0].columns if c != "Date"]
    for col in numeric_cols:
        col_values = []
        for df in frames:
            col_values.append(df.set_index("Date")[col])
        stacked = pd.concat(col_values, axis=1)
        merged[col] = stacked.mean(axis=1).values
    return merged


def spatial_mean_hourly(frames: list[pd.DataFrame]) -> pd.DataFrame:
    """Average hourly values across all coordinate points."""
    if not frames:
        return pd.DataFrame()

    merged = frames[0][["DateTime"]].copy()
    numeric_cols = [c for c in frames[0].columns if c != "DateTime"]
    for col in numeric_cols:
        col_values = []
        for df in frames:
            col_values.append(df.set_index("DateTime")[col])
        stacked = pd.concat(col_values, axis=1)
        merged[col] = stacked.mean(axis=1).values
    return merged

def build_hourly_monthly(df_hourly: pd.DataFrame) -> pd.DataFrame:
    if df_hourly.empty:
        return pd.DataFrame()
    df = df_hourly.copy()
    df["MonthStart"] = df["DateTime"].values.astype("datetime64[M]")
    monthly = df.groupby("MonthStart", as_index=False).agg(
        HumidityMean=("Humidity", "mean"),
        HumidityMax=("Humidity", "max"),
        DewPointMean=("DewPoint", "mean"),
        PressureMSLMean=("PressureMSL", "mean"),
        SurfacePressureMean=("SurfacePressure", "mean"),
        CloudCoverMean=("CloudCover", "mean"),
        CloudCoverLowMean=("CloudCoverLow", "mean"),
        CloudCoverMidMean=("CloudCoverMid", "mean"),
        CloudCoverHighMean=("CloudCoverHigh", "mean"),
        WindSpeedHourlyMean=("WindSpeedHourly", "mean"),
        WindGustHourlyMean=("WindGustHourly", "mean"),
        ValidHourlyRows=("DateTime", "count"),
    )
    return monthly.rename(columns={"MonthStart": "Date"})


def build_monthly(df_daily: pd.DataFrame, df_hourly: pd.DataFrame) -> pd.DataFrame:
    df = df_daily.copy()
    df["MonthStart"] = df["Date"].values.astype("datetime64[M]")
    grouped = df.groupby("MonthStart", as_index=False)

    monthly = grouped.agg(
        Rainfall=("Rainfall", "sum"),
        Precipitation=("Precipitation", "sum"),
        PrecipitationHours=("PrecipitationHours", "sum"),
        ShortwaveRadiation=("ShortwaveRadiation", "sum"),
        Evapotranspiration=("Evapotranspiration", "sum"),
        TempMean=("TempMean", "mean"),
        TempMin=("TempMin", "mean"),
        TempMax=("TempMax", "mean"),
        ApparentTempMean=("ApparentTempMean", "mean"),
        WindSpeedMax=("WindSpeedMax", "mean"),
        WindGustMax=("WindGustMax", "mean"),
        RainfallDays=("Rainfall", lambda s: int(s.notna().sum())),
    )
    monthly = monthly.rename(columns={"MonthStart": "Date"})
    monthly["ExpectedDays"] = monthly["Date"].apply(
        lambda d: calendar.monthrange(int(d.year), int(d.month))[1]
    )
    monthly["Completeness"] = monthly["RainfallDays"] / monthly["ExpectedDays"]

    hourly_monthly = build_hourly_monthly(df_hourly)
    if not hourly_monthly.empty:
        monthly = monthly.merge(hourly_monthly, on="Date", how="left")

    columns = [
        "Date",
        "Rainfall",
        "Precipitation",
        "PrecipitationHours",
        "ShortwaveRadiation",
        "Evapotranspiration",
        "TempMean",
        "TempMin",
        "TempMax",
        "ApparentTempMean",
        "WindSpeedMax",
        "WindGustMax",
        "HumidityMean",
        "HumidityMax",
        "DewPointMean",
        "PressureMSLMean",
        "SurfacePressureMean",
        "CloudCoverMean",
        "CloudCoverLowMean",
        "CloudCoverMidMean",
        "CloudCoverHighMean",
        "WindSpeedHourlyMean",
        "WindGustHourlyMean",
        "ValidHourlyRows",
        "RainfallDays",
        "ExpectedDays",
        "Completeness",
    ]
    return monthly[[c for c in columns if c in monthly.columns]]

def main():
    print(f"=== Downloading Open-Meteo data for {CITY} ===")
    print(f"Points: {len(HCMC_POINTS)}")
    for pt in HCMC_POINTS:
        print(f"  {pt['name']:30s}  ({pt['lat']}, {pt['lon']})")
    print(f"Period: {START_DATE} -> {END_DATE}")
    print()

    all_daily_frames = []
    all_hourly_frames = []

    for start, end in yearly_ranges(START_DATE, END_DATE):
        print(f"Downloading {start} -> {end} ({len(HCMC_POINTS)} points) ...")
        daily_list, hourly_list = download_year_chunk(start, end)

        sm_daily = spatial_mean_daily(daily_list)
        all_daily_frames.append(sm_daily)

        if hourly_list:
            sm_hourly = spatial_mean_hourly(hourly_list)
            all_hourly_frames.append(sm_hourly)

        time.sleep(0.5)

    df_daily = (
        pd.concat(all_daily_frames, ignore_index=True)
        .drop_duplicates(subset=["Date"])
        .sort_values("Date")
        .reset_index(drop=True)
    )
    df_hourly = (
        pd.concat(all_hourly_frames, ignore_index=True)
        .drop_duplicates(subset=["DateTime"])
        .sort_values("DateTime")
        .reset_index(drop=True)
        if all_hourly_frames
        else pd.DataFrame()
    )

    df_monthly = build_monthly(df_daily, df_hourly)

    df_daily.to_csv(DAILY_PATH, index=False)
    df_monthly.to_csv(MONTHLY_PATH, index=False)

    metadata = {
        "source": "Open-Meteo Historical Weather API",
        "city": CITY,
        "spatial_method": "mean of 7 representative coordinates",
        "coordinates": HCMC_POINTS,
        "timezone": TIMEZONE,
        "start_date": START_DATE.isoformat(),
        "end_date": END_DATE.isoformat(),
        "daily_rows": int(len(df_daily)),
        "monthly_rows": int(len(df_monthly)),
        "target": "monthly total of spatially-averaged daily rainfall",
        "target_unit": "mm/thang",
        "target_definition": (
            "Each day: spatial mean of rain_sum across 7 HCMC coordinates. "
            "Each month: sum of daily spatial means = average monthly rainfall (mm/month)."
        ),
        "api_url_template": "https://archive-api.open-meteo.com/v1/archive",
        "daily_variables": DAILY_VARIABLES,
        "hourly_variables": HOURLY_VARIABLES,
    }
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"\nSaved daily   : {DAILY_PATH} ({len(df_daily)} rows)")
    print(f"Saved monthly : {MONTHLY_PATH} ({len(df_monthly)} rows)")
    print(f"Saved metadata: {METADATA_PATH}")


if __name__ == "__main__":
    main()

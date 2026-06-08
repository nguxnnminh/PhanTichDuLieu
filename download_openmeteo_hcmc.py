import calendar
import json
import os
import time
import urllib.parse
import urllib.request
from urllib.error import HTTPError, URLError
from datetime import date, timedelta

import pandas as pd


LATITUDE = 10.8231
LONGITUDE = 106.6297
CITY = "Ho Chi Minh City"
TIMEZONE = "Asia/Ho_Chi_Minh"

# ERA5-based Open-Meteo archive is available far before 2010. Starting at 1979
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
HOURLY_PATH = "hcmc_openmeteo_hourly.csv"
MONTHLY_PATH = "hcmc_openmeteo_monthly.csv"
METADATA_PATH = "hcmc_openmeteo_metadata.json"
CACHE_DIR = "openmeteo_cache"


def request_archive(start_date: date, end_date: date) -> dict:
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": ",".join(DAILY_VARIABLES),
        "hourly": ",".join(HOURLY_VARIABLES),
        "timezone": TIMEZONE,
    }
    url = "https://archive-api.open-meteo.com/v1/archive?" + urllib.parse.urlencode(params)
    cache_path = os.path.join(CACHE_DIR, f"openmeteo_{start_date.year}.json")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f), url

    os.makedirs(CACHE_DIR, exist_ok=True)
    last_error = None
    for attempt in range(1, 7):
        try:
            with urllib.request.urlopen(url, timeout=90) as response:
                payload = json.loads(response.read().decode("utf-8"))
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False)
            return payload, url
        except HTTPError as exc:
            last_error = exc
            if exc.code == 429:
                wait_seconds = min(90, 10 * attempt)
                print(f"  HTTP 429 rate limit. Waiting {wait_seconds}s before retry {attempt}/6...")
                time.sleep(wait_seconds)
                continue
            raise
        except URLError as exc:
            last_error = exc
            wait_seconds = min(60, 5 * attempt)
            print(f"  Network error: {exc}. Waiting {wait_seconds}s before retry {attempt}/6...")
            time.sleep(wait_seconds)
    raise RuntimeError(f"Failed to download {start_date} -> {end_date}: {last_error}")


def yearly_ranges(start_date: date, end_date: date):
    current = start_date
    while current <= end_date:
        year_end = date(current.year, 12, 31)
        chunk_end = min(year_end, end_date)
        yield current, chunk_end
        current = chunk_end + timedelta(days=1)


def daily_payload_to_frame(payload: dict) -> pd.DataFrame:
    daily = payload["daily"]
    df = pd.DataFrame({
        "Date": pd.to_datetime(daily["time"]),
        "Rainfall": daily.get("rain_sum"),
        "Precipitation": daily.get("precipitation_sum"),
        "PrecipitationHours": daily.get("precipitation_hours"),
        "ShortwaveRadiation": daily.get("shortwave_radiation_sum"),
        "Evapotranspiration": daily.get("et0_fao_evapotranspiration"),
        "TempMean": daily.get("temperature_2m_mean"),
        "TempMin": daily.get("temperature_2m_min"),
        "TempMax": daily.get("temperature_2m_max"),
        "ApparentTempMean": daily.get("apparent_temperature_mean"),
        "WindSpeedMax": daily.get("wind_speed_10m_max"),
        "WindGustMax": daily.get("wind_gusts_10m_max"),
    })
    return df


def hourly_payload_to_frame(payload: dict) -> pd.DataFrame:
    hourly = payload.get("hourly", {})
    if not hourly:
        return pd.DataFrame()
    return pd.DataFrame({
        "DateTime": pd.to_datetime(hourly["time"]),
        "Humidity": hourly.get("relative_humidity_2m"),
        "DewPoint": hourly.get("dew_point_2m"),
        "PressureMSL": hourly.get("pressure_msl"),
        "SurfacePressure": hourly.get("surface_pressure"),
        "CloudCover": hourly.get("cloud_cover"),
        "CloudCoverLow": hourly.get("cloud_cover_low"),
        "CloudCoverMid": hourly.get("cloud_cover_mid"),
        "CloudCoverHigh": hourly.get("cloud_cover_high"),
        "WindSpeedHourly": hourly.get("wind_speed_10m"),
        "WindGustHourly": hourly.get("wind_gusts_10m"),
    })


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
    frames = []
    hourly_frames = []
    api_urls = []
    for start, end in yearly_ranges(START_DATE, END_DATE):
        print(f"Downloading {start} -> {end}")
        payload, url = request_archive(start, end)
        api_urls.append(url)
        frames.append(daily_payload_to_frame(payload))
        hourly_frame = hourly_payload_to_frame(payload)
        if not hourly_frame.empty:
            hourly_frames.append(hourly_frame)
        time.sleep(1.5)

    df_daily = (
        pd.concat(frames, ignore_index=True)
        .drop_duplicates(subset=["Date"])
        .sort_values("Date")
        .reset_index(drop=True)
    )
    df_hourly = (
        pd.concat(hourly_frames, ignore_index=True)
        .drop_duplicates(subset=["DateTime"])
        .sort_values("DateTime")
        .reset_index(drop=True)
        if hourly_frames else pd.DataFrame()
    )
    df_monthly = build_monthly(df_daily, df_hourly)

    df_daily.to_csv(DAILY_PATH, index=False)
    if not df_hourly.empty:
        df_hourly.to_csv(HOURLY_PATH, index=False)
    df_monthly.to_csv(MONTHLY_PATH, index=False)

    metadata = {
        "source": "Open-Meteo Historical Weather API",
        "city": CITY,
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "timezone": TIMEZONE,
        "start_date": START_DATE.isoformat(),
        "end_date": END_DATE.isoformat(),
        "daily_rows": int(len(df_daily)),
        "hourly_rows": int(len(df_hourly)),
        "monthly_rows": int(len(df_monthly)),
        "target": "monthly total rainfall",
        "target_unit": "mm/thang",
        "api_url_template": "https://archive-api.open-meteo.com/v1/archive",
        "daily_variables": DAILY_VARIABLES,
        "hourly_variables": HOURLY_VARIABLES,
        "chunked_by": "year",
        "cache_dir": CACHE_DIR,
        "first_chunk_url": api_urls[0] if api_urls else None,
        "last_chunk_url": api_urls[-1] if api_urls else None,
    }
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"Saved daily   : {DAILY_PATH} ({len(df_daily)} rows)")
    if not df_hourly.empty:
        print(f"Saved hourly  : {HOURLY_PATH} ({len(df_hourly)} rows)")
    print(f"Saved monthly : {MONTHLY_PATH} ({len(df_monthly)} rows)")
    print(f"Saved metadata: {METADATA_PATH}")


if __name__ == "__main__":
    main()

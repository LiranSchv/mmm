from __future__ import annotations
"""
Builds seasonality regressors for MMM models:
  - Day-of-week indicators
  - National public holidays (via `holidays` library)
  - Custom user-defined events
"""
from typing import Any
import pandas as pd
import numpy as np

try:
    import holidays as hol_lib
    _HOLIDAYS_AVAILABLE = True
except ImportError:
    _HOLIDAYS_AVAILABLE = False


# Country codes supported by the `holidays` library
SUPPORTED_COUNTRIES = {
    "US": "United States",
    "UK": "United Kingdom",
    "GB": "United Kingdom",
    "DE": "Germany",
    "FR": "France",
    "AU": "Australia",
    "IL": "Israel",
    "CA": "Canada",
    "NL": "Netherlands",
    "ES": "Spain",
    "IT": "Italy",
    "JP": "Japan",
    "BR": "Brazil",
}


def build_seasonality_features(
    dates: pd.Series,
    config: dict[str, Any],
) -> pd.DataFrame:
    """
    config = {
        "dow": true,                          # day-of-week dummies
        "countries": ["US", "UK"],            # national holidays
        "custom_events": [
            {"name": "product_launch", "date": "2024-03-15", "window_days": 7}
        ]
    }

    Returns a DataFrame indexed by date with one column per feature.
    """
    dates = pd.to_datetime(dates)
    df = pd.DataFrame({"date": dates})

    # Day of week (0=Mon … 6=Sun)
    if config.get("dow", True):
        for i, name in enumerate(["mon", "tue", "wed", "thu", "fri", "sat", "sun"]):
            df[f"dow_{name}"] = (df["date"].dt.dayofweek == i).astype(int)

    # Week of year sine/cosine encoding for smooth annual seasonality
    df["week_sin"] = np.sin(2 * np.pi * df["date"].dt.isocalendar().week / 52)
    df["week_cos"] = np.cos(2 * np.pi * df["date"].dt.isocalendar().week / 52)

    # National holidays
    countries = config.get("countries", [])
    if countries and _HOLIDAYS_AVAILABLE:
        years = list(range(dates.dt.year.min(), dates.dt.year.max() + 1))
        holiday_dates: set = set()
        for country_code in countries:
            code = "GB" if country_code == "UK" else country_code
            try:
                country_holidays = hol_lib.country_holidays(code, years=years)
                holiday_dates.update(country_holidays.keys())
            except (KeyError, NotImplementedError):
                pass
        df["is_holiday"] = df["date"].dt.date.isin(holiday_dates).astype(int)
    else:
        df["is_holiday"] = 0

    # Black Friday / Cyber Monday proximity (major for gaming FTBs)
    bf_dates = _black_friday_dates(dates.dt.year.min(), dates.dt.year.max())
    df["days_to_black_friday"] = df["date"].apply(
        lambda d: min(abs((d - bf).days) for bf in bf_dates)
    )
    df["near_black_friday"] = (df["days_to_black_friday"] <= 7).astype(int)

    # Custom events
    for event in config.get("custom_events", []):
        event_date = pd.Timestamp(event["date"])
        window = event.get("window_days", 7)
        col = f"event_{event['name'].lower().replace(' ', '_')}"
        df[col] = (
            (df["date"] >= event_date - pd.Timedelta(days=window // 2)) &
            (df["date"] <= event_date + pd.Timedelta(days=window // 2))
        ).astype(int)

    df = df.set_index("date")
    return df


def _black_friday_dates(year_min: int, year_max: int) -> list[pd.Timestamp]:
    """Return Black Friday dates (4th Thursday of November + 1 day)."""
    bfs = []
    for year in range(year_min, year_max + 1):
        nov = pd.date_range(f"{year}-11-01", f"{year}-11-30", freq="D")
        thursdays = nov[nov.dayofweek == 3]
        if len(thursdays) >= 4:
            bfs.append(thursdays[3] + pd.Timedelta(days=1))
    return bfs


def list_supported_countries() -> list[dict[str, str]]:
    return [{"code": k, "name": v} for k, v in SUPPORTED_COUNTRIES.items()]

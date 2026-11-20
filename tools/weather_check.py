"""Check an hourly weather DataFrame (from weather_fetch.py) and print a report:
number of hours, time range, UTC check, missing hours (gaps), duplicates, missing values.

Usage in a Jupyter notebook:
    import pandas as pd
    from weather_check import check_weather

    w_solar = pd.read_csv("weather_glejbjerg.csv", parse_dates=["date"])
    result = check_weather(w_solar, year=2025)   # expects 8760 hourly rows for 2025 (UTC)
    result["gaps"]                               # table of missing periods

Or from the command line:
    python weather_check.py weather_glejbjerg.csv 2025
"""
import inspect

import pandas as pd

HOUR = pd.Timedelta(hours=1)


def _guess_name(df: pd.DataFrame, frame) -> str | None:
    """Find a variable name in the caller's namespace that refers to df."""
    try:
        for ns in (frame.f_locals, frame.f_globals):
            for key, value in ns.items():
                if value is df and not key.startswith("_"):
                    return key
    finally:
        del frame
    return None


def _timestamps(df: pd.DataFrame) -> pd.DatetimeIndex:
    """Timestamps from the 'date' column, or from the index if there is no such column."""
    source = df["date"] if "date" in df.columns else df.index
    return pd.DatetimeIndex(pd.to_datetime(source))


def _runs(missing: pd.DatetimeIndex) -> pd.DataFrame:
    """Group missing hourly timestamps into contiguous gaps."""
    if len(missing) == 0:
        return pd.DataFrame(columns=["start", "end", "hours"])
    s = missing.to_series()
    grp = s.groupby((s.diff() != HOUR).cumsum().values)
    return pd.DataFrame(
        {
            "start": grp.min().reset_index(drop=True),
            "end": grp.max().reset_index(drop=True),
            "hours": grp.size().reset_index(drop=True),
        }
    )


def check_weather(
    df: pd.DataFrame,
    year: int | None = None,
    name: str | None = None,
    max_gaps_shown: int = 10,
) -> dict:
    """Print a data-quality report for an hourly weather DataFrame and return the results.

    year: if given, the data is expected to cover that whole calendar year in UTC
          (00:00 on 1 Jan to 23:00 on 31 Dec). Otherwise the expected period is the
          first to the last timestamp in the data, so only internal gaps are found.
    name: label for the report. Default: the variable name of df in the calling code.
    """
    name = name or _guess_name(df, inspect.currentframe().f_back) or "weather data"
    idx = _timestamps(df)

    # --- UTC check -------------------------------------------------------------
    if idx.tz is None:
        tz_note = "no time zone in timestamps, assumed to be UTC"
        is_utc = None
        idx = idx.tz_localize("UTC")
    else:
        as_utc = idx.tz_convert("UTC")
        is_utc = bool((idx.tz_localize(None) == as_utc.tz_localize(None)).all())
        tz_note = "timestamps are UTC" if is_utc else f"timestamps are in {idx.tz}, converted to UTC"
        idx = as_utc

    # --- hours present, duplicates, off-the-hour stamps --------------------------
    n_rows = len(idx)
    duplicates = int(idx.duplicated().sum())
    off_hour = int(((idx.minute != 0) | (idx.second != 0)).sum())
    unique = idx.unique().sort_values()

    # --- expected period, missing and extra hours --------------------------------
    if year is not None:
        start, end = pd.Timestamp(f"{year}-01-01", tz="UTC"), pd.Timestamp(f"{year}-12-31 23:00", tz="UTC")
    else:
        start, end = unique.min(), unique.max()
    expected = pd.date_range(start, end, freq="h")
    missing = expected.difference(unique)
    extra = unique.difference(expected)
    gaps = _runs(missing)

    # --- missing values (NaN) per column -----------------------------------------
    values = df.drop(columns=["date"], errors="ignore")
    nan_counts = values.isna().sum()
    nan_rows = int(values.isna().any(axis=1).sum())

    issues = bool(len(missing) or len(extra) or duplicates or off_hour or nan_rows or is_utc is False)

    # --- report -----------------------------------------------------------------
    print(f"=== Weather data check: {name} ===")
    print(f"Hours (rows) in data : {n_rows}")
    print(f"First / last (UTC)   : {unique.min()}  ->  {unique.max()}")
    print(f"Time zone            : {tz_note}")
    print(f"Expected hours       : {len(expected)}  ({start:%Y-%m-%d %H:%M} -> {end:%Y-%m-%d %H:%M} UTC)")
    print(f"Missing hours        : {len(missing)}")
    if len(gaps):
        print(gaps.head(max_gaps_shown).to_string(index=False))
        if len(gaps) > max_gaps_shown:
            print(f"... and {len(gaps) - max_gaps_shown} more gaps")
    print(f"Extra hours outside expected period: {len(extra)}")
    print(f"Duplicate timestamps : {duplicates}")
    print(f"Timestamps not on the hour: {off_hour}")
    print(f"Rows with missing values: {nan_rows}")
    if nan_counts.sum():
        nonzero = nan_counts[nan_counts > 0]
        print(pd.DataFrame({"missing": nonzero, "percent": (100 * nonzero / n_rows).round(2)}).to_string())
    else:
        print("No missing values in any column.")
    print("Result: " + ("ISSUES FOUND" if issues else "OK"))

    return {
        "rows": n_rows,
        "first": unique.min(),
        "last": unique.max(),
        "is_utc": is_utc,
        "expected_hours": len(expected),
        "missing_hours": len(missing),
        "gaps": gaps,
        "extra_hours": len(extra),
        "duplicates": duplicates,
        "off_hour": off_hour,
        "nan_counts": nan_counts,
        "ok": not issues,
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        sys.exit("usage: python weather_check.py FILE.csv [YEAR]")
    frame = pd.read_csv(sys.argv[1], parse_dates=["date"])
    check_weather(frame, year=int(sys.argv[2]) if len(sys.argv) > 2 else None, name=sys.argv[1])

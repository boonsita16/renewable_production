"""Plot helpers for the weather CSVs written by weather_fetch.py.

Usage in a Jupyter notebook:
    import pandas as pd
    from weather_plots import plot_weather

    w = pd.read_csv("weather_glejbjerg.csv", parse_dates=["date"])

    # Hourly distribution (box plot per hour of day), one stacked panel per month
    plot_weather(w, "shortwave_radiation", mode="hourly", months=[1, 7])

    # Daily average line over the year (or agg="sum", "max", "median", ...)
    plot_weather(w, "wind_speed_10m", mode="daily")
    plot_weather(w, "wind_speed_10m", mode="daily", months=[1, 7])  # only some months

Requires: pandas, matplotlib, seaborn
"""
import calendar
import inspect
import warnings

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

UNITS = {
    "temperature_2m": "°C",
    "relative_humidity_2m": "%",
    "wind_speed_10m": "m/s",
    "wind_speed_100m": "m/s",
    "wind_direction_10m": "°",
    "wind_direction_100m": "°",
    "surface_pressure": "hPa",
    "shortwave_radiation": "W/m²",
    "direct_normal_irradiance": "W/m²",
    "diffuse_radiation": "W/m²",
}


def _prepare(df: pd.DataFrame, tz: str | None) -> pd.DataFrame:
    """Return a copy with datetime 'date' (optionally converted to tz), 'hour' and 'month'."""
    out = df.copy()
    if "date" in out.columns:
        out["date"] = pd.to_datetime(out["date"], utc=True)
    else:  # fall back to a datetime index
        out["date"] = pd.to_datetime(out.index, utc=True)
    if tz:
        out["date"] = out["date"].dt.tz_convert(tz)
    out["hour"] = out["date"].dt.hour
    out["month"] = out["date"].dt.month
    return out


def _guess_name(df: pd.DataFrame, frame) -> str | None:
    """Find a variable name in the caller's namespace that refers to df (e.g. 'w_solar')."""
    try:
        for ns in (frame.f_locals, frame.f_globals):
            for key, value in ns.items():
                if value is df and not key.startswith("_"):
                    return key
    finally:
        del frame
    return None


def plot_weather(
    df: pd.DataFrame,
    variable: str,
    mode: str = "hourly",
    months: list[int] | None = None,
    tz: str | None = None,
    agg: str = "mean",
    figsize: tuple[float, float] | None = None,
    save_path: str | None = None,
    name: str | None = None,
) -> None:
    """Plot one weather variable.

    mode="hourly":  box plot of the variable by hour of day, one stacked panel per month
                    in `months` (default [1, 7]); panels share x and y scales.
    mode="daily":   line chart of `agg` (default mean) per day; `months` restricts the
                    plot to those months, default is the whole period.
    tz: optional time zone for the hour of day / month grouping (e.g. "Europe/Copenhagen").
        Data is UTC by default.
    save_path: if given, the figure is also saved to this file.
    name: label shown in the plot titles. Default: the variable name the DataFrame has
          in the calling code/notebook (e.g. 'w_solar'); pass name="..." to override.
    """
    if variable not in df.columns:
        raise ValueError(f"'{variable}' not in columns: {list(df.columns)}")
    if mode not in ("hourly", "daily"):
        raise ValueError("mode must be 'hourly' or 'daily'")
    if "direction" in variable and mode == "daily" and agg in ("mean", "median"):
        warnings.warn("Averaging a wind direction in degrees is not meaningful (circular quantity).")

    name = name or _guess_name(df, inspect.currentframe().f_back)
    prefix = f"{name} – " if name else ""
    data = _prepare(df, tz)
    unit = UNITS.get(variable, "")
    ylabel = f"{variable} [{unit}]" if unit else variable

    if mode == "hourly":
        months = list(months) if months else [1, 7]
        fig, axes = plt.subplots(
            nrows=len(months),
            ncols=1,
            figsize=figsize or (14, 4 * len(months) + 1),
            sharex=True,
            sharey=True,
            squeeze=False,
        )
        axes = axes.ravel()
        for ax, m in zip(axes, months):
            subset = data[data["month"] == m]
            if subset.empty:
                ax.set_title(f"{prefix}{calendar.month_name[m]}: no data")
                continue
            sns.boxplot(data=subset, x="hour", y=variable, ax=ax, color="tab:blue", fliersize=2)
            ax.set_title(f"{prefix}Hourly distribution of {variable}, {calendar.month_name[m]}", fontsize=13)
            ax.set_xlabel("")
            ax.set_ylabel(ylabel, fontsize=11)
            ax.grid(axis="y", linestyle="--", alpha=0.7)
        axes[-1].set_xlabel(f"Hour of day ({tz or 'UTC'})", fontsize=12)
    else:
        if months:
            data = data[data["month"].isin(months)]
        resampler = data.set_index("date")[variable].resample("D")
        daily = resampler.agg(agg).where(resampler.count() > 0)  # NaN (line gap) for days without data
        daily.index = daily.index.tz_localize(None)  # local wall-clock dates for the axis
        fig, ax = plt.subplots(figsize=figsize or (14, 5))
        ax.plot(daily.index, daily.values, color="tab:blue", linewidth=1.2)
        ax.set_title(f"{prefix}Daily {agg} of {variable}", fontsize=13)
        ax.set_ylabel(f"{agg} {ylabel}", fontsize=11)
        ax.grid(linestyle="--", alpha=0.7)
        fig.autofmt_xdate()

    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()

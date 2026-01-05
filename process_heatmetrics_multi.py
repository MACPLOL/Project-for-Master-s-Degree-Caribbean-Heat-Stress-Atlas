#!/usr/bin/env python3
import sys
import json
import pandas as pd

# Thresholds (°C)
HOT_DAY_32 = 32.0          # “hot day”
HOT_DAY_35 = 35.0          # “very hot day”
WARM_NIGHT_24 = 24.0       # “warm night”

# Quality filter
MIN_DAYS_PER_YEAR = 200    # require at least this many valid days in a year

# Stations to ignore completely (too short / messy records)
BAD_STATIONS = {
    "ADJUNTAS 2 NW, PR US",
    "MAYAGUEZ AIRPORT, PR US",
    "MAYAGUEZ ARRIBA, PR RQ",
}

# Nicer labels for some stations
FRIENDLY_NAMES = {
    "SAN JUAN L M MARIN INTERNATIONAL AIRPORT, PR US": "San Juan (Airport)",
    "PONCE 4 E, PR US": "Ponce",
    "MAYAGUEZ 1 O, PR US": "Mayagüez",
    "ROOSEVELT ROADS, PR US": "Ceiba (Roosevelt Roads)",
    "ARECIBO 3 ESE, PR US": "Arecibo",
    # add/edit as you like
}

# ---------- MAIN LOGIC ----------

def main(input_csv: str, output_geojson: str) -> None:
    # Read CSV and parse DATE column as datetime
    df = pd.read_csv(input_csv, parse_dates=["DATE"])

    # Drop known-bad stations (by NAME)
    if "NAME" in df.columns:
        df = df[~df["NAME"].isin(BAD_STATIONS)].copy()

    # Keep only the columns we actually need
    required = ["STATION", "NAME", "LATITUDE", "LONGITUDE", "DATE", "TMAX", "TMIN"]
    for col in required:
        if col not in df.columns:
            raise SystemExit(f"Missing required column '{col}' in {input_csv}")

    df = df[required]

    # Remove rows with missing TMAX or TMIN
    df = df.dropna(subset=["TMAX", "TMIN"]).copy()
    if df.empty:
        raise SystemExit("No non-missing TMAX/TMIN values in file.")

    # Convert Fahrenheit to Celsius (CDO “Standard” units are °F)
    df["TMAX_C"] = (df["TMAX"] - 32.0) * 5.0 / 9.0
    df["TMIN_C"] = (df["TMIN"] - 32.0) * 5.0 / 9.0

    # Precompute year and month
    df["year"] = df["DATE"].dt.year
    df["month"] = df["DATE"].dt.month

    features = []

    for station_id, g in df.groupby("STATION"):
        g = g.sort_values("DATE").copy()

        name_raw = g["NAME"].iloc[0]
        name = FRIENDLY_NAMES.get(name_raw, name_raw)
        lat = float(g["LATITUDE"].iloc[0])
        lon = float(g["LONGITUDE"].iloc[0])

        # metrics[metric_name][year_str] = value
        metrics = {
            "hot_days_32": {},
            "hot_days_35": {},
            "warm_nights_24": {},
            "oppressive_days": {},
            "hottest_month_index": {},
            "hottest_month_tmax": {},
            "hottest_month_tmin": {},
        }

        for year, gy in g.groupby("year"):
            # Skip incomplete years
            if gy["TMAX_C"].notna().sum() < MIN_DAYS_PER_YEAR:
                continue

            year_str = str(year)

            # --- Day / night threshold counts ---
            hot32 = int((gy["TMAX_C"] >= HOT_DAY_32).sum())
            hot35 = int((gy["TMAX_C"] >= HOT_DAY_35).sum())
            wn24  = int((gy["TMIN_C"] >= WARM_NIGHT_24).sum())
            opp   = int(
                ((gy["TMAX_C"] >= HOT_DAY_32) & (gy["TMIN_C"] >= WARM_NIGHT_24)).sum()
            )

            metrics["hot_days_32"][year_str] = hot32
            metrics["hot_days_35"][year_str] = hot35
            metrics["warm_nights_24"][year_str] = wn24
            metrics["oppressive_days"][year_str] = opp

            # --- Hottest month stats for that year ---
            monthly = gy.groupby("month").agg(
                tmax_mean=("TMAX_C", "mean"),
                tmin_mean=("TMIN_C", "mean"),
            )

            # month index (1–12) with highest mean TMAX
            hottest_month = int(monthly["tmax_mean"].idxmax())
            metrics["hottest_month_index"][year_str] = hottest_month
            metrics["hottest_month_tmax"][year_str] = float(
                monthly.loc[hottest_month, "tmax_mean"]
            )
            metrics["hottest_month_tmin"][year_str] = float(
                monthly.loc[hottest_month, "tmin_mean"]
            )

        # If station has no valid years, skip it
        if not metrics["hot_days_32"]:
            continue

        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat],
                },
                "properties": {
                    "id": station_id,
                    "name": name,
                    "country": "Puerto Rico",
                    "metrics": metrics,
                },
            }
        )

    fc = {"type": "FeatureCollection", "features": features}

    with open(output_geojson, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(features)} station(s) to {output_geojson}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 process_heatmetrics_multi.py input.csv output.geojson")
        raise SystemExit(1)

    main(sys.argv[1], sys.argv[2])

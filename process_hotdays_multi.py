import sys, json
import pandas as pd

# Threshold & quality filter
THRESHOLD_C = 32.0          # “very hot day” = Tmax ≥ 32 °C
MIN_DAYS_PER_YEAR = 200     # need at least this many valid days in a year


def main(input_csv, output_geojson):
    # Read CSV and parse DATE column as datetime
    df = pd.read_csv(input_csv, parse_dates=["DATE"])

    # Drop stations with very patchy data
    bad_stations = [
        "ADJUNTAS 2 NW, PR US",
        "MAYAGUEZ AIRPORT, PR US",
        "MAYAGUEZ ARRIBA, PR RQ",
    ]
    df = df[~df["NAME"].isin(bad_stations)].copy()

    # We only need these columns
    needed_cols = ["STATION", "NAME", "LATITUDE", "LONGITUDE", "DATE", "TMAX"]
    for c in needed_cols:
        if c not in df.columns:
            raise SystemExit(f"Missing column {c} in {input_csv}")
    df = df[needed_cols]

    # Drop rows where TMAX is missing
    df = df[df["TMAX"].notna()]
    if df.empty:
        raise SystemExit("No non-missing TMAX values in file.")

    features = []

    # Optional: nicer names for some stations
    FRIENDLY = {
        "ROOSEVELT ROADS, PR US": "Ceiba (Roosevelt Roads)",
        "PONCE 4 E, PR US":       "Ponce",
        "MAYAGUEZ AIRPORT, PR US": "Mayagüez Airport",  # harmless even though we drop it
        # add more here if you want prettier labels
    }

    # Loop over each station separately
    for station_id, g in df.groupby("STATION"):
        name_raw = g["NAME"].iloc[0]
        name = FRIENDLY.get(name_raw, name_raw)
        lat = float(g["LATITUDE"].iloc[0])
        lon = float(g["LONGITUDE"].iloc[0])

        g = g.copy()

        # CSV uses Fahrenheit, so convert to Celsius
        g["TMAX_C"] = (g["TMAX"] - 32.0) * 5.0 / 9.0

        values = {}

        # Group by year and count “very hot days”
        for year, gy in g.groupby(g["DATE"].dt.year):
            # skip incomplete years
            if gy["TMAX_C"].notna().sum() < MIN_DAYS_PER_YEAR:
                continue

            hot_count = int((gy["TMAX_C"] >= THRESHOLD_C).sum())
            values[str(year)] = hot_count

        # If this station has no good years, skip it
        if not values:
            continue

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            },
            "properties": {
                "id": station_id,
                "name": name,
                "country": "Puerto Rico",
                "values": values
            }
        })

    fc = {"type": "FeatureCollection", "features": features}

    with open(output_geojson, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(features)} station(s) to {output_geojson}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 process_hotdays_multi.py input.csv output.geojson")
        raise SystemExit(1)
    main(sys.argv[1], sys.argv[2])

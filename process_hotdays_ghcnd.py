import sys
import json
from pathlib import Path

import pandas as pd


def main(input_csv, output_geojson):
    # 1. Load the CSV you downloaded from NOAA
    df = pd.read_csv(input_csv)

    # Expect columns: STATION, NAME, LATITUDE, LONGITUDE, DATE, TMAX, ...
    df["DATE"] = pd.to_datetime(df["DATE"])
    df["year"] = df["DATE"].dt.year

    # 2. Convert TMAX from Fahrenheit -> Celsius
    #    T(°C) = (T(°F) - 32) * 5/9
    df["tmax_c"] = (df["TMAX"] - 32.0) * 5.0 / 9.0

    # 3. Very hot day = Tmax >= 32 °C
    hot_mask = df["tmax_c"] >= 32.0

    features = []

    # 4. Group by station (works even if later you add more stations)
    for station_id, station_df in df.groupby("STATION"):
        first = station_df.iloc[0]
        raw_name = str(first["NAME"])
        lat = float(first["LATITUDE"])
        lon = float(first["LONGITUDE"])

        # Friendly name + country (hard-coded for now)
        name = "San Juan (Airport)"
        country = "Puerto Rico"

        # 5. Count very hot days per year for this station
        station_hot = station_df[hot_mask & (station_df["STATION"] == station_id)]
        counts = station_hot.groupby("year").size()

        # Build { "1960": 58, "1961": 45, ... }
        values = {str(int(year)): int(cnt) for year, cnt in counts.items()}

        props = {
            "station_id": station_id,
            "name": name,
            "country": country,
            "values": values,  # matches current Leaflet structure
        }

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat],  # [lon, lat] for GeoJSON
            },
            "properties": props,
        }
        features.append(feature)

    fc = {"type": "FeatureCollection", "features": features}

    # 6. Save GeoJSON
    out_path = Path(output_geojson)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(fc, f, indent=2)

    print(f"Saved {len(features)} station(s) to {output_geojson}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python process_hotdays_ghcnd.py input.csv output.geojson")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])

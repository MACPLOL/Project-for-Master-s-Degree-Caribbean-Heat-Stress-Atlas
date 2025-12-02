import sys, os, json
import matplotlib.pyplot as plt

# Human-readable labels for the metrics
METRIC_LABELS = {
    "hot_days_32":     "Hot days (Tmax ≥ 32 °C)",
    "hot_days_35":     "Very hot days (Tmax ≥ 35 °C)",
    "warm_nights_24":  "Warm nights (Tmin ≥ 24 °C)",
    "oppressive_days": "Oppressive days (Tmax ≥ 32 °C & Tmin ≥ 24 °C)",
}

def safe_filename(name: str) -> str:
    """Turn station name into something safe for a filename."""
    bad_chars = [' ', '(', ')', '/', ',', ':']
    fn = name
    for ch in bad_chars:
        fn = fn.replace(ch, '_')
    # collapse multiple underscores
    while '__' in fn:
        fn = fn.replace('__', '_')
    return fn.strip('_').lower()

def main(geojson_path: str, out_dir: str):
    # Ensure output directory exists
    os.makedirs(out_dir, exist_ok=True)

    # Load GeoJSON
    with open(geojson_path, encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    if not features:
        print("No features found in GeoJSON.")
        return

    for feat in features:
        props = feat.get("properties", {})
        name = props.get("name", "Unknown station")
        metrics = props.get("metrics", {})

        # Use hot_days_32 (or another metric) as reference for available years
        ref_metric = metrics.get("hot_days_32") or metrics.get("hot_days_35")
        if not ref_metric:
            print(f"Skipping {name}: no reference metric.")
            continue

        years = sorted(ref_metric.keys(), key=int)
        years_int = [int(y) for y in years]

        # Build series for the metrics we care about
        series = {}
        for key in ["hot_days_32", "warm_nights_24"]:
            m = metrics.get(key)
            if not m:
                continue
            values = [m.get(y, None) for y in years]
            # Skip if all values are None
            if all(v is None for v in values):
                continue
            series[key] = values

        if not series:
            print(f"Skipping {name}: no usable series.")
            continue

        # Plot
        plt.figure(figsize=(6, 4))

        for metric_key, values in series.items():
            label = METRIC_LABELS.get(metric_key, metric_key)
            plt.plot(years_int, values, marker='o', linewidth=1.2, markersize=3, label=label)

        plt.title(f"{name} — heat metrics over time")
        plt.xlabel("Year")
        plt.ylabel("Days per year")
        plt.grid(True, linewidth=0.3, alpha=0.5)
        plt.legend(fontsize=8)
        plt.tight_layout()

        out_name = safe_filename(name) + "_timeseries.png"
        out_path = os.path.join(out_dir, out_name)
        plt.savefig(out_path, dpi=150)
        plt.close()

        print(f"Saved plot for {name} -> {out_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 plot_station_timeseries.py stations_heatmetrics_all.geojson output_dir")
        sys.exit(1)

    geojson_path = sys.argv[1]
    out_dir = sys.argv[2]
    main(geojson_path, out_dir)

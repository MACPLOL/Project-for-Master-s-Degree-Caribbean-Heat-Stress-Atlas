import sys, json

# Stations we want to remove (with and without the GHCND: prefix)
BAD_IDS = {
    "RQC00660053", "GHCND:RQC00660053",   # ADJUNTAS 2 NW, PR US
    "RQ1PRMY0005", "GHCND:RQ1PRMY0005",   # MAYAGUEZ ARRIBA, PR RQ
}

def main(in_file, out_file):
    with open(in_file, "r", encoding="utf-8") as f:
        fc = json.load(f)

    keep_features = []
    removed = []

    for feat in fc.get("features", []):
        props = feat.get("properties", {})
        sid = props.get("id") or props.get("station") or ""
        # strip any accidental whitespace
        sid_clean = sid.strip()

        if sid_clean in BAD_IDS:
            removed.append(props.get("name", sid_clean))
            continue

        keep_features.append(feat)

    out = {"type": "FeatureCollection", "features": keep_features}

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Kept {len(keep_features)} station(s)")
    if removed:
        print("Removed:", ", ".join(sorted(set(removed))))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 filter_hotdays_stations.py input.geojson output.geojson")
        raise SystemExit(1)
    main(sys.argv[1], sys.argv[2])

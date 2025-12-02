import sys, json

def main(output_path, input_paths):
    features = []
    for path in input_paths:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        feats = data.get("features", [])
        features.extend(feats)

    fc = {"type": "FeatureCollection", "features": features}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(features)} merged feature(s) to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 merge_heatmetrics_geojson.py output.geojson input1.geojson input2.geojson ...")
        sys.exit(1)

    out_path = sys.argv[1]
    in_paths = sys.argv[2:]
    main(out_path, in_paths)

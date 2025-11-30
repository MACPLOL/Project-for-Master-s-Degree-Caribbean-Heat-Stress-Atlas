import sys, json

def main(single_file, multi_file, out_file):
    # Load the two geojson files
    with open(single_file, "r", encoding="utf-8") as f:
        g1 = json.load(f)
    with open(multi_file, "r", encoding="utf-8") as f:
        g2 = json.load(f)

    features = []
    seen = set()

    # Helper to add features without duplicates
    def add_from(fc):
        for feat in fc.get("features", []):
            props = feat.get("properties", {})
            key = props.get("id") or props.get("name")
            if key is None:
                # fallback: lat/lon
                geom = feat.get("geometry", {})
                coords = tuple(geom.get("coordinates", []))
                key_local = ("coords", coords)
            else:
                key_local = ("id_or_name", key)

            if key_local in seen:
                continue
            seen.add(key_local)
            features.append(feat)

    add_from(g1)
    add_from(g2)

    out_fc = {"type": "FeatureCollection", "features": features}

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_fc, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(features)} feature(s) to {out_file}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 merge_hotdays_geojson.py single.geojson multi.geojson output.geojson")
        raise SystemExit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])

# Data folder

This folder holds the datasets used by the Caribbean Heat Stress Atlas project. The files are kept small and focused so it is clear which ones drive the map and which ones are raw inputs.

## Primary inputs
- `data/all_stations_1960_2025.csv`: Raw, station-level daily temperature observations (1960–2025). This is the large source file used to derive the metrics.

## Derived outputs (used by the web map)
- `data/stations_heatmetrics_all.geojson`: Per-station, per-year heat metrics used by `index.html`.
- `data/stations_heatmetrics.geojson`: A smaller or earlier version of the heat metrics output.
- `data/stations_all_hotdays.geojson`: Hot-day counts per station.
- `data/stations_multi_hotdays.geojson`: Hot-day counts across multiple stations.
- `data/stations_multi_hotdays_filtered.geojson`: Filtered version of the multi-station hot-day dataset.
- `data/stations_san_juan_heatmetrics.geojson`: Heat metrics focused on the San Juan station.
- `data/stations_san_juan_hotdays.geojson`: Hot-day counts focused on the San Juan station.
- `data/stations_example.geojson`: Example subset for testing or demo use.
- `data/station_summary.csv`: Summary table created from the metrics.
- `data/pr_boundary.geojson`: Puerto Rico boundary used for the map overlay.

## Raw inputs
- `data/raw/`: Raw, unprocessed files kept for reference or reruns.
  - `data/raw/san_juan_1960_2025.csv`: San Juan-only raw data extracted from the full station file.

## Regeneration
If you need to rebuild the metrics, start from `data/all_stations_1960_2025.csv` and run the processing scripts in the repo (for example `process_heatmetrics_multi.py` for the metrics output). Always verify outputs before replacing the files used by the web map.

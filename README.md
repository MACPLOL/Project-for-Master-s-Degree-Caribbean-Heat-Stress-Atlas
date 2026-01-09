# Caribbean Heat Stress Atlas

This is my graduate project to complete the requirements for graduation from the Polytechnic University of Puerto Rico, San Juan campus. It was made by Mauro A. Collazo Pabón, masters student, with guidance from my advisor, Professor Jeffrey Duffany, PhD.

At a high level, this project turns raw weather records into an interactive, map-based tool that shows when and where heat becomes a real human problem. The map focuses on hot days, and warm nights. These measures better capture when heat disrupts sleep, reduces performance, and becomes unsafe.

This matters for Puerto Rico and the Caribbean because it helps people make better day-to-day decisions about outdoor work, exercise, and comfort. It also serves as a strong capstone portfolio project, showing I can take messy real-world data, build meaningful analytics, and ship a polished web product.

## What is in this repo
- `index.html` is the interactive web map.
- `data/` contains the raw inputs and the derived outputs used by the map.
- `process_*.py` scripts turn the raw data into heat metrics and hot-day summaries.
- `merge_*.py` scripts package outputs into GeoJSON for the map.
- `plot_station_timeseries.py` generates time-series figures.

## Data flow (simple version)
1. Start with raw station data in `data/all_stations_1960_2025.csv`.
2. Run the processing scripts to compute heat metrics and hot-day counts.
3. Merge outputs into GeoJSON files stored in `data/`.
4. Open `index.html` to explore the results on the map.

## Outputs used by the map
The map reads GeoJSON files in `data/`, such as:
- `data/stations_heatmetrics_all.geojson`
- `data/stations_all_hotdays.geojson`
- `data/stations_multi_hotdays_filtered.geojson`
- `data/pr_boundary.geojson`

## Notes
- The raw data can be large, so, for future uses, I should keep derived files small and focused for the map. Divide and conquer!
- Adding more data into the map can be messy, so a duplicate file should be made to better see the results before adding them to the final version.

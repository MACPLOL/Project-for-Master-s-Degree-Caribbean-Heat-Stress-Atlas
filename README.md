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

## Data dictionary / Methodology (simple language)
- Station: a weather location with a name and coordinates.
- Raw record: a daily temperature reading from the station.
- Hot day: a day that is much hotter than normal for that place (the project uses a threshold in the processing scripts).
- Warm night: a night that stays hot and does not cool down much.
- Heat metrics: summary numbers like how many hot days happened, or how strong the heat was.
- GeoJSON: a map-friendly file that stores points and their numbers.

Methodology (simple steps):
1. Clean the raw station data.
2. Compute daily values (highs and lows).
3. Flag hot days and warm nights.
4. Count them per station and time period.
5. Save results as GeoJSON for the map.

## Validation / QA
- Spot-check a few stations: pick 2-3 and compare map values with the raw CSV for the same dates.
- Plot one station time series with `plot_station_timeseries.py` to make sure hot periods look plausible.
- Open the map and confirm hot-day counts are not all zero or all the same.
- Check that GeoJSON files load without errors in the browser console.

## Notes
- The raw data can be large, so, for future uses, I should keep derived files small and focused for the map. Divide and conquer!
- Adding more data into the map can be messy, so a duplicate file should be made to better see the results before adding them to the final version.

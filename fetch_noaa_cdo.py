#!/usr/bin/env python3
import argparse
import csv
import json
import os
import sys
import time
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://www.ncei.noaa.gov/cdo-web/api/v2"
DEFAULT_LIMIT = 1000
DEFAULT_TIMEOUT = 30
DEFAULT_RETRIES = 3


def load_dotenv(path):
    if not path:
        return
    env_path = Path(path)
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def api_get(endpoint, params, token, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES):
    query = urlencode(params, doseq=True)
    url = f"{BASE_URL}/{endpoint}?{query}"
    headers = {
        "token": token,
        "User-Agent": "heat-stress-atlas/1.0",
    }
    for attempt in range(retries):
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
        except (TimeoutError, URLError):
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise


def paginate(endpoint, params, token, sleep_s, timeout, retries):
    offset = 1
    while True:
        params["limit"] = DEFAULT_LIMIT
        params["offset"] = offset
        payload = api_get(endpoint, params, token, timeout=timeout, retries=retries)
        results = payload.get("results", [])
        yield results
        meta = payload.get("metadata", {}).get("resultset", {})
        count = meta.get("count")
        if count is None:
            if len(results) < DEFAULT_LIMIT:
                break
            offset += DEFAULT_LIMIT
        else:
            if offset + DEFAULT_LIMIT > count:
                break
            offset += DEFAULT_LIMIT
        if sleep_s:
            time.sleep(sleep_s)


def municipality_key(name):
    if not name:
        return ""
    return name.split(",", 1)[0].strip().upper()


def to_date(value):
    return date.fromisoformat(str(value)[:10])


def normalize_value(value):
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if v <= -9000:
        return None
    if abs(v) > 200:
        v = v / 10.0
    return v


def c_to_f(val_c):
    return (val_c * 9.0 / 5.0) + 32.0


def format_value(value):
    if value is None:
        return ""
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.1f}"


def fetch_station_list(token, dataset, location, start, end, sleep_s, timeout, retries):
    params = {
        "datasetid": dataset,
        "locationid": location,
        "startdate": start,
        "enddate": end,
        "datatypeid": ["TMAX", "TMIN"],
        "sortfield": "datacoverage",
        "sortorder": "desc",
    }
    stations = []
    for batch in paginate("stations", params, token, sleep_s, timeout, retries):
        stations.extend(batch)
    return stations


def select_stations(stations, count):
    def coverage(st):
        try:
            return float(st.get("datacoverage") or 0)
        except (TypeError, ValueError):
            return 0

    stations_sorted = sorted(stations, key=coverage, reverse=True)
    selected = []
    seen = set()
    for station in stations_sorted:
        name = station.get("name", "")
        muni = municipality_key(name)
        if not muni or muni in seen:
            continue
        if station.get("latitude") is None or station.get("longitude") is None:
            continue
        selected.append(station)
        seen.add(muni)
        if len(selected) >= count:
            break
    if len(selected) < count:
        raise SystemExit(
            f"Only found {len(selected)} unique municipalities, need {count}."
        )
    return selected


def fetch_station_daily(
    token,
    dataset,
    station_id,
    start,
    end,
    units,
    sleep_s,
    timeout,
    retries,
    station_start=None,
    station_end=None,
):
    start_date = to_date(start)
    end_date = to_date(end)
    if station_start:
        start_date = max(start_date, to_date(station_start))
    if station_end:
        end_date = min(end_date, to_date(station_end))
    if start_date > end_date:
        return {}

    params = {
        "datasetid": dataset,
        "datatypeid": ["TMAX", "TMIN"],
        "stationid": station_id,
        "units": units,
    }
    by_date = {}
    for year in range(start_date.year, end_date.year + 1):
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)
        if year_start < start_date:
            year_start = start_date
        if year_end > end_date:
            year_end = end_date

        params["startdate"] = year_start.isoformat()
        params["enddate"] = year_end.isoformat()
        for batch in paginate("data", params, token, sleep_s, timeout, retries):
            for item in batch:
                date_str = item.get("date", "")[:10]
                if not date_str:
                    continue
                dtype = item.get("datatype")
                if dtype not in ("TMAX", "TMIN"):
                    continue
                value = normalize_value(item.get("value"))
                if value is None:
                    continue
                if units == "metric":
                    value = c_to_f(value)
                entry = by_date.setdefault(date_str, {})
                entry[dtype] = value
    return by_date


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fetch NOAA CDO daily TMAX/TMIN for Puerto Rico stations."
    )
    parser.add_argument("--dotenv", default=".env", help="Path to .env file")
    parser.add_argument("--token-env", default="NOAA_TOKEN", help="Env var with token")
    parser.add_argument("--dataset", default="GHCND", help="Dataset ID")
    parser.add_argument("--location", default="FIPS:72", help="Location ID")
    parser.add_argument("--start", default="1960-01-01", help="Start date")
    parser.add_argument("--end", default="2025-12-31", help="End date")
    parser.add_argument("--station-count", type=int, default=15, help="Station count")
    parser.add_argument(
        "--units",
        choices=["standard", "metric"],
        default="standard",
        help="NOAA units (standard=F). Metric values are converted to F for output.",
    )
    parser.add_argument("--sleep", type=float, default=0.2, help="Sleep between calls")
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help="HTTP timeout per request in seconds",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=DEFAULT_RETRIES,
        help="Retry attempts for transient API/network errors",
    )
    parser.add_argument(
        "--out",
        default="data/noaa_pr_1960_2025.csv",
        help="Output CSV path",
    )
    parser.add_argument("--dry-run", action="store_true", help="List stations only")
    return parser.parse_args()


def main():
    args = parse_args()
    load_dotenv(args.dotenv)
    token = os.environ.get(args.token_env)
    if not token:
        raise SystemExit(
            f"Missing token. Set {args.token_env} or add it to {args.dotenv}."
        )

    stations = fetch_station_list(
        token,
        args.dataset,
        args.location,
        args.start,
        args.end,
        args.sleep,
        args.timeout,
        args.retries,
    )
    if not stations:
        raise SystemExit("No stations returned. Check location/dates.")

    selected = select_stations(stations, args.station_count)
    print(f"Selected {len(selected)} stations with unique municipalities:")
    for station in selected:
        name = station.get("name", "")
        coverage = station.get("datacoverage", "")
        print(f"- {name} (coverage {coverage})")

    if args.dry_run:
        return

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "STATION",
        "NAME",
        "LATITUDE",
        "LONGITUDE",
        "ELEVATION",
        "DATE",
        "TMAX",
        "TMIN",
        "TOBS",
    ]

    row_count = 0
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for idx, station in enumerate(selected, start=1):
            station_id = station.get("id")
            name = station.get("name", "")
            lat = station.get("latitude")
            lon = station.get("longitude")
            elev = station.get("elevation")

            if not station_id:
                continue

            print(f"[{idx}/{len(selected)}] Fetching {station_id} {name}")
            by_date = fetch_station_daily(
                token,
                args.dataset,
                station_id,
                args.start,
                args.end,
                args.units,
                args.sleep,
                args.timeout,
                args.retries,
                station.get("mindate"),
                station.get("maxdate"),
            )

            short_id = station_id.replace("GHCND:", "")
            for date in sorted(by_date.keys()):
                entry = by_date[date]
                tmax = entry.get("TMAX")
                tmin = entry.get("TMIN")
                if tmax is None or tmin is None:
                    continue
                writer.writerow(
                    {
                        "STATION": short_id,
                        "NAME": name,
                        "LATITUDE": lat,
                        "LONGITUDE": lon,
                        "ELEVATION": elev,
                        "DATE": date,
                        "TMAX": format_value(tmax),
                        "TMIN": format_value(tmin),
                        "TOBS": "",
                    }
                )
                row_count += 1

    print(f"Wrote {row_count} rows to {out_path}")


if __name__ == "__main__":
    main()

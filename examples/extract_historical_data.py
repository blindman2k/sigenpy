#!/usr/bin/env python3
"""
Extract all historical data from Sigen API up to yesterday.
Uses local cache to avoid re-downloading immutable historical data.
Aggregates data into 30-minute blocks and saves to monthly JSON files.
Designed to be run daily to incrementally collect new data.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sigenpy import SigenAPI, get_config
from datetime import datetime, timedelta
import json
from collections import defaultdict


CACHE_DIR = "../sigen_cache"
DATA_DIR = "../sigen_data"
CACHE_FILE_PATTERN = "{system_id}_history_{date}.json"
MONTHLY_RAW_FILE_PATTERN = "{system_id}_raw_{year}_{month:02d}.json"
MONTHLY_30MIN_FILE_PATTERN = "{system_id}_30min_{year}_{month:02d}.json"


def ensure_cache_dir():
    """Create cache directory if it doesn't exist."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
        print(f"  Created cache directory: {CACHE_DIR}")


def ensure_data_dir():
    """Create data directory if it doesn't exist."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"  Created data directory: {DATA_DIR}")


def get_cache_path(system_id, date_str):
    """Get the cache file path for a specific date."""
    filename = CACHE_FILE_PATTERN.format(system_id=system_id, date=date_str)
    return os.path.join(CACHE_DIR, filename)


def load_from_cache(system_id, date_str):
    """
    Load historical data from cache if available.

    Returns:
        Data if cached, None if not cached
    """
    cache_path = get_cache_path(system_id, date_str)
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            return json.load(f)
    return None


def save_to_cache(system_id, date_str, data):
    """Save historical data to cache."""
    ensure_cache_dir()
    cache_path = get_cache_path(system_id, date_str)
    with open(cache_path, 'w') as f:
        json.dump(data, f, indent=2)


def aggregate_to_30min_blocks(data_points):
    """
    Aggregate data points into 30-minute blocks.

    Args:
        data_points: List of data points with timestamps

    Returns:
        List of aggregated 30-minute blocks
    """
    # Group data by 30-minute blocks
    blocks = defaultdict(list)

    for point in data_points:
        # Extract timestamp - Sigen uses 'dataTime' field in format '20251031 00:00'
        timestamp = point.get('dataTime')

        if timestamp is None:
            print(f"Warning: No dataTime found in data point: {point}")
            continue

        # Parse timestamp to datetime
        try:
            # Parse format: '20251031 00:00'
            dt = datetime.strptime(timestamp, '%Y%m%d %H:%M')
        except:
            print(f"Warning: Could not parse timestamp: {timestamp}")
            continue

        # Round down to nearest 30-minute block
        minutes = (dt.minute // 30) * 30
        block_time = dt.replace(minute=minutes, second=0, microsecond=0)
        block_key = block_time.isoformat()

        blocks[block_key].append(point)

    # Aggregate each block
    aggregated = []
    for block_key in sorted(blocks.keys()):
        block_time = datetime.fromisoformat(block_key)
        points = blocks[block_key]

        # Create aggregated record
        agg_record = {
            'timestamp': block_key,
            'block_start': block_time.isoformat(),
            'block_end': (block_time + timedelta(minutes=30)).isoformat(),
            'data_points_count': len(points),
        }

        # Aggregate numeric values (average)
        numeric_fields = defaultdict(list)
        for point in points:
            for key, value in point.items():
                if key == 'dataTime':  # Skip the timestamp field
                    continue
                if isinstance(value, (int, float)):
                    numeric_fields[key].append(value)

        # Calculate averages
        for field, values in numeric_fields.items():
            if values:
                agg_record[f'{field}_avg'] = sum(values) / len(values)
                agg_record[f'{field}_min'] = min(values)
                agg_record[f'{field}_max'] = max(values)
                agg_record[f'{field}_sum'] = sum(values)

        aggregated.append(agg_record)

    return aggregated


def get_all_cached_dates(system_id):
    """Get all dates that have cached data."""
    cached_dates = []
    if os.path.exists(CACHE_DIR):
        for filename in os.listdir(CACHE_DIR):
            if filename.startswith(f"{system_id}_history_") and filename.endswith(".json"):
                date_str = filename.replace(f"{system_id}_history_", "").replace(".json", "")
                try:
                    cached_dates.append(datetime.strptime(date_str, '%Y-%m-%d').date())
                except:
                    pass
    return sorted(cached_dates)


def group_by_month(data_points):
    """Group data points by year-month."""
    monthly_data = defaultdict(list)
    for point in data_points:
        timestamp = point.get('dataTime')
        if timestamp:
            try:
                dt = datetime.strptime(timestamp, '%Y%m%d %H:%M')
                month_key = (dt.year, dt.month)
                monthly_data[month_key].append(point)
            except:
                pass
    return monthly_data


def save_monthly_files(system_id, all_data_points):
    """Save data points grouped by month into separate files."""
    ensure_data_dir()

    # Group data by month
    monthly_data = group_by_month(all_data_points)

    saved_files = []
    for (year, month), points in sorted(monthly_data.items()):
        # Save raw monthly data
        raw_filename = MONTHLY_RAW_FILE_PATTERN.format(
            system_id=system_id,
            year=year,
            month=month
        )
        raw_path = os.path.join(DATA_DIR, raw_filename)
        with open(raw_path, 'w') as f:
            json.dump(points, f, indent=2)

        # Aggregate to 30-minute blocks for this month
        aggregated = aggregate_to_30min_blocks(points)

        # Save 30-minute aggregated data
        agg_filename = MONTHLY_30MIN_FILE_PATTERN.format(
            system_id=system_id,
            year=year,
            month=month
        )
        agg_path = os.path.join(DATA_DIR, agg_filename)
        with open(agg_path, 'w') as f:
            json.dump(aggregated, f, indent=2)

        saved_files.append({
            'year': year,
            'month': month,
            'raw_file': raw_filename,
            'agg_file': agg_filename,
            'data_points': len(points),
            'blocks': len(aggregated)
        })

    return saved_files


def main():
    print("=" * 70)
    print("Extract Sigen Historical Data with Caching")
    print("=" * 70)

    # Load configuration
    print("\n1. Loading configuration...")
    config = get_config()
    print(f"✓ Config loaded")

    # Initialize API
    print("\n2. Initializing API and authenticating...")
    api = SigenAPI(
        base_url=config['base_url'],
        username=config['username'],
        password=config['password']
    )
    api.login()
    api.get_systems()
    print(f"✓ Authenticated")
    print(f"  System ID: {api.system_id}")

    # Ensure directories exist
    ensure_cache_dir()
    ensure_data_dir()

    # Determine date range: from earliest installation to yesterday
    # System was installed around Oct 3, 2025 based on previous runs
    yesterday = (datetime.now() - timedelta(days=1)).date()

    # Check what dates we already have cached
    cached_dates = get_all_cached_dates(api.system_id)

    if cached_dates:
        start_date = cached_dates[0]  # Continue from earliest cached
        print(f"\n  Found cached data from {start_date} to {cached_dates[-1]}")
    else:
        # Start from when system was likely installed
        start_date = datetime(2025, 10, 1).date()

    end_date = yesterday

    print(f"\n3. Fetching historical data...")
    print(f"  Using 'day' level with 5-minute data points")
    print(f"  Date range: {start_date} to {end_date}")
    print(f"  Cache directory: {CACHE_DIR}")
    print(f"  Data directory: {DATA_DIR}")

    try:
        all_data_points = []
        current_date = start_date
        day_count = 0
        cached_count = 0
        fetched_count = 0
        failed_count = 0

        while current_date <= end_date:
            day_count += 1
            date_str = current_date.strftime('%Y-%m-%d')

            print(f"\n  Day {day_count}: {date_str}...", end=" ")

            # Try to load from cache first
            cached_data = load_from_cache(api.system_id, date_str)

            if cached_data is not None:
                print(f"✓ [CACHED] {len(cached_data)} points")
                all_data_points.extend(cached_data)
                cached_count += 1
            else:
                # Fetch from API
                try:
                    endpoint = f'/openapi/systems/{api.system_id}/history'
                    params = {
                        'date': date_str,
                        'level': 'day'
                    }
                    response = api._make_request('GET', endpoint, params=params)

                    # Check for API limit or access restriction
                    if response.get('code') == 424:
                        print(f"✗ API LIMIT REACHED")
                        print(f"\n  API credit limit reached. Stopping here.")
                        print(f"  Run the script again later to continue from where we left off.")
                        failed_count += 1
                        break
                    elif response.get('code') == 1201:
                        print(f"✗ ACCESS RESTRICTED (date may be before system installation)")
                        failed_count += 1
                    elif response.get('code') != 0:
                        print(f"✗ Error: {response.get('msg')}")
                        failed_count += 1
                    else:
                        history = api._parse_data_field(response)

                        # Extract itemList which contains the 5-minute interval data
                        day_points = []
                        if isinstance(history, dict) and 'itemList' in history:
                            day_points = history['itemList']
                        elif isinstance(history, list):
                            day_points = history

                        # Save to cache
                        save_to_cache(api.system_id, date_str, day_points)

                        all_data_points.extend(day_points)
                        print(f"✓ [FETCHED] {len(day_points)} points")
                        fetched_count += 1

                except Exception as e:
                    print(f"✗ Failed: {e}")
                    failed_count += 1
                    # Check if it's a 424 error
                    if "424" in str(e):
                        print(f"\n  API credit limit reached. Stopping here.")
                        print(f"  Run the script again later to continue from where we left off.")
                        break

            current_date += timedelta(days=1)

        print(f"\n  ✓ Total data points collected: {len(all_data_points)}")
        print(f"\n  Summary:")
        print(f"    - Cached days: {cached_count}")
        print(f"    - Newly fetched days: {fetched_count}")
        print(f"    - Failed days: {failed_count}")

        if not all_data_points:
            print("\n  Warning: No data points retrieved.")
            return

        # Show sample of first data point
        if all_data_points:
            print(f"\n  Sample data point structure:")
            print(f"  {json.dumps(all_data_points[0], indent=4, default=str)}")

        # Save data grouped by month
        print(f"\n4. Saving data grouped by month...")
        saved_files = save_monthly_files(api.system_id, all_data_points)

        print(f"\n  ✓ Saved {len(saved_files)} month(s) of data")
        for file_info in saved_files:
            print(f"    {file_info['year']}-{file_info['month']:02d}: "
                  f"{file_info['data_points']} points → {file_info['blocks']} blocks")

        # Print summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Total raw data points: {len(all_data_points)}")
        print(f"Total months saved: {len(saved_files)}")

        if saved_files:
            print(f"\nMonthly files created in {DATA_DIR}/:")
            for file_info in saved_files:
                print(f"  - {file_info['raw_file']}")
                print(f"  - {file_info['agg_file']}")

        print(f"\nCache directory: {CACHE_DIR}/")
        print(f"  Contains {len(cached_dates) if cached_dates else 0} daily cache files")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "=" * 70)
    print("EXTRACTION COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()

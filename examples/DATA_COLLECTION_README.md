# Sigen Historical Data Collection

Automated data collection system for Sigen solar/battery system with intelligent caching and monthly file organization.

## Quick Start

Run the data collection script:

```bash
python extract_historical_data.py
```

The script will:
1. Authenticate with Sigen API
2. Collect all historical data from system installation to yesterday
3. Use local cache to avoid re-downloading immutable data
4. Save data organized by month

## Directory Structure

```
sigen/
├── extract_historical_data.py    # Main data collection script
├── sigen_cache/                   # Daily cache files (never re-downloaded)
│   └── SERDB1759111111_history_2025-10-01.json
│   └── SERDB1759111111_history_2025-10-02.json
│   └── ...
└── sigen_data/                    # Monthly aggregated data files
    ├── SERDB1759111111_raw_2025_10.json       # Raw 5-minute data
    ├── SERDB1759111111_30min_2025_10.json     # 30-minute aggregated blocks
    ├── SERDB1759111111_raw_2025_11.json
    └── SERDB1759111111_30min_2025_11.json
```

## File Naming Convention

### Monthly Raw Data Files
Format: `{system_id}_raw_{year}_{month:02d}.json`

Example: `SERDB1759111111_raw_2025_10.json`

Contains: Array of 5-minute interval data points for the entire month

### Monthly Aggregated Data Files
Format: `{system_id}_30min_{year}_{month:02d}.json`

Example: `SERDB1759111111_30min_2025_10.json`

Contains: Array of 30-minute blocks with avg/min/max/sum statistics for each metric

## Data Point Structure (5-minute intervals)

```json
{
  "dataTime": "20251031 13:05",
  "pvTotalPower": 8.365,
  "loadPower": 4.573,
  "toGridPower": 3.792,
  "fromGridPower": 0.0,
  "esChargePower": 0.0,
  "esDischargePower": 0.709,
  "batSoc": 35.3,
  "powerGeneration": 0.22,
  "powerUse": 0.15,
  ...
}
```

## 30-Minute Block Structure

```json
{
  "timestamp": "2025-10-31T13:00:00",
  "block_start": "2025-10-31T13:00:00",
  "block_end": "2025-10-31T13:30:00",
  "data_points_count": 6,
  "pvTotalPower_avg": 7.23,
  "pvTotalPower_min": 4.25,
  "pvTotalPower_max": 8.96,
  "pvTotalPower_sum": 43.38,
  "loadPower_avg": 3.54,
  ...
}
```

## Scheduling Daily Runs

### Using cron (Linux/macOS)

Add to crontab (`crontab -e`):

```bash
# Run every day at 1 AM
0 1 * * * cd /path/to/sigen && /usr/bin/python3 extract_historical_data.py >> /path/to/logs/sigen_extract.log 2>&1
```

### Using launchd (macOS)

Create `~/Library/LaunchAgents/com.sigen.extract.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.sigen.extract</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/sigen/extract_historical_data.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>1</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>WorkingDirectory</key>
    <string>/path/to/sigen</string>
    <key>StandardOutPath</key>
    <string>/path/to/logs/sigen_extract.log</string>
    <key>StandardErrorPath</key>
    <string>/path/to/logs/sigen_extract.error.log</string>
</dict>
</plist>
```

Load with: `launchctl load ~/Library/LaunchAgents/com.sigen.extract.plist`

### Using Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 1:00 AM
4. Set action: Start a program
   - Program: `python.exe`
   - Arguments: `extract_historical_data.py`
   - Start in: `C:\path\to\sigen`

## Reading Data from Other Scripts

```python
import json
from datetime import datetime

def load_month_data(system_id, year, month, aggregated=True):
    """
    Load data for a specific month.

    Args:
        system_id: Sigen system ID
        year: Year (e.g., 2025)
        month: Month (1-12)
        aggregated: If True, load 30-min blocks, else load raw 5-min data

    Returns:
        List of data points or blocks
    """
    file_type = "30min" if aggregated else "raw"
    filename = f"sigen_data/{system_id}_{file_type}_{year}_{month:02d}.json"

    with open(filename, 'r') as f:
        return json.load(f)

# Example: Load October 2025 30-minute blocks
data = load_month_data("SERDB1759111111", 2025, 10, aggregated=True)
print(f"Loaded {len(data)} 30-minute blocks")

# Example: Load raw 5-minute data for October 2025
raw_data = load_month_data("SERDB1759111111", 2025, 10, aggregated=False)
print(f"Loaded {len(raw_data)} raw data points")
```

## Caching Behavior

- **Daily cache files** (`sigen_cache/`) are permanent and never re-downloaded
- Historical data is immutable - once cached, it's final
- The script automatically resumes from where it left off
- Safe to run multiple times - only fetches missing data
- Handles API rate limits gracefully

## API Rate Limits

If you hit API rate limits (error code 424):
- Script will stop and save progress
- All fetched data is cached
- Simply run the script again later to continue
- No data is lost or re-downloaded

## Data Fields Reference

### Power Fields (kW)
- `pvTotalPower`: Total PV generation power
- `loadPower`: Total load power consumption
- `toGridPower`: Power exported to grid
- `fromGridPower`: Power imported from grid
- `esChargePower`: Battery charging power
- `esDischargePower`: Battery discharging power

### Energy Fields (kWh - cumulative for the interval)
- `powerGeneration`: Energy generated by PV
- `powerUse`: Total energy consumed
- `powerToGrid`: Energy exported to grid
- `powerFromGrid`: Energy imported from grid
- `esCharging`: Energy charged to battery
- `esDischarging`: Energy discharged from battery

### Battery Fields
- `batSoc`: Battery state of charge (%)
- `esChargeDischargePower`: Net battery power (+ charging, - discharging)

## Troubleshooting

**No data for certain dates:**
- System may not have been installed yet
- API returns "Access restriction" for dates before installation

**API errors:**
- Error 424: Rate limit reached, wait and re-run
- Error 1201: Access restriction (date too early or too late)

**Missing monthly files:**
- Script only creates files for months with data
- Run the script to generate missing months

## Notes

- Data collection starts from October 1, 2025 (or earliest cached date)
- Ends at yesterday (today's incomplete data is excluded)
- Safe to run daily without configuration changes
- Automatically handles month rollovers
- All timestamps in ISO 8601 format

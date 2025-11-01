# SigenPy

A Python client library for the Sigen Cloud API, providing easy access to solar and battery system data.

## Features

- 🔐 Simple authentication with username/password
- 📊 Access realtime and historical data
- 🔋 Monitor battery state, solar generation, and grid interaction
- 💾 Built-in caching for efficient data collection
- 📅 Monthly data aggregation utilities
- 🐍 Type hints and comprehensive documentation

## Installation

```bash
pip install sigenpy
```

Or install from source:

```bash
git clone https://github.com/blindman2k/sigenpy.git
cd sigenpy
pip install -e .
```

## Quick Start

### 1. Configure Credentials

Create a `secrets.json` file (copy from `secrets.json.example`):

```json
{
  "sigen": {
    "base_url": "https://api-aus.sigencloud.com",
    "username": "your-email@example.com",
    "password": "your-password"
  }
}
```

**Note**: Never commit `secrets.json` to version control!

Alternatively, use environment variables:

```bash
export SIGEN_BASE_URL="https://api-aus.sigencloud.com"
export SIGEN_USERNAME="your-email@example.com"
export SIGEN_PASSWORD="your-password"
```

### 2. Basic Usage

```python
from sigenpy import SigenAPI, get_config

# Load configuration
config = get_config()

# Initialize API client
api = SigenAPI(
    base_url=config['base_url'],
    username=config['username'],
    password=config['password']
)

# Authenticate and fetch system info
api.initialize()

# Get realtime data
energy_flow = api.get_system_energy_flow()
print(f"Current solar generation: {energy_flow.get('pvTotalPower')} kW")
print(f"Battery SoC: {energy_flow.get('batSoc')}%")

# Get system summary
summary = api.get_system_summary()
print(summary)

# Get devices
devices = api.get_devices()
for device in devices:
    print(f"{device['deviceType']}: {device['serialNumber']}")
```

## API Reference

### Authentication

```python
# Login and cache system information
api.login()
api.get_systems()  # Caches system_id
api.get_devices()  # Caches inverter_serial_number

# Or use the convenience method
api.initialize()  # Does all of the above
```

### Realtime Data

```python
# System summary with current metrics
summary = api.get_system_summary()

# Energy flow data
energy_flow = api.get_system_energy_flow()

# Device-specific realtime info
device_info = api.get_device_realtime_info()
```

### Historical Data

```python
from datetime import datetime, timedelta

# Get historical data for a specific date
end_time = datetime.now()
start_time = end_time - timedelta(days=7)

history = api.get_system_history(
    start_time=start_time,
    end_time=end_time,
    interval='day'
)
```

### System Information

```python
# List all systems
systems = api.get_systems()
for system in systems:
    print(f"System: {system['systemName']}")
    print(f"  Capacity: {system['pvCapacity']} kW PV, {system['batteryCapacity']} kWh Battery")

# List all devices
devices = api.get_devices()
for device in devices:
    print(f"{device['deviceType']}: {device['status']}")
```

## Data Collection Examples

See the `examples/` directory for complete working examples:

- **`test_get_systems.py`** - Simple authentication and system list
- **`example_usage.py`** - Comprehensive API usage examples
- **`extract_historical_data.py`** - Daily data collection with caching and monthly aggregation

### Running Examples

```bash
cd examples
python test_get_systems.py
python example_usage.py
python extract_historical_data.py
```

## Advanced Usage

### Historical Data Collection with Caching

The library includes utilities for efficiently collecting historical data:

```python
from datetime import datetime
import json

# Fetch data for a specific date (uses 'day' level for 5-minute intervals)
date_str = '2025-10-31'
endpoint = f'/openapi/systems/{api.system_id}/history'
params = {'date': date_str, 'level': 'day'}
response = api._make_request('GET', endpoint, params=params)
history = api._parse_data_field(response)

# Access 5-minute interval data
data_points = history['itemList']
for point in data_points:
    print(f"{point['dataTime']}: {point['pvTotalPower']} kW")
```

See `examples/extract_historical_data.py` for a complete data collection system with:
- Automatic caching to avoid re-downloading
- Monthly file organization
- 30-minute data aggregation
- Resume capability after API rate limits

## Data Structure

### Realtime Data Point (5-minute intervals)

```python
{
    "dataTime": "20251031 13:05",
    "pvTotalPower": 8.365,        # Solar generation (kW)
    "loadPower": 4.573,            # Load consumption (kW)
    "toGridPower": 3.792,          # Export to grid (kW)
    "fromGridPower": 0.0,          # Import from grid (kW)
    "esChargePower": 0.0,          # Battery charging (kW)
    "esDischargePower": 0.709,     # Battery discharging (kW)
    "batSoc": 35.3,                # Battery state of charge (%)
    "powerGeneration": 0.22,       # Energy generated (kWh)
    "powerUse": 0.15,              # Energy consumed (kWh)
    ...
}
```

### Available Metrics

**Power Metrics (kW):**
- `pvTotalPower` - Solar PV generation
- `loadPower` - Total load consumption
- `toGridPower` - Export to grid
- `fromGridPower` - Import from grid
- `esChargePower` - Battery charging
- `esDischargePower` - Battery discharging

**Energy Metrics (kWh):**
- `powerGeneration` - PV energy generated
- `powerUse` - Energy consumed
- `powerToGrid` - Energy exported
- `powerFromGrid` - Energy imported
- `esCharging` - Battery energy charged
- `esDischarging` - Battery energy discharged

**Battery Metrics:**
- `batSoc` - State of charge (%)
- `esChargeDischargePower` - Net power (+ charging, - discharging)

## Error Handling

```python
import requests

try:
    summary = api.get_system_summary()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 424:
        print("API rate limit reached")
    elif e.response.status_code == 500:
        print("Server error")
    else:
        print(f"HTTP error: {e}")
except requests.exceptions.RequestException as e:
    print(f"Network error: {e}")
```

## Configuration

### Using secrets.json (Recommended)

```json
{
  "sigen": {
    "base_url": "https://api-aus.sigencloud.com",
    "username": "your-email@example.com",
    "password": "your-password"
  }
}
```

### Using Environment Variables

```bash
export SIGEN_BASE_URL="https://api-aus.sigencloud.com"
export SIGEN_USERNAME="your-email@example.com"
export SIGEN_PASSWORD="your-password"
```

### Programmatic Configuration

```python
from sigenpy import SigenAPI

api = SigenAPI(
    base_url="https://api-aus.sigencloud.com",
    username="your-email@example.com",
    password="your-password"
)
```

## API Regions

Available base URLs:
- Australia: `https://api-aus.sigencloud.com`
- Europe: `https://api-eu.sigencloud.com`
- Asia: `https://api-sea.sigencloud.com`

## Development

### Setup Development Environment

```bash
git clone https://github.com/blindman2k/sigenpy.git
cd sigenpy
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
pytest --cov=sigenpy
```

### Code Formatting

```bash
black sigenpy/
flake8 sigenpy/
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Disclaimer

This is an unofficial client library for the Sigen Cloud API. It is not affiliated with, endorsed by, or officially connected with Sigen Energy.

## Support

- **Issues**: [GitHub Issues](https://github.com/blindman2k/sigenpy/issues)
- **Documentation**: [GitHub README](https://github.com/blindman2k/sigenpy/blob/main/README.md)

## Changelog

### 0.1.0 (2025-11-01)
- Initial release
- Basic API authentication and data retrieval
- Realtime and historical data access
- Caching utilities
- Monthly data aggregation

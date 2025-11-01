# SigenPy Package Structure

This document describes the organization of the SigenPy library and its files.

## Directory Structure

```
sigen/
├── sigenpy/                      # Main package directory
│   ├── __init__.py               # Package exports
│   ├── sigen_api.py              # Main API client
│   └── sigen_config.py           # Configuration loader
│
├── examples/                      # Example scripts
│   ├── test_get_systems.py       # Simple authentication test
│   ├── example_usage.py          # Comprehensive API demo
│   ├── extract_historical_data.py # Data collection with caching
│   └── DATA_COLLECTION_README.md # Data collection documentation
│
├── sigen_cache/                   # Local data cache (gitignored)
│   └── {system_id}_history_{date}.json
│
├── sigen_data/                    # Monthly data files (gitignored)
│   ├── {system_id}_raw_{year}_{month}.json
│   └── {system_id}_30min_{year}_{month}.json
│
├── README.md                      # Main library documentation
├── LICENSE                        # MIT License
├── setup.py                       # Package setup (traditional)
├── pyproject.toml                 # Package setup (modern)
├── MANIFEST.in                    # Package manifest
├── requirements.txt               # Dependencies
├── .gitignore                     # Git ignore rules
├── secrets.json                   # Credentials (gitignored)
└── secrets.json.example           # Credentials template
```

## File Purposes

### Package Files (`sigenpy/`)

- **`__init__.py`** - Package initialization, exports `SigenAPI`, `get_config`, etc.
- **`sigen_api.py`** - Core API client with all endpoint methods
- **`sigen_config.py`** - Configuration loading from secrets.json or environment variables

### Example Files (`examples/`)

- **`test_get_systems.py`** - Minimal example showing authentication and system listing
- **`example_usage.py`** - Comprehensive examples of all API features
- **`extract_historical_data.py`** - Production-ready data collection script with:
  - Automatic caching to avoid re-downloading
  - Monthly file organization
  - 30-minute data aggregation
  - Resume capability after API rate limits

### Configuration Files

- **`secrets.json`** - Your API credentials (NEVER commit to git)
- **`secrets.json.example`** - Template for creating secrets.json
- **`.gitignore`** - Ensures secrets and data directories are not committed

### Package Metadata

- **`README.md`** - Library documentation with usage examples
- **`LICENSE`** - MIT License
- **`setup.py`** - Traditional Python package setup
- **`pyproject.toml`** - Modern Python package configuration
- **`MANIFEST.in`** - Specifies which files to include in distribution
- **`requirements.txt`** - Runtime dependencies

## gitignored Items

The following are automatically excluded from version control:

### Credentials
- `secrets.json`
- `*.postman_environment.json`
- `*.postman_collection.json`

### Data Directories
- `sigen_cache/` - Daily API response cache
- `sigen_data/` - Monthly aggregated data
- `data/` - Generic data directory
- `cache/` - Generic cache directory

### Python Build Artifacts
- `__pycache__/`
- `*.pyc`
- `dist/`
- `build/`
- `*.egg-info/`

## Installation Methods

### For Users (from PyPI)
```bash
pip install sigenpy
```

### For Development (from source)
```bash
git clone https://github.com/blindman2k/sigenpy.git
cd sigenpy
pip install -e .
```

### For Development with Test Tools
```bash
pip install -e ".[dev]"
```

## Usage Patterns

### Quick Usage
```python
from sigenpy import SigenAPI, get_config

config = get_config()  # Reads secrets.json
api = SigenAPI(**config)
api.initialize()
print(api.get_system_summary())
```

### Data Collection
```bash
cd examples
python extract_historical_data.py
```

Runs daily to incrementally collect new data into monthly files.

## Publishing to PyPI

### Build Distribution
```bash
python -m build
```

### Upload to PyPI
```bash
twine upload dist/*
```

### Test Installation
```bash
pip install sigenpy
python -c "from sigenpy import SigenAPI; print('Success!')"
```

## Data Flow

1. **Authentication**
   - Load credentials from secrets.json
   - Call `/openapi/auth/login/password`
   - Store access token

2. **System Discovery**
   - Call `/openapi/system` to get system list
   - Cache system_id
   - Call `/openapi/system/{id}/devices`
   - Cache inverter serial number

3. **Data Collection** (extract_historical_data.py)
   - For each day from installation to yesterday:
     - Check if cached locally
     - If not cached, fetch from API using `/openapi/systems/{id}/history?date={date}&level=day`
     - Save to `sigen_cache/{system_id}_history_{date}.json`
   - Group all data by month
   - Save raw monthly files to `sigen_data/{system_id}_raw_{year}_{month}.json`
   - Aggregate into 30-minute blocks
   - Save aggregated files to `sigen_data/{system_id}_30min_{year}_{month}.json`

## API Endpoints Used

- `POST /openapi/auth/login/password` - Authentication
- `GET /openapi/system` - List systems
- `GET /openapi/system/{id}/devices` - List devices
- `GET /openapi/systems/{id}/summary` - System summary
- `GET /openapi/systems/{id}/energyFlow` - Energy flow
- `GET /openapi/systems/{id}/devices/{sn}/realtimeInfo` - Device info
- `GET /openapi/systems/{id}/history?date={date}&level=day` - Historical data

## Security Notes

- **Never commit `secrets.json`** - It contains your credentials
- **Never commit Postman files** - They may contain sensitive data
- **Never commit data directories** - They contain your personal energy data
- Use environment variables for CI/CD pipelines
- Rotate credentials regularly

## Contributing

When contributing:
1. Fork the repository
2. Create a feature branch
3. Ensure your changes don't include secrets or personal data
4. Run tests if available
5. Submit a pull request

## Support

- Issues: [GitHub Issues](https://github.com/blindman2k/sigenpy/issues)
- Documentation: This README and inline docstrings
- Examples: See `examples/` directory

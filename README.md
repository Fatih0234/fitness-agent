# ExerciseDB API Client

A Python client library for the ExerciseDB API with both synchronous and asynchronous support.

## Features

- **Dual Mode Support**: Both synchronous and asynchronous API calls
- **Type Hints**: Full type annotations for better IDE support
- **Reference Data Caching**: Cache reference lists to disk for faster access
- **Comprehensive Error Handling**: Custom exceptions for API errors, cache errors, and validation errors
- **URL Encoding**: Proper URL encoding for search parameters
- **Pagination Support**: Built-in pagination for large datasets

## Installation

```bash
pip install -e .
```

Or for development:

```bash
pip install -e ".[dev]"
```

## Configuration

Create a `.env` file in your project root:

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your API key
EXERCISE_DB_API_KEY=your_rapidapi_key_here
EXERCISE_DB_API_HOST=exercisedb.p.rapidapi.com
```

You can get your API key from [RapidAPI](https://rapidapi.com/justin-wolfenberger286/api/exercisedb).

## Usage

### Basic Setup

```python
from exercise_db import ExerciseDBSystem

# Initialize the client
client = ExerciseDBSystem()
```

### Check API Status

```python
# Synchronous
status = client.check_status()
print(status)

# Asynchronous
import asyncio
status = await client.async_check_status()
print(status)
```

### Search Exercises

Search exercises by various filters:

```python
# By body part
exercises = client.search_exercises("bodyPart", "chest")

# By equipment
exercises = client.search_exercises("equipment", "barbell")

# By target muscle
exercises = client.search_exercises("target", "abs")

# With pagination
exercises = client.search_exercises("bodyPart", "legs", limit=20, offset=0)
```

### Get Exercise by ID

```python
exercise = client.get_exercise_by_id("1346")
print(exercise)
```

### List All Exercises

```python
# Get all exercises with pagination
exercises = client.list_all_exercises(limit=100, offset=0)
```

### Fetch Reference Data

Reference lists include body parts, equipment, and target muscles:

```python
# Fetch a single reference list
body_parts = client.fetch_and_cache_reference("bodyPartList")
print(body_parts)

# Fetch all reference data at once
refs = client.fetch_all_reference_data(cache=True)
print(refs)
# Output: {'targetList': [...], 'equipmentList': [...], 'bodyPartList': [...]}
```

### Load Cached Reference Data

```python
# Load from memory cache
cached_data = client.load_cached_reference("bodyPartList")

# Load from file
from_disk = client.load_reference_from_file("data/cached_references/bodyPartList.json")
```

### Exercise Images

```python
# Get exercise image by exercise ID
image_data = client.get_exercise_image("1346")
print(image_data)
```

## Async Usage

All methods have async counterparts:

```python
import asyncio
from exercise_db import ExerciseDBSystem

client = ExerciseDBSystem()

async def main():
    # Fetch data asynchronously
    exercises = await client.async_search_exercises("bodyPart", "back")
    
    # Multiple concurrent requests
    status, refs = await asyncio.gather(
        client.async_check_status(),
        client.async_fetch_all_reference_data()
    )
    
    return exercises, status, refs

exercises, status, refs = asyncio.run(main())
```

## Error Handling

```python
from exercise_db import ExerciseDBSystem, APIError, ValidationError, CacheError

try:
    exercises = client.search_exercises("bodyPart", "chest")
except ValidationError as e:
    print(f"Invalid input: {e}")
except APIError as e:
    print(f"API error: {e}")
except CacheError as e:
    print(f"Cache error: {e}")
```

## Project Structure

```
fitness-app/
├── src/
│   └── exercise_db/
│       ├── __init__.py      # Package exports
│       ├── client.py        # Main client implementation
│       ├── config.py        # Configuration management
│       └── exceptions.py    # Custom exceptions
├── tests/                   # Test suite
├── data/                    # Cache directory
├── .env.example             # Environment variables template
├── .gitignore
└── pyproject.toml          # Project configuration
```

## Development

### Running Tests

```bash
pytest
```

### Linting

```bash
ruff check .
```

### Type Checking

```bash
mypy src/
```

## API Endpoints

The client supports the following ExerciseDB API endpoints:

- **Gateway**: `/status` - Check API status
- **Exercises**: 
  - `/exercises` - List all exercises
  - `/exercises/exercise/{id}` - Get exercise by ID
  - `/exercises/{filter_type}/{value}` - Search exercises
- **Images**: `/image/{exercise_id}` - Get exercise images
- **References**: `/exercises/{list_type}` - Get reference lists (bodyPartList, equipmentList, targetList)

## Requirements

- Python 3.10+
- requests >= 2.31.0
- python-dotenv >= 1.0.0
- aiohttp >= 3.9.0

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues related to the ExerciseDB API itself, please visit the [official API documentation](https://rapidapi.com/justin-wolfenberger286/api/exercisedb).

For issues with this client library, please open an issue on GitHub.

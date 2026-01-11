"""Configuration dataclass for ExerciseDB client"""

from dataclasses import dataclass


@dataclass
class ExerciseConfig:
    """Configuration loaded from .env"""

    api_key: str
    host: str = "exercisedb.p.rapidapi.com"
    cache_dir: str = "data/cached_references"

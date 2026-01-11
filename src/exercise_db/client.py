"""ExerciseDB API Client with async/sync support"""

import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import aiohttp
import requests
from dotenv import load_dotenv

from .config import ExerciseConfig
from .exceptions import APIError, CacheError, ValidationError

load_dotenv()


class ExerciseDBSystem:
    """Async/Sync hybrid ExerciseDB API client"""

    def __init__(self, config: Optional[ExerciseConfig] = None) -> None:
        self.config = config or self._load_config()
        self.base_url = f"https://{self.config.host}"
        self.headers: Dict[str, str] = {
            "x-rapidapi-key": self.config.api_key,
            "x-rapidapi-host": self.config.host,
        }
        self._reference_cache: Dict[str, List[str]] = {}

    def _load_config(self) -> ExerciseConfig:
        """Load configuration from environment variables"""
        api_key = os.getenv("EXERCISE_DB_API_KEY")
        if not api_key:
            raise ValidationError("EXERCISE_DB_API_KEY not found in environment")
        return ExerciseConfig(
            api_key=api_key,
            host=os.getenv("EXERCISE_DB_API_HOST", "exercisedb.p.rapidapi.com"),
            cache_dir=os.getenv("CACHE_DIR", "data/cached_references"),
        )

    def _validate_and_encode(self, value: str) -> str:
        """Validate and URL-encode search parameters"""
        if not value or not isinstance(value, str):
            raise ValidationError(f"Invalid search value: {value}")
        return quote(value, safe="")

    def _get_cache_path(self, list_type: str) -> Path:
        """Get the file path for cached reference data"""
        cache_dir = Path(self.config.cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / f"{list_type}.json"

    def _handle_response(self, response: requests.Response) -> Any:
        """Handle HTTP response and raise errors if needed"""
        if not response.ok:
            raise APIError(
                f"API request failed: {response.status_code} {response.text}",
                status_code=response.status_code,
            )
        return response.json()

    async def _handle_async_response(self, response: aiohttp.ClientResponse) -> Any:
        """Handle async HTTP response and raise errors if needed"""
        if not response.ok:
            raise APIError(
                f"API request failed: {response.status} {await response.text()}",
                status_code=response.status,
            )
        return await response.json()

    # === GATEWAY SERVICE ===

    async def async_check_status(self) -> Dict[str, Any]:
        """Verify API gateway is operational (async)"""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(f"{self.base_url}/status") as response:
                return await self._handle_async_response(response)

    def check_status(self) -> Dict[str, Any]:
        """Verify API gateway is operational (sync)"""
        response = requests.get(
            f"{self.base_url}/status",
            headers=self.headers,
        )
        return self._handle_response(response)

    # === IMAGE SERVICE ===

    async def async_get_exercise_image(self, exercise_id: str) -> Dict[str, Any]:
        """Fetch exercise images (async)"""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(f"{self.base_url}/image/{exercise_id}") as response:
                return await self._handle_async_response(response)

    def get_exercise_image(self, exercise_id: str) -> Dict[str, Any]:
        """Fetch exercise images (sync)"""
        response = requests.get(
            f"{self.base_url}/image/{exercise_id}",
            headers=self.headers,
        )
        return self._handle_response(response)

    # === REFERENCE DATA MANAGEMENT ===

    async def async_fetch_and_cache_reference(
        self,
        list_type: str,
        cache_file: Optional[str] = None,
    ) -> List[str]:
        """Fetch reference list and optionally cache to file (async)"""
        endpoint = f"/exercises/{list_type}"
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(f"{self.base_url}{endpoint}") as response:
                data = await self._handle_async_response(response)

        self._reference_cache[list_type] = data

        if cache_file:
            self._save_to_cache(list_type, data, cache_file)

        return data

    def fetch_and_cache_reference(
        self,
        list_type: str,
        cache_file: Optional[str] = None,
    ) -> List[str]:
        """Fetch reference list and optionally cache to file (sync)"""
        endpoint = f"/exercises/{list_type}"
        response = requests.get(
            f"{self.base_url}{endpoint}",
            headers=self.headers,
        )
        data = self._handle_response(response)

        self._reference_cache[list_type] = data

        if cache_file:
            self._save_to_cache(list_type, data, cache_file)

        return data

    def _save_to_cache(self, list_type: str, data: List[str], filepath: str) -> None:
        """Save reference data to cache file"""
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            raise CacheError(f"Failed to save cache file {filepath}: {e}")

    def _load_from_cache(self, list_type: str) -> Optional[List[str]]:
        """Load reference data from memory cache"""
        return self._reference_cache.get(list_type)

    def load_cached_reference(self, list_type: str) -> Optional[List[str]]:
        """Load reference data from memory cache"""
        return self._load_from_cache(list_type)

    def save_cached_reference(self, list_type: str, cache_file: str) -> None:
        """Save cached reference data to file"""
        data = self._reference_cache.get(list_type)
        if data is None:
            raise CacheError(f"No cached data found for {list_type}")
        self._save_to_cache(list_type, data, cache_file)

    def load_reference_from_file(self, cache_file: str) -> List[str]:
        """Load reference data from file and update memory cache"""
        try:
            path = Path(cache_file)
            with open(path) as f:
                data = json.load(f)
            list_type = path.stem
            self._reference_cache[list_type] = data
            return data
        except OSError as e:
            raise CacheError(f"Failed to load cache file {cache_file}: {e}")

    # === EXERCISE SEARCH ===

    async def async_search_exercises(
        self,
        filter_type: str,
        value: str,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Search exercises with URL encoding (async)"""
        encoded_value = self._validate_and_encode(value)
        url = f"{self.base_url}/exercises/{filter_type}/{encoded_value}"
        params: Dict[str, int] = {"limit": limit, "offset": offset}

        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(url, params=params) as response:
                return await self._handle_async_response(response)

    def search_exercises(
        self,
        filter_type: str,
        value: str,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Search exercises with URL encoding (sync)"""
        encoded_value = self._validate_and_encode(value)
        url = f"{self.base_url}/exercises/{filter_type}/{encoded_value}"
        params: Dict[str, int] = {"limit": limit, "offset": offset}

        response = requests.get(
            url,
            headers=self.headers,
            params=params,
        )
        return self._handle_response(response)

    async def async_get_exercise_by_id(
        self,
        exercise_id: str,
    ) -> Dict[str, Any]:
        """Get single exercise by ID (async)"""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(
                f"{self.base_url}/exercises/exercise/{exercise_id}"
            ) as response:
                return await self._handle_async_response(response)

    def get_exercise_by_id(self, exercise_id: str) -> Dict[str, Any]:
        """Get single exercise by ID (sync)"""
        response = requests.get(
            f"{self.base_url}/exercises/exercise/{exercise_id}",
            headers=self.headers,
        )
        return self._handle_response(response)

    async def async_list_all_exercises(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List all exercises with pagination (async)"""
        params: Dict[str, int] = {"limit": limit, "offset": offset}
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(
                f"{self.base_url}/exercises",
                params=params,
            ) as response:
                return await self._handle_async_response(response)

    def list_all_exercises(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List all exercises with pagination (sync)"""
        params: Dict[str, int] = {"limit": limit, "offset": offset}
        response = requests.get(
            f"{self.base_url}/exercises",
            headers=self.headers,
            params=params,
        )
        return self._handle_response(response)

    # === CONVENIENCE METHODS ===

    async def async_fetch_all_reference_data(
        self, cache: bool = True
    ) -> Dict[str, List[str]]:
        """Fetch all reference lists at once (async)"""
        cache_dir = self._get_cache_path("").parent if cache else None
        results: Dict[str, List[str]] = {}

        for list_type in ["targetList", "equipmentList", "bodyPartList"]:
            cache_file = str(cache_dir / f"{list_type}.json") if cache_dir else None
            results[list_type] = await self.async_fetch_and_cache_reference(
                list_type, cache_file
            )

        return results

    def fetch_all_reference_data(self, cache: bool = True) -> Dict[str, List[str]]:
        """Fetch all reference lists at once (sync)"""
        cache_dir = self._get_cache_path("").parent if cache else None
        results: Dict[str, List[str]] = {}

        for list_type in ["targetList", "equipmentList", "bodyPartList"]:
            cache_file = str(cache_dir / f"{list_type}.json") if cache_dir else None
            results[list_type] = self.fetch_and_cache_reference(list_type, cache_file)

        return results

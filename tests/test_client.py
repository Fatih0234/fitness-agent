"""Unit tests for ExerciseDBSystem client"""

import pytest
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
import json


def _make_async_response(ok: bool, json_data: Any, status: int = 200, text: str = ""):
    """Helper to create a properly configured async response mock"""
    response = MagicMock()
    response.ok = ok
    response.status = status
    response.json = AsyncMock(return_value=json_data)
    response.text = AsyncMock(return_value=text)
    return response


def _make_async_context_manager(return_value):
    """Helper to create a properly configured async context manager"""
    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(return_value=return_value)
    ctx.__aexit__ = AsyncMock(return_value=None)
    return ctx


class TestExerciseDBSystem:
    """Test cases for ExerciseDBSystem class"""

    def test_init_with_config(self, exercise_db_system):
        """Test initialization with custom config"""
        assert exercise_db_system.config.api_key == "test_api_key"
        assert exercise_db_system.config.host == "exercisedb.p.rapidapi.com"
        assert "x-rapidapi-key" in exercise_db_system.headers
        assert exercise_db_system.headers["x-rapidapi-key"] == "test_api_key"

    def test_init_with_env_var(self, monkeypatch):
        """Test initialization loads from environment"""
        from exercise_db.client import ExerciseDBSystem

        monkeypatch.setenv("EXERCISE_DB_API_KEY", "env_api_key")
        monkeypatch.setenv("EXERCISE_DB_API_HOST", "custom.host.com")

        system = ExerciseDBSystem()
        assert system.config.api_key == "env_api_key"
        assert system.config.host == "custom.host.com"

    def test_init_missing_api_key(self, monkeypatch):
        """Test initialization fails without API key"""
        from exercise_db.client import ExerciseDBSystem
        from exercise_db.exceptions import ValidationError

        monkeypatch.delenv("EXERCISE_DB_API_KEY", raising=False)

        with pytest.raises(ValidationError):
            ExerciseDBSystem()


class TestURLEncoding:
    """Test URL encoding and validation"""

    def test_validate_and_encode_simple(self, exercise_db_system):
        """Test encoding simple strings"""
        result = exercise_db_system._validate_and_encode("abs")
        assert result == "abs"

    def test_validate_and_encode_spaces(self, exercise_db_system):
        """Test encoding handles spaces"""
        result = exercise_db_system._validate_and_encode("upper chest")
        assert result == "upper%20chest"

    def test_validate_and_encode_special_chars(self, exercise_db_system):
        """Test encoding special characters"""
        result = exercise_db_system._validate_and_encode("chest (major)")
        assert "%28" in result
        assert "%29" in result

    def test_validate_and_encode_empty_string(self, exercise_db_system):
        """Test validation rejects empty strings"""
        from exercise_db.exceptions import ValidationError

        with pytest.raises(ValidationError):
            exercise_db_system._validate_and_encode("")

    def test_validate_and_encode_none(self, exercise_db_system):
        """Test validation rejects None"""
        from exercise_db.exceptions import ValidationError

        with pytest.raises(ValidationError):
            exercise_db_system._validate_and_encode(None)  # type: ignore


class TestGatewayService:
    """Test Gateway Service endpoints"""

    def test_check_status_sync(self, exercise_db_system, mock_requests_get):
        """Test sync status check"""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": "ok", "message": "Test passed"}
        mock_requests_get.return_value = mock_response

        result = exercise_db_system.check_status()

        assert result == {"status": "ok", "message": "Test passed"}
        mock_requests_get.assert_called_once()
        call_args = mock_requests_get.call_args
        assert "status" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_check_status_async(self, exercise_db_system):
        """Test async status check"""
        mock_response = _make_async_response(True, {"status": "ok"})
        mock_get_ctx = _make_async_context_manager(mock_response)
        mock_session = MagicMock()
        mock_session.get.return_value = mock_get_ctx
        mock_session_ctx = _make_async_context_manager(mock_session)

        with patch("aiohttp.ClientSession", return_value=mock_session_ctx):
            result = await exercise_db_system.async_check_status()

        assert result == {"status": "ok"}


class TestImageService:
    """Test Image Service endpoints"""

    def test_get_exercise_image_sync(
        self, exercise_db_system, mock_requests_get, sample_exercise_response
    ):
        """Test sync image fetch"""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "images": ["url1.jpg", "url2.jpg"],
            "exercise": sample_exercise_response,
        }
        mock_requests_get.return_value = mock_response

        result = exercise_db_system.get_exercise_image("0001")

        assert "images" in result
        mock_requests_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_exercise_image_async(
        self, exercise_db_system, sample_exercise_response
    ):
        """Test async image fetch"""
        mock_response = _make_async_response(
            True, {"images": ["url1.jpg"], "exercise": sample_exercise_response}
        )
        mock_get_ctx = _make_async_context_manager(mock_response)
        mock_session = MagicMock()
        mock_session.get.return_value = mock_get_ctx
        mock_session_ctx = _make_async_context_manager(mock_session)

        with patch("aiohttp.ClientSession", return_value=mock_session_ctx):
            result = await exercise_db_system.async_get_exercise_image("0001")

        assert "images" in result


class TestReferenceData:
    """Test reference data fetching and caching"""

    def test_fetch_reference_list_sync(
        self, exercise_db_system, mock_requests_get, sample_reference_list
    ):
        """Test sync reference list fetch"""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = sample_reference_list
        mock_requests_get.return_value = mock_response

        result = exercise_db_system.fetch_and_cache_reference("targetList")

        assert result == sample_reference_list
        assert "targetList" in exercise_db_system._reference_cache
        mock_requests_get.assert_called_once()

    def test_fetch_reference_with_cache_file(
        self,
        exercise_db_system,
        mock_requests_get,
        sample_reference_list,
        tmp_path,
    ):
        """Test reference list fetch with file caching"""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = sample_reference_list
        mock_requests_get.return_value = mock_response

        cache_file = tmp_path / "targetList.json"
        result = exercise_db_system.fetch_and_cache_reference(
            "targetList", cache_file=str(cache_file)
        )

        assert result == sample_reference_list
        assert cache_file.exists()
        with open(cache_file) as f:
            loaded = json.load(f)
        assert loaded == sample_reference_list

    def test_load_cached_reference(self, exercise_db_system, sample_reference_list):
        """Test loading from memory cache"""
        exercise_db_system._reference_cache["bodyPartList"] = sample_reference_list

        result = exercise_db_system.load_cached_reference("bodyPartList")

        assert result == sample_reference_list

    def test_load_cached_reference_missing(self, exercise_db_system):
        """Test loading non-existent cache returns None"""
        result = exercise_db_system.load_cached_reference("nonexistent")

        assert result is None

    def test_save_cached_reference(
        self, exercise_db_system, sample_reference_list, tmp_path
    ):
        """Test saving cached reference to file"""
        exercise_db_system._reference_cache["targetList"] = sample_reference_list
        cache_file = tmp_path / "save_test.json"

        exercise_db_system.save_cached_reference("targetList", str(cache_file))

        assert cache_file.exists()
        with open(cache_file) as f:
            assert json.load(f) == sample_reference_list

    def test_save_cached_reference_missing(self, exercise_db_system, tmp_path):
        """Test saving non-existent cache raises error"""
        from exercise_db.exceptions import CacheError

        with pytest.raises(CacheError):
            exercise_db_system.save_cached_reference(
                "missingList", str(tmp_path / "test.json")
            )

    def test_load_reference_from_file(
        self, exercise_db_system, sample_reference_list, tmp_path
    ):
        """Test loading reference from file"""
        cache_file = tmp_path / "fileLoad.json"
        with open(cache_file, "w") as f:
            json.dump(sample_reference_list, f)

        result = exercise_db_system.load_reference_from_file(str(cache_file))

        assert result == sample_reference_list
        assert "fileLoad" in exercise_db_system._reference_cache

    def test_load_reference_from_file_missing(self, exercise_db_system, tmp_path):
        """Test loading non-existent file raises error"""
        from exercise_db.exceptions import CacheError

        with pytest.raises(CacheError):
            exercise_db_system.load_reference_from_file(
                str(tmp_path / "nonexistent.json")
            )

    @pytest.mark.asyncio
    async def test_async_fetch_reference(
        self, exercise_db_system, sample_reference_list
    ):
        """Test async reference list fetch"""
        mock_response = _make_async_response(True, sample_reference_list)
        mock_get_ctx = _make_async_context_manager(mock_response)
        mock_session = MagicMock()
        mock_session.get.return_value = mock_get_ctx
        mock_session_ctx = _make_async_context_manager(mock_session)

        with patch("aiohttp.ClientSession", return_value=mock_session_ctx):
            result = await exercise_db_system.async_fetch_and_cache_reference(
                "equipmentList"
            )

            assert result == sample_reference_list
            assert "equipmentList" in exercise_db_system._reference_cache


class TestExerciseSearch:
    """Test exercise search functionality"""

    def test_search_exercises_sync(
        self, exercise_db_system, mock_requests_get, sample_exercises_list
    ):
        """Test sync exercise search"""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = sample_exercises_list
        mock_requests_get.return_value = mock_response

        result = exercise_db_system.search_exercises(
            filter_type="target", value="chest", limit=10
        )

        assert result == sample_exercises_list
        call_args = mock_requests_get.call_args
        assert "chest" in call_args[0][0]
        assert call_args[1]["params"]["limit"] == 10

    def test_search_exercises_with_encoding(
        self, exercise_db_system, mock_requests_get
    ):
        """Test search properly URL-encodes values"""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = []
        mock_requests_get.return_value = mock_response

        exercise_db_system.search_exercises(filter_type="name", value="push up")

        call_args = mock_requests_get.call_args
        assert "push%20up" in call_args[0][0]

    def test_get_exercise_by_id_sync(
        self, exercise_db_system, mock_requests_get, sample_exercise_response
    ):
        """Test sync get exercise by ID"""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = sample_exercise_response
        mock_requests_get.return_value = mock_response

        result = exercise_db_system.get_exercise_by_id("0001")

        assert result == sample_exercise_response
        mock_requests_get.assert_called_once()
        call_args = mock_requests_get.call_args
        assert "0001" in call_args[0][0]

    def test_list_all_exercises_sync(
        self, exercise_db_system, mock_requests_get, sample_exercises_list
    ):
        """Test sync list all exercises"""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = sample_exercises_list
        mock_requests_get.return_value = mock_response

        result = exercise_db_system.list_all_exercises(limit=50)

        assert result == sample_exercises_list
        assert mock_requests_get.call_args[1]["params"]["limit"] == 50

    @pytest.mark.asyncio
    async def test_async_search_exercises(
        self, exercise_db_system, sample_exercises_list
    ):
        """Test async exercise search"""
        mock_response = _make_async_response(True, sample_exercises_list)
        mock_get_ctx = _make_async_context_manager(mock_response)
        mock_session = MagicMock()
        mock_session.get.return_value = mock_get_ctx
        mock_session_ctx = _make_async_context_manager(mock_session)

        with patch("aiohttp.ClientSession", return_value=mock_session_ctx):
            result = await exercise_db_system.async_search_exercises(
                filter_type="target", value="abs"
            )

            assert result == sample_exercises_list

    @pytest.mark.asyncio
    async def test_async_get_exercise_by_id(
        self, exercise_db_system, sample_exercise_response
    ):
        """Test async get exercise by ID"""
        mock_response = _make_async_response(True, sample_exercise_response)
        mock_get_ctx = _make_async_context_manager(mock_response)
        mock_session = MagicMock()
        mock_session.get.return_value = mock_get_ctx
        mock_session_ctx = _make_async_context_manager(mock_session)

        with patch("aiohttp.ClientSession", return_value=mock_session_ctx):
            result = await exercise_db_system.async_get_exercise_by_id("0001")

            assert result == sample_exercise_response

    @pytest.mark.asyncio
    async def test_async_list_all_exercises(
        self, exercise_db_system, sample_exercises_list
    ):
        """Test async list all exercises"""
        mock_response = _make_async_response(True, sample_exercises_list)
        mock_get_ctx = _make_async_context_manager(mock_response)
        mock_session = MagicMock()
        mock_session.get.return_value = mock_get_ctx
        mock_session_ctx = _make_async_context_manager(mock_session)

        with patch("aiohttp.ClientSession", return_value=mock_session_ctx):
            result = await exercise_db_system.async_list_all_exercises(limit=100)

            assert result == sample_exercises_list


class TestConvenienceMethods:
    """Test convenience/helper methods"""

    def test_fetch_all_reference_data(
        self, exercise_db_system, mock_requests_get, sample_reference_list
    ):
        """Test fetching all reference lists at once"""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = sample_reference_list
        mock_requests_get.return_value = mock_response

        result = exercise_db_system.fetch_all_reference_data(cache=False)

        assert "targetList" in result
        assert "equipmentList" in result
        assert "bodyPartList" in result
        assert mock_requests_get.call_count == 3

    @pytest.mark.asyncio
    async def test_async_fetch_all_reference(
        self, exercise_db_system, sample_reference_list
    ):
        """Test async fetching all reference lists"""
        mock_response = _make_async_response(True, sample_reference_list)
        mock_get_ctx = _make_async_context_manager(mock_response)
        mock_session = MagicMock()
        mock_session.get.return_value = mock_get_ctx
        mock_session_ctx = _make_async_context_manager(mock_session)

        with patch("aiohttp.ClientSession", return_value=mock_session_ctx):
            result = await exercise_db_system.async_fetch_all_reference_data(
                cache=False
            )

            assert "targetList" in result
            assert "equipmentList" in result
            assert "bodyPartList" in result


class TestErrorHandling:
    """Test error handling"""

    def test_handle_response_error(self, exercise_db_system, mock_requests_get):
        """Test HTTP error handling"""
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_requests_get.return_value = mock_response

        from exercise_db.exceptions import APIError

        with pytest.raises(APIError) as exc_info:
            exercise_db_system.check_status()

        assert exc_info.value.status_code == 429

    @pytest.mark.asyncio
    async def test_async_handle_response_error(self, exercise_db_system):
        """Test async HTTP error handling"""
        from exercise_db.exceptions import APIError

        mock_response = _make_async_response(False, {}, status=500, text="Server error")
        mock_response.text.return_value = "Server error"
        mock_get_ctx = _make_async_context_manager(mock_response)
        mock_session = MagicMock()
        mock_session.get.return_value = mock_get_ctx
        mock_session_ctx = _make_async_context_manager(mock_session)

        with patch("aiohttp.ClientSession", return_value=mock_session_ctx):
            with pytest.raises(APIError) as exc_info:
                await exercise_db_system.async_check_status()

            assert exc_info.value.status_code == 500

    def test_get_cache_path(self, exercise_db_system):
        """Test cache path generation"""
        path = exercise_db_system._get_cache_path("targetList")

        assert "targetList.json" in str(path)
        assert path.parent.name == "cached_references"

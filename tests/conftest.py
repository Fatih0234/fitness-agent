"""Pytest configuration and fixtures"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_config():
    """Create a mock ExerciseConfig"""
    from exercise_db.config import ExerciseConfig

    return ExerciseConfig(
        api_key="test_api_key",
        host="exercisedb.p.rapidapi.com",
        cache_dir="data/cached_references",
    )


@pytest.fixture
def exercise_db_system(mock_config):
    """Create an ExerciseDBSystem instance with mock config"""
    from exercise_db.client import ExerciseDBSystem

    return ExerciseDBSystem(config=mock_config)


@pytest.fixture
def sample_exercise_response():
    """Sample exercise data for testing"""
    return {
        "id": "0001",
        "name": "Push Up",
        "target": "chest",
        "equipment": "body",
        "bodyPart": "chest",
        "instructions": ["Step 1", "Step 2"],
        "gifUrl": "https://example.com/pushup.gif",
    }


@pytest.fixture
def sample_exercises_list():
    """Sample list of exercises for testing"""
    return [
        {
            "id": "0001",
            "name": "Push Up",
            "target": "chest",
            "equipment": "body",
            "bodyPart": "chest",
        },
        {
            "id": "0002",
            "name": "Dumbbell Press",
            "target": "chest",
            "equipment": "dumbbell",
            "bodyPart": "chest",
        },
    ]


@pytest.fixture
def sample_reference_list():
    """Sample reference list for testing"""
    return ["abs", "biceps", "chest", "back", "legs"]


@pytest.fixture
def mock_requests_get():
    """Mock requests.get for sync tests"""
    with patch("requests.get") as mock:
        yield mock

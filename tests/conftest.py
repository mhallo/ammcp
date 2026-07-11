import subprocess
from unittest.mock import MagicMock

import pytest


def completed_process(stdout: str = "", returncode: int = 0, stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        args=["osascript", "-l", "JavaScript"], returncode=returncode, stdout=stdout, stderr=stderr
    )


@pytest.fixture
def cp():
    return completed_process


@pytest.fixture
def mock_run(monkeypatch):
    """Replace subprocess.run in ammcp.music_control so tests don't touch the real Music.app."""
    mock = MagicMock()
    monkeypatch.setattr("ammcp.music_control.subprocess.run", mock)
    return mock

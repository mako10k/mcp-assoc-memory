"""
テストモジュール
"""

import asyncio
import shutil
import tempfile
from pathlib import Path
from typing import Any, Generator

import pytest

# テスト用のデータディレクトリ
TEST_DATA_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """一時ディレクトリを提供"""
    temp_path = Path(tempfile.mkdtemp())
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def event_loop():
    """イベントループを提供"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


class TestConfig:
    """テスト設定"""

    @staticmethod
    def get_test_database_path(temp_dir: Path) -> str:
        """テスト用データベースパスを取得"""
        return str(temp_dir / "test_memory.db")

    @staticmethod
    def get_test_data_dir(temp_dir: Path) -> str:
        """テスト用データディレクトリを取得"""
        data_dir = temp_dir / "data"
        data_dir.mkdir(exist_ok=True)
        return str(data_dir)

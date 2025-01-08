"""Tests for the DataComparisonCore class."""

import pandas as pd
import pytest
from io import StringIO, BytesIO
from datacompy_web_ui.core.comparison import DataComparisonCore

# Sample CSV data for testing
BASE_CSV = """id,name,value
1,John,100
2,Jane,200
3,Bob,300"""

COMPARE_CSV = """id,name,value
1,John,100
2,Jane,250
4,Alice,400"""


class MockFileContent:
    def __init__(self, content, name):
        self.content = content
        self.name = name
        self._file = BytesIO(content.encode("utf-8"))

    def read(self, size=-1):
        return self._file.read(size)

    def seek(self, pos, whence=0):
        return self._file.seek(pos, whence)

    def tell(self):
        return self._file.tell()

    def __iter__(self):
        self.seek(0)
        return iter(self.content.splitlines())

    @property
    def buffer(self):
        return self._file


@pytest.fixture
def comparison():
    return DataComparisonCore()


@pytest.fixture
def base_file():
    return MockFileContent(BASE_CSV, "base.csv")


@pytest.fixture
def compare_file():
    return MockFileContent(COMPARE_CSV, "compare.csv")


def test_load_data(comparison, base_file, compare_file):
    success, error = comparison.load_data(
        files={"file1": base_file, "file2": compare_file}, options={}
    )
    assert success
    assert error == ""
    assert comparison.df1 is not None
    assert comparison.df2 is not None
    assert len(comparison.df1) == 3
    assert len(comparison.df2) == 3


def test_get_column_info(comparison, base_file, compare_file):
    comparison.load_data(files={"file1": base_file, "file2": compare_file}, options={})
    info = comparison.get_column_info(comparison.df1)

    assert "Column Name" in info.columns
    assert "Type" in info.columns
    assert "Non-Null Count" in info.columns
    assert len(info) == 3  # id, name, value columns


def test_get_join_column_stats(comparison, base_file, compare_file):
    comparison.load_data(files={"file1": base_file, "file2": compare_file}, options={})
    stats = comparison.get_join_column_stats()

    assert len(stats) == 3  # id, name, value columns
    assert any(stat["Column"] == "id" for stat in stats)
    assert any(stat["Column"] == "name" for stat in stats)
    assert any(stat["Column"] == "value" for stat in stats)


def test_compare_data(comparison, base_file, compare_file):
    comparison.load_data(files={"file1": base_file, "file2": compare_file}, options={})
    result = comparison.compare_data(["id"])

    assert result is not None
    assert comparison.comparison is not None


def test_get_comparison_stats(comparison, base_file, compare_file):
    comparison.load_data(files={"file1": base_file, "file2": compare_file}, options={})
    comparison.compare_data(["id"])
    stats = comparison.get_comparison_stats()

    assert stats["rows_in_common"] == 2  # Records with id 1 and 2
    assert stats["unmatched_base"] == 1  # Record with id 3
    assert stats["unmatched_compare"] == 1  # Record with id 4
    assert stats["total_base"] == 3
    assert stats["total_compare"] == 3


def test_load_data_with_invalid_file(comparison):
    invalid_csv = "a,b,c\n1,2\nx,y,z,w"
    invalid_file = MockFileContent(invalid_csv, "invalid.csv")

    success, error = comparison.load_data(
        files={"file1": invalid_file, "file2": invalid_file}, options={}
    )
    assert not success
    assert error != ""

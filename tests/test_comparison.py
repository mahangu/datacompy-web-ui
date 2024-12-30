"""Tests for the DataComparisonCore class."""
import pandas as pd
import pytest
from io import StringIO
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

@pytest.fixture
def comparison():
    """Create a DataComparisonCore instance for testing."""
    return DataComparisonCore()

@pytest.fixture
def base_file(tmp_path):
    """Create a temporary base CSV file."""
    file = tmp_path / "base.csv"
    file.write_text(BASE_CSV)
    return str(file)

@pytest.fixture
def compare_file(tmp_path):
    """Create a temporary compare CSV file."""
    file = tmp_path / "compare.csv"
    file.write_text(COMPARE_CSV)
    return str(file)

def test_load_data(comparison, base_file, compare_file):
    """Test loading CSV files."""
    success, error = comparison.load_data(base_file, compare_file)
    assert success
    assert error == ""
    assert comparison.df1 is not None
    assert comparison.df2 is not None
    assert len(comparison.df1) == 3
    assert len(comparison.df2) == 3

def test_get_column_info(comparison, base_file, compare_file):
    """Test getting column information."""
    comparison.load_data(base_file, compare_file)
    info = comparison.get_column_info(comparison.df1)
    
    assert 'Column Name' in info.columns
    assert 'Type' in info.columns
    assert 'Non-Null Count' in info.columns
    assert len(info) == 3  # id, name, value columns

def test_get_join_column_stats(comparison, base_file, compare_file):
    """Test getting join column statistics."""
    comparison.load_data(base_file, compare_file)
    stats = comparison.get_join_column_stats()
    
    assert len(stats) == 3  # id, name, value columns
    assert any(stat['Column'] == 'id' for stat in stats)
    assert any(stat['Column'] == 'name' for stat in stats)
    assert any(stat['Column'] == 'value' for stat in stats)

def test_compare_data(comparison, base_file, compare_file):
    """Test data comparison functionality."""
    comparison.load_data(base_file, compare_file)
    result = comparison.compare_data(['id'])
    
    assert result is not None
    assert comparison.comparison is not None

def test_get_comparison_stats(comparison, base_file, compare_file):
    """Test getting comparison statistics."""
    comparison.load_data(base_file, compare_file)
    comparison.compare_data(['id'])
    stats = comparison.get_comparison_stats()
    
    assert stats['rows_in_common'] == 2  # Records with id 1 and 2
    assert stats['unmatched_base'] == 1  # Record with id 3
    assert stats['unmatched_compare'] == 1  # Record with id 4
    assert stats['total_base'] == 3
    assert stats['total_compare'] == 3

def test_load_data_with_invalid_file(comparison, tmp_path):
    """Test loading invalid CSV files."""
    invalid_file = tmp_path / "invalid.csv"
    # Create a truly invalid CSV with mismatched columns
    invalid_file.write_text("a,b,c\n1,2\nx,y,z,w")
    
    success, error = comparison.load_data(str(invalid_file), str(invalid_file))
    assert not success
    assert error != "" 
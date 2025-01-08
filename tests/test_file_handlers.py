import pytest
import pandas as pd
from io import BytesIO
import openpyxl
from datacompy_web_ui.core.file_handlers import (
    FileHandler,
    CSVHandler,
    ExcelHandler,
    get_handler,
)


class MockFileName:
    def __init__(self, name):
        self.name = name


def test_base_handler():
    handler = FileHandler()
    with pytest.raises(NotImplementedError):
        handler.read_data(None)
    assert handler.get_options(None) == {}


def test_csv_handler():
    handler = CSVHandler()
    # Test file type detection
    assert handler.can_handle(MockFileName("test.csv"))
    assert not handler.can_handle(MockFileName("test.xlsx"))
    # Test reading CSV data
    csv_data = "a,b\n1,2\n3,4"
    file = BytesIO(csv_data.encode())
    file.name = "test.csv"
    df = handler.read_data(file)
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (2, 2)
    # Test options
    assert handler.get_options(None) == {}


def test_excel_handler():
    handler = ExcelHandler()
    # Test file type detection
    assert handler.can_handle(MockFileName("test.xlsx"))
    assert handler.can_handle(MockFileName("test.xls"))
    assert not handler.can_handle(MockFileName("test.csv"))
    # Create test Excel file
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws["A1"] = "a"
    ws["B1"] = "b"
    ws["A2"] = 1
    ws["B2"] = 2
    # Add second sheet
    ws2 = wb.create_sheet("Sheet2")
    ws2["A1"] = "x"
    ws2["B1"] = "y"
    # Save to BytesIO
    excel_file = BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)
    excel_file.name = "test.xlsx"
    # Test getting sheet names
    options = handler.get_options(excel_file)
    assert "sheet_name" in options
    assert "Sheet1" in options["sheet_name"]
    assert "Sheet2" in options["sheet_name"]
    # Test reading with sheet selection
    excel_file.seek(0)
    df = handler.read_data(excel_file, sheet_name="Sheet1")
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (1, 2)
    assert list(df.columns) == ["a", "b"]


def test_get_handler():
    # Test CSV handler
    csv_file = MockFileName("test.csv")
    handler = get_handler(csv_file)
    assert isinstance(handler, CSVHandler)
    # Test Excel handler
    excel_file = MockFileName("test.xlsx")
    handler = get_handler(excel_file)
    assert isinstance(handler, ExcelHandler)
    # Test unsupported file type
    text_file = MockFileName("test.txt")
    handler = get_handler(text_file)
    assert handler is None

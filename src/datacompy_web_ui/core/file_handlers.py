"""File handlers for different data formats.

This module provides a pluggable system for handling different file formats in the application.
New file formats can be supported by implementing the FileHandler interface.
"""

from typing import Optional, Dict, Any
import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class FileHandler:
    """Base class for file format handlers.

    This class defines the interface that all file handlers must implement.
    To add support for a new file format, subclass this class and implement
    the required methods.

    Attributes:
        supported_extensions (set[str]): Set of file extensions this handler supports.
            Should be defined by subclasses (e.g., {'.csv'}, {'.xlsx', '.xls'}).
    """

    def can_handle(self, file) -> bool:
        """Check if this handler can process the given file.

        Args:
            file: A file-like object with a 'name' attribute.

        Returns:
            bool: True if this handler can process the file, False otherwise.
        """
        return Path(file.name).suffix.lower() in self.supported_extensions

    def read_data(self, file, **options) -> pd.DataFrame:
        """Read data from file into a pandas DataFrame.

        Args:
            file: A file-like object containing the data.
            **options: Additional options specific to the file format.

        Returns:
            pd.DataFrame: The data read from the file.

        Raises:
            NotImplementedError: This is an abstract method that must be implemented
                by subclasses.
        """
        raise NotImplementedError

    def get_options(self, file) -> Dict[str, Any]:
        """Get additional options needed for this file type.

        This method allows handlers to specify additional options that might
        be needed when reading the file (e.g., sheet names for Excel files).

        Args:
            file: A file-like object to get options for.

        Returns:
            Dict[str, Any]: A dictionary of options specific to this file type.
                Empty dict if no additional options are needed.
        """
        return {}


class CSVHandler(FileHandler):
    """Handler for CSV files.

    A simple handler for CSV files that uses pandas read_csv under the hood.
    """

    supported_extensions = {".csv"}

    def read_data(self, file, **options) -> pd.DataFrame:
        """Read data from a CSV file.

        Args:
            file: A file-like object containing CSV data.
            **options: Additional options passed to pd.read_csv.

        Returns:
            pd.DataFrame: The data read from the CSV file.

        Raises:
            Exception: If there's an error reading the CSV file.
        """
        try:
            file.seek(0)  # Reset file pointer
            return pd.read_csv(file)
        except Exception as e:
            logger.error(f"Error reading CSV: {str(e)}")
            raise


class ExcelHandler(FileHandler):
    """Handler for Excel files.

    Supports both .xlsx and .xls files using pandas read_excel.
    Provides sheet selection functionality.
    """

    supported_extensions = {".xlsx", ".xls"}

    def read_data(self, file, **options) -> pd.DataFrame:
        """Read data from an Excel file.

        Args:
            file: A file-like object containing Excel data.
            **options: Additional options passed to pd.read_excel.
                Important options:
                    sheet_name (str): Name of the sheet to read.

        Returns:
            pd.DataFrame: The data read from the Excel file.

        Raises:
            Exception: If there's an error reading the Excel file.
        """
        try:
            sheet_name = options.get("sheet_name")
            logger.debug(f"Reading Excel file with sheet: {sheet_name}")
            return pd.read_excel(file, sheet_name=sheet_name)
        except Exception as e:
            logger.error(f"Error reading Excel file: {str(e)}")
            raise

    def get_options(self, file) -> Dict[str, Any]:
        """Get available sheet names from the Excel file.

        Args:
            file: A file-like object containing Excel data.

        Returns:
            Dict[str, Any]: Dictionary containing 'sheet_name' key with
                a list of available sheet names.

        Raises:
            Exception: If there's an error reading the Excel file structure.
        """
        try:
            sheets = pd.ExcelFile(file).sheet_names
            logger.debug(f"Found sheets: {sheets}")
            return {"sheet_name": sheets}
        except Exception as e:
            logger.error(f"Error getting Excel sheets: {str(e)}")
            raise


def get_handler(file) -> Optional[FileHandler]:
    """Get appropriate handler for a file based on its extension.

    Factory function that returns the appropriate handler for a given file.

    Args:
        file: A file-like object with a 'name' attribute.

    Returns:
        Optional[FileHandler]: An instance of the appropriate handler class,
            or None if no suitable handler is found.
    """
    handlers = [CSVHandler(), ExcelHandler()]
    for handler in handlers:
        if handler.can_handle(file):
            logger.debug(f"Using handler {handler.__class__.__name__} for {file.name}")
            return handler
    logger.warning(f"No handler found for file: {file.name}")
    return None

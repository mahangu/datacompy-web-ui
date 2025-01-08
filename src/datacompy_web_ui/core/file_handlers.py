"""File handlers for different data formats."""

from typing import Optional, Dict, Any
import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class FileHandler:
    """Base class for file handlers."""

    def can_handle(self, file) -> bool:
        """Check if this handler can process the file."""
        return Path(file.name).suffix.lower() in self.supported_extensions

    def read_data(self, file, **options) -> pd.DataFrame:
        """Read data from file into a pandas DataFrame."""
        raise NotImplementedError

    def get_options(self, file) -> Dict[str, Any]:
        """Get additional options needed for this file type."""
        return {}


class CSVHandler(FileHandler):
    """Handler for CSV files."""

    supported_extensions = {".csv"}

    def read_data(self, file, **options) -> pd.DataFrame:
        try:
            file.seek(0)  # Reset file pointer
            return pd.read_csv(file)
        except Exception as e:
            logger.error(f"Error reading CSV: {str(e)}")
            raise


class ExcelHandler(FileHandler):
    """Handler for Excel files."""

    supported_extensions = {".xlsx", ".xls"}

    def read_data(self, file, **options) -> pd.DataFrame:
        try:
            sheet_name = options.get("sheet_name")
            logger.debug(f"Reading Excel file with sheet: {sheet_name}")
            return pd.read_excel(file, sheet_name=sheet_name)
        except Exception as e:
            logger.error(f"Error reading Excel file: {str(e)}")
            raise

    def get_options(self, file) -> Dict[str, Any]:
        try:
            sheets = pd.ExcelFile(file).sheet_names
            logger.debug(f"Found sheets: {sheets}")
            return {"sheet_name": sheets}
        except Exception as e:
            logger.error(f"Error getting Excel sheets: {str(e)}")
            raise


def get_handler(file) -> Optional[FileHandler]:
    """Get appropriate handler for a file."""
    handlers = [CSVHandler(), ExcelHandler()]
    for handler in handlers:
        if handler.can_handle(file):
            logger.debug(f"Using handler {handler.__class__.__name__} for {file.name}")
            return handler
    logger.warning(f"No handler found for file: {file.name}")
    return None

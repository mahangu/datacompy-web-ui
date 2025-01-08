"""Core functionality for Datacompy Web UI.

This module provides the core comparison functionality, wrapping DataCompy
to provide a high-level interface for file comparison operations.
"""

from typing import Tuple, Optional, Dict, List
import datacompy
import pandas as pd
import logging
from .file_handlers import get_handler

logger = logging.getLogger(__name__)


class DataComparisonCore:
    """Core class for handling data comparison operations.

    This class provides a high-level interface for comparing two data files.
    It handles file loading, comparison configuration, and results analysis.
    The class supports different file formats through the file handler system.

    Attributes:
        df1 (Optional[pd.DataFrame]): The first (base) DataFrame for comparison
        df2 (Optional[pd.DataFrame]): The second (compare) DataFrame for comparison
        comparison (Optional[datacompy.Compare]): The DataCompy comparison object
        file1_options (Dict): Options used when loading the first file
        file2_options (Dict): Options used when loading the second file
    """

    def __init__(self):
        """Initialize a new comparison instance."""
        self.df1 = None
        self.df2 = None
        self.comparison = None
        self.file1_options = {}
        self.file2_options = {}

    def get_file_options(self, file) -> Dict:
        """Get options needed for reading a specific file type.

        Some file types (like Excel) require additional options (like sheet selection).
        This method determines what options are available for a given file.

        Args:
            file: A file-like object to get options for.

        Returns:
            Dict: A dictionary of options specific to the file type.
                For example, Excel files return {'sheet_name': ['Sheet1', 'Sheet2']}.
        """
        try:
            handler = get_handler(file)
            if handler:
                return handler.get_options(file)
            logger.warning(f"No handler found for file: {file.name}")
            return {}
        except Exception as e:
            logger.error(f"Error getting file options: {str(e)}")
            return {}

    def load_data(self, files: Dict, options: Dict) -> Tuple[bool, str]:
        """Load data from uploaded files.

        Loads two files for comparison using appropriate handlers based on file type.
        Supports different file formats through the file handler system.

        Args:
            files: Dictionary containing two files:
                {'file1': first_file, 'file2': second_file}
            options: Dictionary containing options for each file:
                {'file1': {...}, 'file2': {...}}

        Returns:
            Tuple[bool, str]: A tuple containing:
                - Success flag (True if both files loaded successfully)
                - Error message (empty string if successful, error details if failed)
        """
        try:
            # Get handlers for both files
            handler1 = get_handler(files["file1"])
            handler2 = get_handler(files["file2"])

            if not handler1:
                msg = f"Unsupported file type: {files['file1'].name}"
                logger.error(msg)
                return False, msg
            if not handler2:
                msg = f"Unsupported file type: {files['file2'].name}"
                logger.error(msg)
                return False, msg

            try:
                # Load the data
                logger.info(f"Loading file1: {files['file1'].name}")
                self.df1 = handler1.read_data(
                    files["file1"], **options.get("file1", {})
                )
                logger.debug(
                    f"File1 loaded, shape: {self.df1.shape if self.df1 is not None else 'None'}"
                )

                logger.info(f"Loading file2: {files['file2'].name}")
                self.df2 = handler2.read_data(
                    files["file2"], **options.get("file2", {})
                )
                logger.debug(
                    f"File2 loaded, shape: {self.df2.shape if self.df2 is not None else 'None'}"
                )

                if self.df1 is None or self.df2 is None:
                    msg = "Failed to load one or both files"
                    logger.error(msg)
                    return False, msg

                return True, ""

            except Exception as e:
                msg = f"Error reading files: {str(e)}"
                logger.error(msg)
                return False, msg

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return False, str(e)

    def get_column_info(self, df: pd.DataFrame) -> pd.DataFrame:
        """Get detailed column information for a DataFrame.

        Analyzes a DataFrame to provide detailed information about each column,
        including data types, null counts, and sample values.

        Args:
            df: The DataFrame to analyze.

        Returns:
            pd.DataFrame: A DataFrame containing column analysis with these columns:
                - Column Name: Name of the column
                - Type: Data type of the column
                - Non-Null %: Percentage of non-null values
                - Non-Null Count: Count of non-null values
                - Null Count: Count of null values
                - Sample Values: Example values from the column
        """
        try:
            columns_df = pd.DataFrame(
                {
                    "Column Name": df.columns,
                    "Type": df.dtypes.astype(str),
                    "Non-Null Count": df.count(),
                    "Null Count": df.isna().sum(),
                    "Sample Values": [
                        (
                            str(df[col].dropna().head(2).tolist())[:50] + "..."
                            if not df[col].empty
                            else "No samples"
                        )
                        for col in df.columns
                    ],
                }
            )

            total_rows = len(df)
            columns_df["Non-Null %"] = (
                columns_df["Non-Null Count"] / total_rows * 100
            ).round(1).astype(str) + "%"
            columns_df = columns_df[
                [
                    "Column Name",
                    "Type",
                    "Non-Null %",
                    "Non-Null Count",
                    "Null Count",
                    "Sample Values",
                ]
            ]

            return columns_df
        except Exception as e:
            logger.error(f"Error getting column info: {str(e)}")
            return pd.DataFrame()

    def get_join_column_stats(self) -> List[Dict]:
        """Get statistics for potential join columns.

        Analyzes columns present in both DataFrames to help users select
        appropriate join keys. Provides statistics about uniqueness and null
        values, and recommends columns suitable for joining.

        Returns:
            List[Dict]: List of dictionaries containing column statistics:
                - Column: Column name
                - Type: Data type
                - Unique Values: Count and percentage for both files
                - Nulls: Null count for both files
                - Recommended: Indicator if column is recommended for joining
                  (high uniqueness, no nulls)
        """
        try:
            if not (self.df1 is not None and self.df2 is not None):
                logger.warning(
                    "Cannot get join column stats: one or both DataFrames are None"
                )
                return []

            # Get common columns in a deterministic order
            common_columns = sorted(set(self.df1.columns) & set(self.df2.columns))
            join_stats = []

            for col in common_columns:
                unique_vals_base = self.df1[col].nunique()
                unique_vals_compare = self.df2[col].nunique()
                null_count_base = self.df1[col].isna().sum()
                null_count_compare = self.df2[col].isna().sum()

                uniqueness_base = (
                    (unique_vals_base / len(self.df1) * 100) if len(self.df1) > 0 else 0
                )
                uniqueness_compare = (
                    (unique_vals_compare / len(self.df2) * 100)
                    if len(self.df2) > 0
                    else 0
                )

                # Calculate an overall uniqueness score for sorting
                uniqueness_score = min(uniqueness_base, uniqueness_compare)

                is_good_key = (
                    uniqueness_base > 90
                    and uniqueness_compare > 90
                    and null_count_base == 0
                    and null_count_compare == 0
                )

                join_stats.append(
                    {
                        "Column": col,
                        "Type": str(self.df1[col].dtype),
                        "Unique Values (Base)": f"{unique_vals_base:,} ({uniqueness_base:.1f}%)",
                        "Unique Values (Compare)": f"{unique_vals_compare:,} ({uniqueness_compare:.1f}%)",
                        "Nulls (Base)": null_count_base,
                        "Nulls (Compare)": null_count_compare,
                        "Recommended": "✅ Recommended" if is_good_key else "",
                        "uniqueness_score": uniqueness_score,  # Added for sorting
                    }
                )

            # Sort by uniqueness score (descending) and then column name
            join_stats.sort(key=lambda x: (-x["uniqueness_score"], x["Column"]))

            # Remove the sorting score before returning
            for stat in join_stats:
                del stat["uniqueness_score"]

            return join_stats
        except Exception as e:
            logger.error(f"Error getting join column stats: {str(e)}")
            return []

    def compare_data(self, join_columns: List[str]) -> Optional[datacompy.Compare]:
        """Perform the comparison using specified join columns.

        Creates a DataCompy comparison object using the specified columns as join keys.
        The comparison analyzes differences between the two DataFrames.

        Args:
            join_columns: List of column names to use as join keys.

        Returns:
            Optional[datacompy.Compare]: The comparison object if successful,
                None if comparison could not be performed.
        """
        try:
            if not (self.df1 is not None and self.df2 is not None):
                logger.warning("Cannot compare data: one or both DataFrames are None")
                return None

            logger.info(f"Comparing data using join columns: {join_columns}")
            self.comparison = datacompy.Compare(
                self.df1,
                self.df2,
                join_columns=join_columns,
                df1_name="Base File",
                df2_name="Compare File",
            )
            return self.comparison
        except Exception as e:
            logger.error(f"Error comparing data: {str(e)}")
            return None

    def get_comparison_stats(self) -> Dict:
        """Get comprehensive comparison statistics.

        Calculates detailed statistics about the comparison results, including
        matching rows, unmatched rows, and match rates.

        Returns:
            Dict: Dictionary containing comparison statistics:
                - rows_in_common: Number of matching rows
                - unmatched_base: Number of rows only in base file
                - unmatched_compare: Number of rows only in compare file
                - match_rate: Percentage of matching rows
                - total_base: Total rows in base file
                - total_compare: Total rows in compare file
                - merged_data: DataFrame containing all rows with match indicators
        """
        try:
            if not self.comparison:
                logger.warning(
                    "Cannot get comparison stats: no comparison has been performed"
                )
                return {}

            df_merged = pd.merge(
                self.df1,
                self.df2,
                on=self.comparison.join_columns,
                how="outer",
                indicator=True,
                suffixes=("_base", "_compare"),
            )

            rows_in_common = len(df_merged[df_merged["_merge"] == "both"])
            unmatched_base = len(df_merged[df_merged["_merge"] == "left_only"])
            unmatched_compare = len(df_merged[df_merged["_merge"] == "right_only"])
            match_rate = (
                (rows_in_common / len(self.df1) * 100) if len(self.df1) > 0 else 0
            )

            logger.info(
                f"Comparison stats: {rows_in_common} rows in common, {unmatched_base} only in base, {unmatched_compare} only in compare"
            )
            return {
                "rows_in_common": rows_in_common,
                "unmatched_base": unmatched_base,
                "unmatched_compare": unmatched_compare,
                "match_rate": match_rate,
                "total_base": len(self.df1),
                "total_compare": len(self.df2),
                "merged_data": df_merged,
            }
        except Exception as e:
            logger.error(f"Error getting comparison stats: {str(e)}")
            return {}

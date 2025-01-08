"""Core functionality for Datacompy Web UI."""

from typing import Tuple, Optional, Dict, List
import datacompy
import pandas as pd
import logging
from .file_handlers import get_handler

logger = logging.getLogger(__name__)


class DataComparisonCore:
    """Core class for handling data comparison operations."""

    def __init__(self):
        """Initialize the comparison object."""
        self.df1 = None
        self.df2 = None
        self.comparison = None
        self.file1_options = {}
        self.file2_options = {}

    def get_file_options(self, file) -> Dict:
        """Get options needed for reading this file type."""
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
        """Load data from uploaded files."""
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
        """Get detailed column information for a DataFrame."""
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
        """Get statistics for potential join columns."""
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
        """Perform the comparison using specified join columns."""
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
        """Get comprehensive comparison statistics."""
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

"""Core comparison logic for DataCompy Web UI."""
import warnings
import pandas as pd
from typing import Optional, List, Dict, Tuple

# Suppress optional dependency warnings from datacompy
warnings.filterwarnings('ignore', message='.*optional dependency.*')
warnings.filterwarnings('ignore', message='.*currently is not supported.*')

import datacompy

class DataComparisonCore:
    """Core class for handling data comparison operations."""
    
    def __init__(self):
        self.df1: Optional[pd.DataFrame] = None
        self.df2: Optional[pd.DataFrame] = None
        self.comparison: Optional[datacompy.Compare] = None
        self.sheet_names1 = []
        self.sheet_names2 = []

    def _get_file_type(self, file) -> str:
        """Determine file type from extension."""
        name = file.name.lower()
        if name.endswith('.csv'):
            return 'csv'
        elif name.endswith(('.xlsx', '.xls')):
            return 'excel'
        else:
            raise ValueError("Unsupported file type. Please upload CSV or Excel files.")

    def get_sheet_names(self, file) -> List[str]:
        """Get sheet names from Excel file."""
        if self._get_file_type(file) == 'excel':
            return pd.ExcelFile(file).sheet_names
        return []

    def load_data(self, file1, file2, sheet1: Optional[str] = None, sheet2: Optional[str] = None) -> Tuple[bool, str]:
        """Load data from uploaded files."""
        try:
            # Determine file types
            type1 = self._get_file_type(file1)
            type2 = self._get_file_type(file2)

            # Load first file
            if type1 == 'csv':
                self.df1 = pd.read_csv(file1)
            else:  # Excel
                if not sheet1:
                    self.sheet_names1 = self.get_sheet_names(file1)
                    return False, "Please select a sheet from the first Excel file"
                self.df1 = pd.read_excel(file1, sheet_name=sheet1)

            # Load second file
            if type2 == 'csv':
                self.df2 = pd.read_csv(file2)
            else:  # Excel
                if not sheet2:
                    self.sheet_names2 = self.get_sheet_names(file2)
                    return False, "Please select a sheet from the second Excel file"
                self.df2 = pd.read_excel(file2, sheet_name=sheet2)

            return True, ""

        except Exception as e:
            return False, str(e)

    def get_column_info(self, df: pd.DataFrame) -> pd.DataFrame:
        """Get detailed column information for a DataFrame."""
        columns_df = pd.DataFrame({
            'Column Name': df.columns,
            'Type': df.dtypes.astype(str),
            'Non-Null Count': df.count(),
            'Null Count': df.isna().sum(),
            'Sample Values': [str(df[col].dropna().head(2).tolist())[:50] + '...' 
                            if not df[col].empty else 'No samples' 
                            for col in df.columns]
        })
        
        total_rows = len(df)
        columns_df['Non-Null %'] = (columns_df['Non-Null Count'] / total_rows * 100).round(1).astype(str) + '%'
        columns_df = columns_df[['Column Name', 'Type', 'Non-Null %', 'Non-Null Count', 'Null Count', 'Sample Values']]
        
        return columns_df

    def get_join_column_stats(self) -> List[Dict]:
        """Get statistics for potential join columns."""
        if not (self.df1 is not None and self.df2 is not None):
            return []

        # Get common columns in a deterministic order
        common_columns = sorted(set(self.df1.columns) & set(self.df2.columns))
        join_stats = []
        
        for col in common_columns:
            unique_vals_base = self.df1[col].nunique()
            unique_vals_compare = self.df2[col].nunique()
            null_count_base = self.df1[col].isna().sum()
            null_count_compare = self.df2[col].isna().sum()
            
            uniqueness_base = (unique_vals_base / len(self.df1) * 100) if len(self.df1) > 0 else 0
            uniqueness_compare = (unique_vals_compare / len(self.df2) * 100) if len(self.df2) > 0 else 0
            
            # Calculate an overall uniqueness score for sorting
            uniqueness_score = min(uniqueness_base, uniqueness_compare)
            
            is_good_key = (
                uniqueness_base > 90 and
                uniqueness_compare > 90 and
                null_count_base == 0 and
                null_count_compare == 0
            )
            
            join_stats.append({
                'Column': col,
                'Type': str(self.df1[col].dtype),
                'Unique Values (Base)': f"{unique_vals_base:,} ({uniqueness_base:.1f}%)",
                'Unique Values (Compare)': f"{unique_vals_compare:,} ({uniqueness_compare:.1f}%)",
                'Nulls (Base)': null_count_base,
                'Nulls (Compare)': null_count_compare,
                'Recommended': '✅ Recommended' if is_good_key else '',
                'uniqueness_score': uniqueness_score  # Added for sorting
            })
        
        # Sort by uniqueness score (descending) and then column name
        join_stats.sort(key=lambda x: (-x['uniqueness_score'], x['Column']))
        
        # Remove the sorting score before returning
        for stat in join_stats:
            del stat['uniqueness_score']
            
        return join_stats

    def compare_data(self, join_columns: List[str]) -> Optional[datacompy.Compare]:
        """Perform the comparison using specified join columns."""
        if not (self.df1 is not None and self.df2 is not None):
            return None

        self.comparison = datacompy.Compare(
            self.df1,
            self.df2,
            join_columns=join_columns,
            df1_name='Base File',
            df2_name='Compare File'
        )
        return self.comparison

    def get_comparison_stats(self) -> Dict:
        """Get comprehensive comparison statistics."""
        if not self.comparison:
            return {}

        df_merged = pd.merge(
            self.df1, 
            self.df2, 
            on=self.comparison.join_columns, 
            how='outer', 
            indicator=True,
            suffixes=('_base', '_compare')
        )

        rows_in_common = len(df_merged[df_merged['_merge'] == 'both'])
        unmatched_base = len(df_merged[df_merged['_merge'] == 'left_only'])
        unmatched_compare = len(df_merged[df_merged['_merge'] == 'right_only'])
        match_rate = (rows_in_common / len(self.df1) * 100) if len(self.df1) > 0 else 0

        return {
            'rows_in_common': rows_in_common,
            'unmatched_base': unmatched_base,
            'unmatched_compare': unmatched_compare,
            'match_rate': match_rate,
            'total_base': len(self.df1),
            'total_compare': len(self.df2),
            'merged_data': df_merged
        } 
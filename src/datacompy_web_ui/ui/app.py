"""Streamlit UI for DataCompy Web UI."""

import warnings
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from pathlib import Path

# Suppress optional dependency warnings
warnings.filterwarnings("ignore", message=".*optional dependency.*")
warnings.filterwarnings("ignore", message=".*currently is not supported.*")
warnings.filterwarnings(
    "ignore", message=".*For better performance, install the Watchdog.*"
)

from datacompy_web_ui.core.comparison import DataComparisonCore


def setup_page() -> None:
    """Configure the Streamlit page settings and styling."""
    st.set_page_config(
        page_title="DataCompy Web UI",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    css_path = Path(__file__).parent / "styles" / "styles.css"
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def render_header():
    """Render the app header and description."""
    st.title("📊 Datacompy Web UI")
    st.markdown(
        """
    Compare CSV and Excel files and analyze their differences using DataCompy.
    Upload your files below and select the columns to use as join keys.
    """
    )


def calculate_height(df, min_height=200, max_height=600, row_height=35):
    """Calculate a reasonable height for a dataframe display."""
    return min(max(min_height, (len(df) + 1) * row_height), max_height)


def run_app():
    """Run the Streamlit application."""
    setup_page()
    render_header()

    comparison = DataComparisonCore()

    # File upload section
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📄 Base File (File 1)")
        file1 = st.file_uploader(
            "Choose your base file", type=["csv", "xlsx", "xls"], key="file1"
        )
        file1_options = {}
        if file1:
            options = comparison.get_file_options(file1)
            if "sheet_name" in options:
                file1_options["sheet_name"] = st.selectbox(
                    "Select sheet from Base File", options["sheet_name"], key="sheet1"
                )

    with col2:
        st.subheader("📄 Compare File (File 2)")
        file2 = st.file_uploader(
            "Choose your comparison file", type=["csv", "xlsx", "xls"], key="file2"
        )
        file2_options = {}
        if file2:
            options = comparison.get_file_options(file2)
            if "sheet_name" in options:
                file2_options["sheet_name"] = st.selectbox(
                    "Select sheet from Compare File",
                    options["sheet_name"],
                    key="sheet2",
                )

    if file1 and file2:
        success, error = comparison.load_data(
            files={"file1": file1, "file2": file2},
            options={"file1": file1_options, "file2": file2_options},
        )
        if not success:
            st.error(f"Error loading files: {error}")
            return

        # Display file summaries
        col1, col2 = st.columns(2)
        with col1:
            st.info(
                f"""
            **Base File Summary:**
            - Total Rows: {comparison.df1.shape[0]:,}
            - Total Columns: {comparison.df1.shape[1]}
            """
            )
            with st.expander("📋 Column Details", expanded=True):
                column_info = comparison.get_column_info(comparison.df1)
                st.dataframe(
                    column_info,
                    use_container_width=True,
                    height=calculate_height(column_info),
                )

        with col2:
            st.info(
                f"""
            **Compare File Summary:**
            - Total Rows: {comparison.df2.shape[0]:,}
            - Total Columns: {comparison.df2.shape[1]}
            """
            )
            with st.expander("📋 Column Details", expanded=True):
                column_info = comparison.get_column_info(comparison.df2)
                st.dataframe(
                    column_info,
                    use_container_width=True,
                    height=calculate_height(column_info),
                )

        # Join column selection
        st.subheader("🔑 Select Join Key Columns")
        join_stats = comparison.get_join_column_stats()

        if join_stats:
            with st.expander("📊 Column Statistics", expanded=True):
                st.markdown(
                    """
                **Selection Guide:**
                - ✅ marks recommended join keys (high uniqueness, no nulls)
                - Best join keys typically have high uniqueness percentages
                - Avoid columns with null values for joins
                - Consider business context when selecting multiple columns
                """
                )
                st.dataframe(pd.DataFrame(join_stats), use_container_width=True)

            # Get recommended columns
            recommended_columns = [
                stat["Column"]
                for stat in join_stats
                if stat["Recommended"] == "✅ Recommended"
            ]

            common_columns = list(
                set(comparison.df1.columns) & set(comparison.df2.columns)
            )

            # Sort columns to show recommended ones first
            sorted_columns = recommended_columns + [
                col for col in sorted(common_columns) if col not in recommended_columns
            ]

            selected_columns = st.multiselect(
                "Select one or more columns to use as join keys:",
                options=sorted_columns,
                default=recommended_columns[:1] if recommended_columns else None,
                help="Choose columns that uniquely identify rows (e.g., ID fields, composite keys)",
            )

            if selected_columns:
                if st.button("🔍 Compare Files"):
                    with st.spinner("Comparing files..."):
                        comparison.compare_data(selected_columns)
                        display_comparison_results(comparison)


def display_comparison_results(comparison: DataComparisonCore):
    """Display the comparison results."""
    if not comparison or not comparison.comparison:
        st.error("No comparison has been performed yet.")
        return

    # Get the comparison object
    dc = comparison.comparison

    # Display high-level metrics
    st.header("📊 Comparison Overview")
    col1, col2, col3 = st.columns(3)

    match_rate = (
        (dc.count_matching_rows() / len(dc.df1) * 100) if len(dc.df1) > 0 else 0
    )
    with col1:
        st.metric(
            "Match Rate",
            f"{match_rate:.1f}%",
            help="Percentage of rows that match between files",
        )
    with col2:
        st.metric(
            "Matching Rows",
            f"{dc.count_matching_rows():,}",
            help="Number of rows that match exactly",
        )
    with col3:
        st.metric(
            "Matching Columns",
            f"{len(dc.intersect_columns()):,}",
            help="Number of columns present in both files",
        )

    # Display column analysis
    st.subheader("📋 Column Analysis")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### 🔍 Column Matches")
        st.info(
            f"""
        - Common Columns: {len(dc.intersect_columns()):,}
        - Only in Base: {len(dc.df1_unq_columns()):,}
        - Only in Compare: {len(dc.df2_unq_columns()):,}
        
        **Join Keys:** {', '.join(f'`{col}`' for col in dc.join_columns)}
        """
        )

    with col2:
        st.markdown("##### 📊 Row Matches")
        st.info(
            f"""
        - Matching Rows: {dc.count_matching_rows():,}
        - Only in Base: {len(dc.df1) - dc.count_matching_rows():,}
        - Only in Compare: {len(dc.df2) - dc.count_matching_rows():,}
        """
        )

    # Display row-level differences
    st.subheader("🔍 Detailed Analysis")

    # Sample mismatches if any exist
    if not dc.all_columns_match():
        with st.expander("❌ Sample Mismatches", expanded=True):
            st.markdown("##### Sample of Mismatched Rows")
            sample_df = dc.sample_mismatch()
            if not sample_df.empty:
                st.dataframe(
                    sample_df,
                    use_container_width=True,
                    height=calculate_height(sample_df),
                )
            else:
                st.success("No mismatches found in the sample")

    # Display unique rows
    with st.expander("👥 Unique Rows", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### Rows Only in Base")
            if not dc.df1_unq_rows.empty:
                st.dataframe(
                    dc.df1_unq_rows,
                    use_container_width=True,
                    height=calculate_height(dc.df1_unq_rows),
                )
            else:
                st.success("No unique rows in Base file")

        with col2:
            st.markdown("##### Rows Only in Compare")
            if not dc.df2_unq_rows.empty:
                st.dataframe(
                    dc.df2_unq_rows,
                    use_container_width=True,
                    height=calculate_height(dc.df2_unq_rows),
                )
            else:
                st.success("No unique rows in Compare file")

    # Column value distributions
    with st.expander("📊 Column Statistics", expanded=True):
        st.markdown("##### Column-by-Column Comparison")
        for col in dc.intersect_columns():
            if col not in dc.join_columns:
                st.markdown(f"**{col}**")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("Base File:")
                    value_counts_df = dc.df1[col].value_counts().head().reset_index()
                    value_counts_df.columns = ["Value", "Count"]
                    st.dataframe(
                        value_counts_df,
                        use_container_width=True,
                        hide_index=True,
                        height=calculate_height(
                            value_counts_df, min_height=150, max_height=300
                        ),
                    )
                with col2:
                    st.markdown("Compare File:")
                    value_counts_df = dc.df2[col].value_counts().head().reset_index()
                    value_counts_df.columns = ["Value", "Count"]
                    st.dataframe(
                        value_counts_df,
                        use_container_width=True,
                        hide_index=True,
                        height=calculate_height(
                            value_counts_df, min_height=150, max_height=300
                        ),
                    )
                st.markdown("---")

    # Display the raw report
    with st.expander("📝 View Raw Report", expanded=False):
        st.text(dc.report())


if __name__ == "__main__":
    run_app()

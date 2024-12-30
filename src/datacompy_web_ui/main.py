"""Main entry point for the DataCompy Web UI application."""
import os
import sys
from streamlit.web import cli as st_cli

def main():
    """Run the DataCompy Web UI application."""
    # Get the path to our app module
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(current_dir, "ui", "app.py")
    
    # Run Streamlit using its CLI
    sys.argv = ["streamlit", "run", app_path]
    sys.exit(st_cli.main())

if __name__ == "__main__":
    main() 
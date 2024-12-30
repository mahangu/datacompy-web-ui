from setuptools import setup, find_packages

setup(
    name="datacompy-web-ui",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={
        "datacompy_web_ui": ["ui/*.py", "ui/styles/*.css", "core/*.py"],
    },
    install_requires=[
        "streamlit>=1.41.0",
        "datacompy>=0.9.1",
        "pandas>=2.1.1",
        "plotly>=5.20.0",
        "matplotlib>=3.8.1",
    ],
    entry_points={
        "console_scripts": [
            "datacompy_web_ui=datacompy_web_ui.main:main",
        ],
    },
    python_requires=">=3.11",
    author="Mahangu Weerasinghe",
    author_email="mahangu@gmail.com",
    description="A web-based UI for DataCompy CSV comparison",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/mahangu/datacompy-web-ui",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Programming Language :: Python :: 3.11",
    ],
) 
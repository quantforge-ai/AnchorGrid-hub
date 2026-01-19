from setuptools import setup, find_packages

setup(
    name="quantgrid",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.25.0",
        "beautifulsoup4>=4.12.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "yfinance>=0.2.0",
        "sqlalchemy>=2.0.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
    ],
)

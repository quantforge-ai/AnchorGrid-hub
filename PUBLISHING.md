# AnchorGrid PyPI Publishing Guide

## Prerequisites

```bash
pip install build twine
```

## Build the Package

```bash
cd D:\AnchorGrid-core
python -m build
```

This creates:
- `dist/anchorgrid-1.0.0.tar.gz` (source)
- `dist/anchorgrid-1.0.0-py3-none-any.whl` (wheel)

## Test Upload to TestPyPI (Recommended First)

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Install from TestPyPI to test
pip install --index-url https://test.pypi.org/simple/ anchorgrid
```

## Publish to PyPI

```bash
# Upload to real PyPI
twine upload dist/*
```

You'll be prompted for:
- Username: `__token__`
- Password: `pypi-...` (your PyPI API token)

## Post-Publication

Install from PyPI:
```bash
pip install anchorgrid
```

Or with ML support:
```bash
pip install anchorgrid[ml]
```

## Version Updates

When releasing a new version:

1. Update version in `pyproject.toml`
2. Update version in `anchorgrid/__init__.py` 
3. Create git tag: `git tag v1.0.0`
4. Rebuild and republish

## Notes

- Package size is ~100MB due to all dependencies
- Consider splitting into `anchorgrid-core`, `anchorgrid-ml` if size is an issue
- ML dependencies are heavy (torch, transformers) - users can skip with base install

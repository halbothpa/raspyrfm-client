# Release Process Guide

This document explains how to create releases for the RaspyRFM integration for Home Assistant OS.

## Overview

The project now includes an automated release workflow that builds optimized packages for Home Assistant OS running on Raspberry Pi 4 and 5. The workflow is triggered automatically when you push a version tag or can be manually triggered.

## Creating a New Release

### Method 1: Automatic (Recommended)

1. **Update the version number** in `pyproject.toml`:
   ```toml
   [tool.poetry]
   version = "1.3.0"  # Update this
   ```

2. **Update the version** in `custom_components/raspyrfm/manifest.json`:
   ```json
   {
     "version": "0.2.0"
   }
   ```

3. **Commit and push** your changes:
   ```bash
   git add pyproject.toml custom_components/raspyrfm/manifest.json
   git commit -m "Bump version to 1.3.0"
   git push origin master
   ```

4. **Create and push a version tag**:
   ```bash
   git tag -a v1.3.0 -m "Release version 1.3.0"
   git push origin v1.3.0
   ```

5. **Wait for the workflow to complete** (usually 3-5 minutes)

6. **Check the release** at https://github.com/halbothpa/raspyrfm-client/releases

### Method 2: Manual Trigger

You can also manually trigger a release from the GitHub Actions interface:

1. Go to https://github.com/halbothpa/raspyrfm-client/actions
2. Select **Build HAOS Release** workflow
3. Click **Run workflow**
4. Enter the version number (e.g., `1.3.0`)
5. Click **Run workflow**

## Release Artifacts

Each release automatically generates the following files:

### 1. `raspyrfm-X.X.X.zip` (Recommended for HAOS users)
- Contains only the Home Assistant custom component
- Ready to extract directly to `/config/custom_components/`
- Size: ~50KB
- **This is what most users should download**

### 2. `raspyrfm-full-X.X.X.tar.gz`
- Includes the custom component
- Includes the Python library (.whl and .tar.gz)
- Includes installation script
- Includes documentation (README, MANUAL, LICENSE)
- Size: ~100KB
- For users who want everything in one package

### 3. `raspyrfm_client-X.X.X-py3-none-any.whl`
- Python wheel package
- For installing via pip: `pip install raspyrfm_client-X.X.X-py3-none-any.whl`
- For Python developers integrating the library

### 4. `raspyrfm_client-X.X.X.tar.gz`
- Python source distribution
- For building from source
- For package maintainers

## Release Notes

The workflow automatically generates comprehensive release notes including:

- What's new in this version
- Installation instructions for HAOS
- Configuration steps
- Hardware requirements
- Documentation links
- Troubleshooting tips

## Publishing to PyPI

The workflow automatically publishes to PyPI when you push a tag (not on manual triggers). Requirements:

1. Set up `PYPI_TOKEN` secret in repository settings
2. Push a version tag (not manual trigger)
3. The workflow will attempt to publish
4. If the version already exists, it will continue (non-fatal error)

To set up PyPI token:

1. Generate a token at https://pypi.org/manage/account/token/
2. Go to repository Settings → Secrets and variables → Actions
3. Create new secret named `PYPI_TOKEN`
4. Paste your PyPI token

## Version Numbering

Follow semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes (e.g., 2.0.0)
- **MINOR**: New features, backward compatible (e.g., 1.3.0)
- **PATCH**: Bug fixes, backward compatible (e.g., 1.2.1)

### Component vs Library Versions

- **Python library** (pyproject.toml): Use full semantic versioning (e.g., 1.3.0)
- **HA Component** (manifest.json): Can use simplified versioning (e.g., 0.2.0)
- They don't have to match, but major releases should align

## Testing Before Release

Before creating a release:

1. **Run tests**:
   ```bash
   poetry install --with test
   poetry run pytest
   ```

2. **Build locally**:
   ```bash
   poetry build
   ```

3. **Verify integration**:
   ```bash
   python -c "import json; print(json.load(open('custom_components/raspyrfm/manifest.json')))"
   ```

4. **Build documentation**:
   ```bash
   cd docs
   make html
   ```

## Release Checklist

Before creating a release, ensure:

- [ ] All tests pass
- [ ] Version numbers updated in both `pyproject.toml` and `manifest.json`
- [ ] CHANGELOG.md updated (if you maintain one)
- [ ] Documentation is up to date
- [ ] Breaking changes are documented
- [ ] README.rst reflects current features
- [ ] Integration tested with latest HAOS

## Troubleshooting

### Workflow fails on "Run tests"
- Check that all dependencies are in poetry.lock
- Ensure tests pass locally first
- Review test output in Actions log

### Workflow fails on "Create GitHub Release"
- Ensure you have write permissions
- Check that the tag doesn't already exist
- Verify GITHUB_TOKEN has correct permissions

### PyPI publish fails
- Check PYPI_TOKEN is set correctly
- Verify version doesn't already exist on PyPI
- Review PyPI API errors in workflow log

### Release artifacts are missing
- Ensure the workflow completed successfully
- Check the "Create HAOS addon archive" step
- Verify zip commands executed without errors

## Updating the Workflow

If you need to modify the release workflow:

1. Edit `.github/workflows/haos-release.yml`
2. Test changes on a feature branch first
3. Use workflow_dispatch trigger to test manually
4. Merge to master only after successful tests

## Getting Help

- Workflow issues: Check Actions tab for detailed logs
- Release questions: Open an issue with the "release" label
- Documentation: See HAOS_INSTALLATION.md for user-facing docs

## Example Release

Here's a complete example of creating version 1.3.0:

```bash
# 1. Update versions
vim pyproject.toml  # Set version = "1.3.0"
vim custom_components/raspyrfm/manifest.json  # Set version = "0.2.0"

# 2. Test everything
poetry run pytest
poetry build
cd docs && make html && cd ..

# 3. Commit changes
git add pyproject.toml custom_components/raspyrfm/manifest.json
git commit -m "Release version 1.3.0

- Add HAOS release workflow
- Improve UI/UX for mobile
- Update documentation for Raspberry Pi 4/5
"

# 4. Push to master
git push origin master

# 5. Create and push tag
git tag -a v1.3.0 -m "Version 1.3.0

Features:
- Automatic HAOS release workflow
- Enhanced UI/UX
- Improved documentation

See release notes for full details."

git push origin v1.3.0

# 6. Wait and verify
# Check https://github.com/halbothpa/raspyrfm-client/actions
# Verify release at https://github.com/halbothpa/raspyrfm-client/releases
```

That's it! The workflow handles everything else automatically.

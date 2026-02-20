# GitHub Setup and Deployment Guide

Complete guide to push DataQE Framework to GitHub as a public repository.

## Prerequisites

1. Git installed on your system
2. GitHub account (create at https://github.com if you don't have one)
3. SSH key configured (recommended) or Personal Access Token (alternative)

## Step-by-Step Guide

### Step 1: Configure Git Locally

Configure git with your information:

```bash
git config --global user.name "Khadar Shaik"
git config --global user.email "khadarmohiddin.shaik@apree.health"
```

Verify configuration:
```bash
git config --global --list
```

### Step 2: Initialize Local Repository

Navigate to the dataqe-framework directory:

```bash
cd /Users/khadarmohiddin.shaik/Projects/Ventana/dataqe-framework
```

Initialize git repository:

```bash
git init
```

### Step 3: Add and Commit All Files

Add all files to staging:

```bash
git add .
```

Review what will be committed:

```bash
git status
```

Create initial commit:

```bash
git commit -m "Initial commit: DataQE Framework v0.0.1

- Multi-database support (MySQL, BigQuery)
- YAML-based test configuration
- Flexible comparison modes
- Dynamic dataset replacement
- Comprehensive reporting
- PHI data protection
- CI/CD integration support
- Complete documentation
- Example configurations

Author: Khadar Shaik <khadarmohiddin.shaik@apree.health>"
```

### Step 4: Create GitHub Repository

1. Go to https://github.com/new
2. Enter repository name: `dataqe-framework`
3. Description: `Data Quality and Equality Testing Framework for validating data consistency between databases`
4. Make it **PUBLIC**
5. DO NOT initialize with README (we already have one)
6. Click "Create repository"

### Step 5: Add Remote and Push

Copy the HTTPS URL from GitHub (it will be: `https://github.com/YOUR_USERNAME/dataqe-framework.git`)

Set the remote origin:

```bash
git remote add origin https://github.com/YOUR_USERNAME/dataqe-framework.git
```

Replace `YOUR_USERNAME` with your actual GitHub username.

Rename branch to main (if needed):

```bash
git branch -M main
```

Push to GitHub:

```bash
git push -u origin main
```

You'll be prompted to enter your GitHub credentials:
- Username: Your GitHub username
- Password: Your Personal Access Token (or use SSH key if configured)

### Step 6: Create Release Tag

Tag the initial release:

```bash
git tag -a v0.0.1 -m "DataQE Framework v0.0.1 - Initial Release

This is the first production release of DataQE Framework with:
- Complete documentation
- Multi-database support
- Dynamic dataset replacement
- Comprehensive reporting"
```

Push the tag to GitHub:

```bash
git push origin v0.0.1
```

## Complete Commands Summary

Here are all the commands in sequence (copy and paste one by one):

```bash
# Configure git
git config --global user.name "Khadar Shaik"
git config --global user.email "khadarmohiddin.shaik@apree.health"

# Navigate to project
cd /Users/khadarmohiddin.shaik/Projects/Ventana/dataqe-framework

# Initialize repository
git init

# Add all files
git add .

# Check status
git status

# Create initial commit
git commit -m "Initial commit: DataQE Framework v0.0.1

- Multi-database support (MySQL, BigQuery)
- YAML-based test configuration
- Flexible comparison modes
- Dynamic dataset replacement
- Comprehensive reporting
- PHI data protection
- CI/CD integration support
- Complete documentation
- Example configurations

Author: Khadar Shaik <khadarmohiddin.shaik@apree.health>"

# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/dataqe-framework.git

# Verify remote
git remote -v

# Rename to main branch
git branch -M main

# Push to GitHub
git push -u origin main

# Create and push tag
git tag -a v0.0.1 -m "DataQE Framework v0.0.1 - Initial Release"
git push origin v0.0.1

# View git log
git log --oneline
```

## Making Repository Installation-Ready

### Option 1: PyPI Package (Recommended for Public Distribution)

To make your package installable via `pip install dataqe-framework`, follow these steps:

#### 1. Create PyPI Account

- Go to https://pypi.org/account/register/
- Create account and verify email

#### 2. Create ~/.pypirc File

Create file `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
repository = https://upload.pypi.org/legacy/
username = YOUR_PYPI_USERNAME

[testpypi]
repository = https://test.pypi.org/legacy/
username = YOUR_PYPI_USERNAME
```

#### 3. Build and Upload Package

```bash
# Install build tools
pip install build twine

# Navigate to project
cd /Users/khadarmohiddin.shaik/Projects/Ventana/dataqe-framework

# Build package
python -m build

# Upload to PyPI
python -m twine upload dist/*
```

After this, anyone can install with:
```bash
pip install dataqe-framework
```

### Option 2: Direct GitHub Installation

Without PyPI, users can install directly from GitHub:

```bash
pip install git+https://github.com/ShaikKhadarmohiddin/dataqe-framework.git
```

### Option 3: From Source

Users can clone and install:

```bash
git clone https://github.com/ShaikKhadarmohiddin/dataqe-framework.git
cd dataqe-framework
pip install -e .
```

## Verifying Public Access

After pushing to GitHub, verify the repository is public:

1. Visit `https://github.com/YOUR_USERNAME/dataqe-framework`
2. Check if "Public" badge is visible
3. Try accessing without being logged in (incognito window)
4. Verify anyone can clone:
   ```bash
   git clone https://github.com/YOUR_USERNAME/dataqe-framework.git
   ```

## Setting Up GitHub Pages (Optional)

To host documentation:

1. Go to GitHub repository Settings → Pages
2. Select "Deploy from branch"
3. Select `main` branch and `/root` folder
4. Documentation will be available at: `https://YOUR_USERNAME.github.io/dataqe-framework/`

## Protecting Main Branch (Recommended)

1. Go to Settings → Branches
2. Add rule for `main`
3. Require pull request reviews before merging
4. Require status checks before merging

## GitHub Actions CI/CD (Optional)

Create `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11']

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .
        pip install pytest
    - name: Run tests
      run: pytest tests/
```

## Troubleshooting

### "Repository already exists"

If you get this error when creating the repository, it means the repository name already exists on your GitHub account.

**Solution**: Either choose a different name or delete the existing repository and recreate it.

### "Permission denied (publickey)"

If using SSH and get permission denied:

1. Verify SSH key is added to SSH agent:
```bash
ssh-add ~/.ssh/id_rsa
```

2. Test SSH connection:
```bash
ssh -T git@github.com
```

### "fatal: 'origin' does not appear to be a 'git' repository"

If you get this error, you haven't set the remote yet:

```bash
git remote add origin https://github.com/YOUR_USERNAME/dataqe-framework.git
```

### "src refspec main does not match any"

This means there are no commits yet:

```bash
# Create a commit first
git commit --allow-empty -m "Initial commit"

# Then push
git push -u origin main
```

## Next Steps

After pushing to GitHub:

1. ✓ Add Topics: Go to repository → About → Add topics
   - Suggested: `data-quality`, `testing`, `validation`, `database`, `mysql`, `bigquery`

2. ✓ Add Description: Update repository description

3. ✓ Add Shields (Optional): Add badges to README
   ```markdown
   ![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
   ![License](https://img.shields.io/badge/license-MIT-blue.svg)
   ![GitHub Workflow Status](https://img.shields.io/github/workflow/status/YOUR_USERNAME/dataqe-framework/Tests)
   ```

4. ✓ Enable Issues: Settings → Features → Issues (enabled by default)

5. ✓ Enable Discussions: Settings → Features → Discussions

6. ✓ Set up Wiki: Settings → Features → Wiki (optional)

## Sharing Your Repository

Once public, you can share:

- **GitHub URL**: `https://github.com/YOUR_USERNAME/dataqe-framework`
- **Installation Command**: `pip install git+https://github.com/YOUR_USERNAME/dataqe-framework.git`
- **Clone Command**: `git clone https://github.com/YOUR_USERNAME/dataqe-framework.git`

## Continuous Updates

For future updates:

```bash
# Make changes to code
# Test locally
# Commit and push
git add .
git commit -m "Your commit message"
git push origin main

# Create new release (for milestones)
git tag -a v0.0.2 -m "Description of v0.0.2"
git push origin v0.0.2
```

## Resources

- GitHub Documentation: https://docs.github.com
- PyPI Upload: https://packaging.python.org/tutorials/packaging-projects/
- Semantic Versioning: https://semver.org/
- MIT License: https://opensource.org/licenses/MIT

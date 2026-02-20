# GitHub Deployment Guide for DataQE Framework

Complete step-by-step guide to push DataQE Framework to https://github.com/ShaikKhadarmohiddin/ as a public repository.

## Your GitHub Information

- **GitHub Username**: ShaikKhadarmohiddin
- **Repository Name**: dataqe-framework
- **Final URL**: https://github.com/ShaikKhadarmohiddin/dataqe-framework
- **Author**: Khadar Shaik
- **Email**: khadarmohiddin.shaik@apree.health

## Step 1: Create Repository on GitHub

1. Go to: https://github.com/new
2. Enter details:
   - **Repository name**: `dataqe-framework`
   - **Description**: `Data Quality and Equality Testing Framework for validating data consistency between databases`
   - **Visibility**: Select **PUBLIC** (so anyone can see and install)
   - **Initialize this repository with**: Leave UNCHECKED (we have docs already)
3. Click **Create repository**

## Step 2: Configure Git Locally

Open terminal and run:

```bash
git config --global user.name "Khadar Shaik"
git config --global user.email "khadarmohiddin.shaik@apree.health"
```

Verify it worked:
```bash
git config --global --list
```

## Step 3: Initialize Local Repository

Navigate to project directory:

```bash
cd /Users/khadarmohiddin.shaik/Projects/Ventana/dataqe-framework
```

Initialize git:

```bash
git init
```

## Step 4: Stage and Commit All Files

Add all files:

```bash
git add .
```

Check what will be committed:

```bash
git status
```

Create the initial commit:

```bash
git commit -m "Initial commit: DataQE Framework v0.0.1

Add comprehensive data validation framework with:
- Multi-database support (MySQL, BigQuery)
- YAML-based test configuration
- Flexible comparison modes
- Dynamic dataset replacement
- Comprehensive reporting
- PHI data protection
- CI/CD integration support
- Complete documentation

Author: Khadar Shaik <khadarmohiddin.shaik@apree.health>"
```

## Step 5: Connect to GitHub Repository

Add the remote connection to your GitHub repository:

```bash
git remote add origin https://github.com/ShaikKhadarmohiddin/dataqe-framework.git
```

Verify the remote was added:

```bash
git remote -v
```

You should see:
```
origin  https://github.com/ShaikKhadarmohiddin/dataqe-framework.git (fetch)
origin  https://github.com/ShaikKhadarmohiddin/dataqe-framework.git (push)
```

## Step 6: Push to GitHub

Rename branch to main (standard practice):

```bash
git branch -M main
```

Push all code to GitHub:

```bash
git push -u origin main
```

**Note**: You'll be prompted for your GitHub credentials:
- If using HTTPS: GitHub username and Personal Access Token (see below)
- If using SSH: No prompt needed (if SSH key is configured)

### Getting Personal Access Token for HTTPS

If you use HTTPS and don't have a token:

1. Go to: https://github.com/settings/tokens
2. Click **Generate new token** → **Generate new token (classic)**
3. Give it a name: "DataQE Framework Push"
4. Select scopes: `repo` (full control of private repositories)
5. Click **Generate token**
6. **Copy the token** (you won't see it again)
7. When prompted during `git push`, use:
   - Username: `ShaikKhadarmohiddin`
   - Password: Paste the token

## Step 7: Create Release Tag

Create a version tag for the first release:

```bash
git tag -a v0.0.1 -m "DataQE Framework v0.0.1 - Initial Release

This is the first production release of DataQE Framework.

Features:
- Multi-database support (MySQL, BigQuery)
- YAML-based test configuration
- Flexible comparison modes
- Dynamic dataset replacement
- Comprehensive reporting
- PHI data protection
- CI/CD integration support

Documentation:
- Complete installation guide
- Configuration reference
- Feature guide with examples
- Architecture documentation
- Contributing guidelines"
```

Push the tag to GitHub:

```bash
git push origin v0.0.1
```

## Step 8: Verify Repository is Public

1. Visit: https://github.com/ShaikKhadarmohiddin/dataqe-framework
2. Look for "Public" badge under repository name
3. You should see all your files and documentation

## All Commands (Copy & Paste)

Run these commands in sequence:

```bash
# Configure Git
git config --global user.name "Khadar Shaik"
git config --global user.email "khadarmohiddin.shaik@apree.health"

# Navigate to project
cd /Users/khadarmohiddin.shaik/Projects/Ventana/dataqe-framework

# Initialize repository
git init

# Stage all files
git add .

# Check status
git status

# Create initial commit
git commit -m "Initial commit: DataQE Framework v0.0.1"

# Add GitHub remote
git remote add origin https://github.com/ShaikKhadarmohiddin/dataqe-framework.git

# Verify remote
git remote -v

# Rename to main branch
git branch -M main

# Push to GitHub
git push -u origin main

# Create version tag
git tag -a v0.0.1 -m "DataQE Framework v0.0.1 - Initial Release"

# Push tag
git push origin v0.0.1

# Verify
git log --oneline
```

## Installation Commands for Users

After your repository is public on GitHub, users can install DataQE Framework via:

### Option 1: Direct from GitHub (Recommended)

```bash
pip install git+https://github.com/ShaikKhadarmohiddin/dataqe-framework.git
```

### Option 2: Clone and Install

```bash
git clone https://github.com/ShaikKhadarmohiddin/dataqe-framework.git
cd dataqe-framework
pip install -e .
```

### Option 3: From PyPI (After publishing)

```bash
pip install dataqe-framework
```

## Update Repository Information (Optional but Recommended)

Go to: https://github.com/ShaikKhadarmohiddin/dataqe-framework/settings

### Add Topics

1. Scroll to "Topics" section
2. Add relevant tags:
   - `data-quality`
   - `testing`
   - `validation`
   - `database`
   - `mysql`
   - `bigquery`
   - `data-validation`

### Set Repository Description

Update the short description to show in searches and on GitHub homepage.

## What You're Sharing

Your public repository includes:

✓ **Source Code**
  - cli.py
  - executor.py
  - preprocessor.py
  - connectors/ (MySQL, BigQuery)
  - comparison/
  - reporter.py

✓ **Documentation**
  - README.md (main guide)
  - GETTING_STARTED.md (tutorials)
  - CONFIGURATION.md (reference)
  - PREPROCESSOR.md (feature guide)
  - ARCHITECTURE.md (technical)
  - CONTRIBUTING.md (how to contribute)

✓ **Examples**
  - example_preprocessor_config.yml
  - example_preprocessor_queries.yml
  - example_preprocessor_test_script.yml

✓ **Configuration**
  - pyproject.toml
  - LICENSE (MIT)
  - .gitignore

✗ **NOT Shared** (safely ignored)
  - Credentials/secrets
  - Virtual environment
  - Output directory
  - IDE settings (.idea, .vscode)
  - Temporary files

## Making It Installable via pip

To make `pip install dataqe-framework` work globally:

### 1. Create PyPI Account

- Go to: https://pypi.org/account/register/
- Register and verify email

### 2. Create PyPI Configuration

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

### 3. Build and Upload

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

After upload, anyone can:
```bash
pip install dataqe-framework
```

## Troubleshooting

### "Repository already exists on this server"
- Go to GitHub and create a new repository with the exact name

### "fatal: not a git repository"
- Run `git init` in the project directory

### "src refspec main does not match any"
- Make sure you created a commit first with `git commit`

### "Repository not found"
- Verify your GitHub username and repository name are correct
- Make sure repository exists on GitHub

### "Could not read Username" (HTTPS)
- You need a Personal Access Token (see Step 6 above)

### "Permission denied (publickey)" (SSH)
- Configure SSH key: https://docs.github.com/en/authentication/connecting-to-github-with-ssh

## Sharing Your Repository

Once pushed, share these links:

**GitHub Repository**:
```
https://github.com/ShaikKhadarmohiddin/dataqe-framework
```

**Installation Command**:
```bash
pip install git+https://github.com/ShaikKhadarmohiddin/dataqe-framework.git
```

**Clone Command**:
```bash
git clone https://github.com/ShaikKhadarmohiddin/dataqe-framework.git
```

## Managing Your Repository

### Pushing Updates

After making changes:

```bash
git add .
git commit -m "Your commit message"
git push origin main
```

### Creating New Releases

For new versions:

```bash
git tag -a v0.0.2 -m "DataQE Framework v0.0.2"
git push origin v0.0.2
```

### Branching for Features

```bash
# Create feature branch
git checkout -b feature/new-connector

# Make changes and commit
git add .
git commit -m "Add PostgreSQL connector"

# Push feature branch
git push origin feature/new-connector

# On GitHub, create Pull Request to merge into main
```

## Resources

- GitHub Docs: https://docs.github.com
- Git Basics: https://git-scm.com/doc
- PyPI Publishing: https://packaging.python.org
- Your Account: https://github.com/ShaikKhadarmohiddin

## Success Checklist

After completing all steps:

- [ ] GitHub account active
- [ ] Repository created at https://github.com/ShaikKhadarmohiddin/dataqe-framework
- [ ] Local git initialized
- [ ] All files staged and committed
- [ ] Remote added and verified
- [ ] Code pushed to GitHub
- [ ] Repository is PUBLIC
- [ ] Release tag v0.0.1 created and pushed
- [ ] Users can clone: `git clone https://github.com/ShaikKhadarmohiddin/dataqe-framework.git`
- [ ] Users can install: `pip install git+https://github.com/ShaikKhadarmohiddin/dataqe-framework.git`

✓ Your DataQE Framework is now PUBLIC and INSTALLABLE!

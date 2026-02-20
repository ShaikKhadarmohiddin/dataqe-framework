# Quick GitHub Push - Copy & Paste Commands

Fast reference for pushing DataQE Framework to GitHub in 5 minutes.

## Before You Start

1. Create GitHub account at https://github.com if needed
2. Create a NEW repository at https://github.com/new
   - Name: `dataqe-framework`
   - Make it **PUBLIC**
   - DO NOT check "Add README"
3. Copy your repository HTTPS URL from GitHub

## Quick Setup (Run These Commands)

Replace `YOUR_USERNAME` with your actual GitHub username, then run:

```bash
# Step 1: Configure Git
git config --global user.name "Khadar Shaik"
git config --global user.email "khadarmohiddin.shaik@apree.health"

# Step 2: Go to project directory
cd /Users/khadarmohiddin.shaik/Projects/Ventana/dataqe-framework

# Step 3: Initialize git
git init

# Step 4: Add all files
git add .

# Step 5: Create initial commit
git commit -m "Initial commit: DataQE Framework v0.0.1"

# Step 6: Add remote (REPLACE YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/dataqe-framework.git

# Step 7: Rename branch to main
git branch -M main

# Step 8: Push to GitHub
git push -u origin main

# Step 9: Create release tag
git tag -a v0.0.1 -m "DataQE Framework v0.0.1 - Initial Release"
git push origin v0.0.1
```

## Verify It Worked

```bash
# Check remote
git remote -v

# Should show:
# origin  https://github.com/YOUR_USERNAME/dataqe-framework.git (fetch)
# origin  https://github.com/YOUR_USERNAME/dataqe-framework.git (push)

# View commit history
git log --oneline

# Check tags
git tag -l
```

## Installation for Users

After pushing, users can install via:

```bash
# Direct from GitHub
pip install git+https://github.com/YOUR_USERNAME/dataqe-framework.git

# Or clone and install
git clone https://github.com/YOUR_USERNAME/dataqe-framework.git
cd dataqe-framework
pip install -e .
```

## Common Mistakes & Fixes

### Error: "fatal: not a git repository"
**Fix**: Run `git init` first

### Error: "repository already exists on this server"
**Fix**: Make sure you created the repo on GitHub at https://github.com/new

### Error: "src refspec main does not match any"
**Fix**: Make sure you committed before pushing (`git commit` step)

### Error: "Repository not found"
**Fix**: Check URL is correct, replace `YOUR_USERNAME` with your actual username

## What Gets Uploaded

✓ All Python source code
✓ All documentation files
✓ Configuration files
✓ Example files
✓ LICENSE and .gitignore

✗ Credentials/secrets (safely ignored)
✗ Virtual environment (safely ignored)
✗ Output directory (safely ignored)

## Make It Public (Already Done!)

Repository is set to **PUBLIC** during creation, so anyone can:
- Clone it
- View code
- Install it via pip

## Next: Make It Installable via pip (Optional)

To make `pip install dataqe-framework` work:

1. Create PyPI account: https://pypi.org/account/register/
2. Run:
```bash
pip install build twine
python -m build
python -m twine upload dist/*
```

Then anyone can: `pip install dataqe-framework`

## Commands Cheat Sheet

```bash
# Check status
git status

# See what's staged
git diff --cached

# See changes not staged
git diff

# View history
git log --oneline -10

# Create new branch
git checkout -b feature-name

# Switch branch
git checkout main

# Merge branch
git merge feature-name

# Delete branch
git branch -d feature-name

# Push new branch
git push origin feature-name

# Create new tag
git tag -a v0.0.2 -m "Version 0.0.2"
git push origin v0.0.2

# View all remotes
git remote -v

# Change remote URL
git remote set-url origin NEW_URL
```

## Questions?

See detailed guide: [GITHUB_SETUP.md](GITHUB_SETUP.md)

## Done! ✓

Your repository is now:
- ✓ On GitHub
- ✓ Public
- ✓ Installable via git
- ✓ Ready for collaboration

#!/bin/bash

# Pre-commit Setup Script for MINDGUARD Project
# This script installs and configures pre-commit hooks

set -e  # Exit on error

echo "======================================================================"
echo "MINDGUARD Pre-commit Hooks Setup"
echo "======================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python 3 found${NC}"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}Error: pip3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ pip3 found${NC}"
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: Not in a git repository${NC}"
    echo "Please initialize git first with: git init"
    exit 1
fi

echo -e "${GREEN}✓ Git repository detected${NC}"
echo ""

# Install pre-commit if not already installed
echo "Checking pre-commit installation..."
if ! command -v pre-commit &> /dev/null; then
    echo -e "${YELLOW}Installing pre-commit...${NC}"
    pip3 install pre-commit
    echo -e "${GREEN}✓ pre-commit installed${NC}"
else
    echo -e "${GREEN}✓ pre-commit already installed${NC}"
fi

# Install development dependencies
echo ""
echo "Installing development dependencies..."
echo "----------------------------------------------------------------------"

# Create requirements-dev.txt if it doesn't exist
cat > requirements-dev.txt << 'EOF'
# Development dependencies
black>=23.3.0
isort>=5.12.0
flake8>=6.0.0
flake8-docstrings>=1.7.0
flake8-bugbear>=23.3.0
flake8-comprehensions>=3.12.0
flake8-simplify>=0.20.0
mypy>=1.3.0
pytest>=7.3.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
pre-commit>=3.3.0
bandit>=1.7.5
types-requests>=2.31.0
types-PyYAML>=6.0.12
EOF

echo "Installing from requirements-dev.txt..."
pip3 install -r requirements-dev.txt

echo -e "${GREEN}✓ Development dependencies installed${NC}"
echo ""

# Check if pre_commit_config.yaml exists
if [ ! -f "configs/pre_commit_config.yaml" ]; then
    echo -e "${YELLOW}Warning: pre_commit_config.yaml not found${NC}"
    echo "Please ensure pre_commit_config.yaml is in the config directory"
    exit 1
fi
echo -e "${GREEN}✓ pre_commit_config.yaml found${NC}"

# Install pre-commit hooks
echo ""
echo "Installing pre-commit hooks..."
echo "----------------------------------------------------------------------"
pre-commit install

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Pre-commit hooks installed successfully${NC}"
else
    echo -e "${RED}✗ Error installing pre-commit hooks${NC}"
    exit 1
fi

# Install hooks for commit-msg (optional)
echo ""
echo "Installing commit-msg hooks..."
pre-commit install --hook-type commit-msg

# Create initial secrets baseline
echo ""
echo "Creating secrets baseline..."
if command -v detect-secrets &> /dev/null; then
    detect-secrets scan > .secrets.baseline
    echo -e "${GREEN}✓ Secrets baseline created${NC}"
else
    echo -e "${YELLOW}Warning: detect-secrets not found, skipping baseline creation${NC}"
fi

# Run pre-commit on all files (optional but recommended)
echo ""
echo "Would you like to run pre-commit on all existing files? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo ""
    echo "Running pre-commit on all files..."
    echo "----------------------------------------------------------------------"
    pre-commit run --all-files || true
    echo ""
    echo -e "${BLUE}Note: Some checks may have failed. This is normal for existing code.${NC}"
    echo -e "${BLUE}The hooks will prevent new violations in future commits.${NC}"
fi

# Create .gitignore additions for linting/testing artifacts
echo ""
echo "Adding linting/testing artifacts to .gitignore..."

cat >> .gitignore << 'EOF'

# Pre-commit and linting
.pre-commit-cache/
.mypy_cache/
.pytest_cache/
.coverage
htmlcov/
*.cover
.hypothesis/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
EOF

echo -e "${GREEN}✓ .gitignore updated${NC}"

# Summary
echo ""
echo "======================================================================"
echo "✓ Pre-commit Setup Complete!"
echo "======================================================================"
echo ""
echo "Installed hooks:"
echo "  ✓ Code formatting (Black, isort)"
echo "  ✓ Linting (flake8)"
echo "  ✓ Type checking (mypy)"
echo "  ✓ Security checks (bandit, detect-secrets)"
echo "  ✓ File checks (trailing whitespace, large files, etc.)"
echo ""
echo "Next steps:"
echo "  1. Commit your changes: git add . && git commit -m 'Setup pre-commit hooks'"
echo "  2. Pre-commit will run automatically on each commit"
echo "  3. To run manually: pre-commit run --all-files"
echo "  4. To update hooks: pre-commit autoupdate"
echo ""
echo "Configuration files:"
echo "  - pre_commit_config.yaml (hook configuration)"
echo "  - pyproject.toml (tool configuration)"
echo "  - .flake8 (flake8 configuration)"
echo "  - requirements-dev.txt (development dependencies)"
echo ""
echo "Useful commands:"
echo "  pre-commit run --all-files    Run all hooks on all files"
echo "  pre-commit run <hook-id>      Run specific hook"
echo "  pre-commit autoupdate         Update hook versions"
echo "  git commit --no-verify        Skip pre-commit hooks (use sparingly)"
echo ""

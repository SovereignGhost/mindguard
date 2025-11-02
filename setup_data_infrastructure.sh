#!/bin/bash

# MINDGUARD Data Infrastructure Setup Script
# This script sets up the complete data directory structure

set -e  # Exit on error

echo "======================================================================"
echo "MINDGUARD Data Infrastructure Setup"
echo "======================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python 3 found${NC}"

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "  Python version: $PYTHON_VERSION"

# Create project root if needed
PROJECT_ROOT="$(pwd)"
echo ""
echo "Project root: $PROJECT_ROOT"
echo ""

# Create necessary Python files if they don't exist
echo "Setting up Python modules..."

if [ ! -f "data_setup.py" ]; then
    echo -e "${YELLOW}Warning: data_setup.py not found in current directory${NC}"
    echo "Please ensure data_setup.py is in the current directory"
    exit 1
fi

if [ ! -f "data_utils.py" ]; then
    echo -e "${YELLOW}Warning: data_utils.py not found in current directory${NC}"
    echo "Please ensure data_utils.py is in the current directory"
    exit 1
fi

echo -e "${GREEN}✓ Python modules found${NC}"
echo ""

# Run the data setup script
echo "Running data infrastructure setup..."
echo "----------------------------------------------------------------------"
python3 data_setup.py

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Data infrastructure created successfully!${NC}"
else
    echo ""
    echo -e "${RED}✗ Error creating data infrastructure${NC}"
    exit 1
fi

echo ""
echo "======================================================================"
echo "Setup Complete!"
echo "======================================================================"
echo ""
echo "Next steps:"
echo "  1. Review the created structure in ./data/"
echo "  2. Check schemas in ./data/schemas/"
echo "  3. Review example data in ./data/examples/"
echo "  4. Customize ./data/configs/dataset_config.json as needed"
echo ""
echo "To verify the setup, run:"
echo "  python3 data_utils.py"
echo ""
echo "To start generating synthetic data, proceed to Phase 2 tasks."
echo ""

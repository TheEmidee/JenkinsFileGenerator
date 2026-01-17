#!/bin/bash
# Bash script to set up Python virtual environment and install requirements
# Usage: ./setup-env.sh [--venv-name NAME] [--pyproject FILE] [--force]

set -e  # Exit on error

# Default values
VENV_NAME=".venv"
PYPROJECT_FILE="pyproject.toml"
FORCE=false

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --venv-name)
            VENV_NAME="$2"
            shift 2
            ;;
        --pyproject)
            PYPROJECT_FILE="$2"
            shift 2
            ;;
        --force)
            FORCE=true
            shift
            ;;
        *)
            echo -e "${RED}Error: Unknown parameter: $1${NC}"
            echo "Usage: $0 [--venv-name NAME] [--pyproject FILE] [--force]"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}Setting up Python virtual environment...${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed or not in PATH${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
echo -e "${YELLOW}Found Python: $PYTHON_VERSION${NC}"

# Check if pyproject.toml exists
if [[ ! -f "$PYPROJECT_FILE" ]]; then
    echo -e "${YELLOW}Warning: $PYPROJECT_FILE not found in current directory${NC}"
    read -p "Continue without installing requirements? (y/n): " response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Remove existing virtual environment if Force flag is used
if [[ "$FORCE" == true ]] && [[ -d "$VENV_NAME" ]]; then
    echo -e "${YELLOW}Removing existing virtual environment...${NC}"
    rm -rf "$VENV_NAME"
fi

# Create virtual environment if it doesn't exist
if [[ ! -d "$VENV_NAME" ]]; then
    echo -e "${YELLOW}Creating virtual environment '$VENV_NAME'...${NC}"
    python3 -m venv "$VENV_NAME"
    echo -e "${GREEN}Virtual environment created successfully!${NC}"
else
    echo -e "${YELLOW}Virtual environment '$VENV_NAME' already exists${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source "$VENV_NAME/bin/activate"

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
python -m pip install --upgrade pip

# Install requirements if file exists
if [[ -f "$PYPROJECT_FILE" ]]; then
    echo -e "${YELLOW}Installing packages from $PYPROJECT_FILE...${NC}"
    if pip install -e .[dev]; then
        echo -e "${GREEN}All packages installed successfully!${NC}"
    else
        echo -e "${RED}Error: Some packages failed to install${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}Skipping package installation - no requirements file found${NC}"
fi

echo -e "\n${GREEN}Setup complete!${NC}"
echo -e "${GREEN}Virtual environment is now active.${NC}"
echo -e "${CYAN}To deactivate later, run: deactivate${NC}"
echo -e "${CYAN}To activate again, run: source $VENV_NAME/bin/activate${NC}"
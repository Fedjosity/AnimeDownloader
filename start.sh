#!/bin/bash

# Script to set up and run the AnimeDownloader project

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}AnimeDownloader Setup Script${NC}"
echo "================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating one...${NC}"
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Failed to create virtual environment. Make sure python3 is installed.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Virtual environment created successfully!${NC}"
else
    echo -e "${GREEN}Virtual environment found.${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to activate virtual environment.${NC}"
    exit 1
fi

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: requirements.txt not found!${NC}"
    exit 1
fi

# Check if packages are installed by trying to import a key package
echo -e "${YELLOW}Checking if requirements are installed...${NC}"
python3 -c "import requests, tqdm, colorama, simple_term_menu" 2>/dev/null

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Installing requirements...${NC}"
    pip install --upgrade pip
    pip install -r requirements.txt
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Failed to install requirements.${NC}"
        exit 1
    fi
    
    # Install playwright browsers if playwright is in requirements
    if grep -q "playwright" requirements.txt; then
        echo -e "${YELLOW}Installing Playwright browsers...${NC}"
        playwright install chromium
    fi
    
    echo -e "${GREEN}Requirements installed successfully!${NC}"
else
    echo -e "${GREEN}Requirements already installed.${NC}"
fi

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo -e "${RED}Error: main.py not found!${NC}"
    exit 1
fi

# Start the project
echo -e "${GREEN}Starting AnimeDownloader...${NC}"
echo "================================"
python3 main.py


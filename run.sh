#!/bin/bash

# ATS-Proof Resume Generator
# This script sets up and runs the ATS-Proof Resume application

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to display help
show_help() {
    echo -e "${GREEN}ATS-Proof Resume Generator${NC}"
    echo "Usage: ./run.sh [option]"
    echo ""
    echo "Options:"
    echo "  --help, -h     Show this help message"
    echo "  --test, -t     Run tests to verify dependencies"
    echo "  --docker, -d   Build and run using Docker"
    echo ""
    echo "If no option is provided, the application will start normally."
}

# Function to test imports
test_imports() {
    echo -e "${YELLOW}Testing dependencies...${NC}"
    
    # First check if packages are installed
    python test_deps.py
    if [ $? -ne 0 ]; then
        echo -e "${RED}Some dependencies are missing. Please install them as indicated above.${NC}"
        return 1
    fi
    
    # Then try the more comprehensive import test if the first test passes
    python test_imports.py
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}All imports successful!${NC}"
        return 0
    else
        echo -e "${RED}Some imports failed. Check the output above.${NC}"
        return 1
    fi
}

# Function to build and run with Docker
run_docker() {
    echo -e "${YELLOW}Building Docker image...${NC}"
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
        exit 1
    fi
    
    docker build -t ats-resume .
    if [ $? -ne 0 ]; then
        echo -e "${RED}Docker build failed.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Running Docker container...${NC}"
    echo "The application will be available at http://localhost:8000"
    docker run -p 8000:8000 ats-resume
}

# Function to find an available port
find_available_port() {
    local port=8000
    while netstat -tuln | grep -q ":$port "; do
        echo -e "${YELLOW}Port $port is already in use. Trying next port...${NC}"
        port=$((port + 1))
    done
    echo $port
}

# Process command line arguments
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
elif [ "$1" = "--test" ] || [ "$1" = "-t" ]; then
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    test_imports
    exit 0
elif [ "$1" = "--docker" ] || [ "$1" = "-d" ]; then
    run_docker
    exit 0
fi

# Normal execution starts here
echo -e "${GREEN}=== ATS-Proof Resume Generator ===${NC}"
echo "Setting up environment..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create virtual environment. Please install venv package.${NC}"
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install or upgrade dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Test imports
test_imports

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}Warning: OPENAI_API_KEY environment variable is not set.${NC}"
    echo -e "${YELLOW}You will need to provide an API key in the web interface.${NC}"
fi

# Create necessary directories
mkdir -p output

# Add cleanup function
cleanup() {
    echo -e "${YELLOW}Shutting down...${NC}"
    deactivate 2>/dev/null || true
    echo -e "${GREEN}Done!${NC}"
}

# Register the cleanup function to run on script exit
trap cleanup EXIT

# Run the application
echo -e "${GREEN}Starting ATS-Proof Resume Generator...${NC}"
PORT=$(find_available_port)
echo "The application will be available at http://localhost:$PORT"

# Debug Python path
echo "Current directory: $(pwd)"
echo "Python path: $PYTHONPATH"
python -c "import sys; print('sys.path:', sys.path)"

# Try to find the main app file
if [ -f "app/main.py" ]; then
    echo "Found app/main.py"
    python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT --reload || {
        echo -e "${RED}Failed to start the application. Check the error message above.${NC}"
        exit 1
    }
elif [ -f "main.py" ]; then
    echo "Found main.py at root level"
    python -m uvicorn main:app --host 0.0.0.0 --port $PORT --reload || {
        echo -e "${RED}Failed to start the application. Check the error message above.${NC}"
        exit 1
    }
else
    echo -e "${RED}Could not find main.py. Please create it or specify the correct path.${NC}"
    exit 1
fi

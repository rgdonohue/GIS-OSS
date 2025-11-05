#!/bin/bash

# GIS-OSS Development Environment Setup Script
# Run this script to set up your local development environment

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== GIS-OSS Development Setup ===${NC}"

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi
echo "✓ Docker found"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose"
    exit 1
fi
echo "✓ Docker Compose found"

# Check Python 3.8+
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo -e "${RED}Error: Python $required_version or higher is required (found $python_version)${NC}"
    exit 1
fi
echo "✓ Python $python_version found"

# Create necessary directories
echo -e "\n${YELLOW}Creating directories...${NC}"
mkdir -p data cache models logs
mkdir -p config/postgres config/models config/tools
echo "✓ Directories created"

# Set up environment file
echo -e "\n${YELLOW}Setting up environment variables...${NC}"
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✓ Created .env from .env.example"
        echo -e "${YELLOW}  Please edit .env and set POSTGRES_PASSWORD${NC}"
    else
        echo -e "${RED}Warning: .env.example not found${NC}"
    fi
else
    echo "✓ .env already exists"
fi

# Create Python virtual environment
echo -e "\n${YELLOW}Setting up Python virtual environment...${NC}"
if [ ! -d venv ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
source venv/bin/activate

echo -e "\n${YELLOW}Installing Python dependencies...${NC}"
pip install --upgrade pip

# Create requirements.txt if it doesn't exist
if [ ! -f requirements.txt ]; then
    cat > requirements.txt << EOF
# Core dependencies
fastapi==0.104.0
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
psycopg2-binary==2.9.9
sqlalchemy==2.0.23
geoalchemy2==0.14.2
asyncpg==0.29.0

# Spatial processing
shapely==2.0.2
pyproj==3.6.1
geojson==3.1.0
geopandas==0.14.1

# LLM (Week 2+)
# vllm==0.2.7
# llama-cpp-python==0.2.20
# transformers==4.36.0
# sentence-transformers==2.2.2

# Utilities
python-dotenv==1.0.0
httpx==0.25.2
redis==5.0.1
structlog==23.2.0

# Development
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.12.0
ruff==0.1.8
mypy==1.7.1
ipython==8.18.1

# API extras
slowapi==0.1.9
python-multipart==0.0.6
EOF
    echo "✓ Created requirements.txt"
fi

pip install -r requirements.txt
echo "✓ Python dependencies installed"

# Check if .env has been configured
if [ -f .env ]; then
    if grep -q "changeme" .env; then
        echo -e "\n${YELLOW}⚠ WARNING: Please update the default passwords in .env${NC}"
    fi
fi

# Download sample data
echo -e "\n${YELLOW}Downloading sample data...${NC}"
if [ ! -f data/sample_data.json ]; then
    # Download a small GeoJSON sample (US states boundaries)
    curl -L -o data/us-states.json \
        "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json" \
        2>/dev/null || echo "Warning: Could not download sample data"
    echo "✓ Sample data downloaded"
else
    echo "✓ Sample data already exists"
fi

# Start services
echo -e "\n${YELLOW}Starting Docker services...${NC}"
docker-compose up -d postgres redis titiler

# Wait for PostgreSQL to be ready
echo -e "\n${YELLOW}Waiting for PostgreSQL to be ready...${NC}"
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker-compose exec -T postgres pg_isready -U gis_user -d gis_oss &>/dev/null; then
        echo "✓ PostgreSQL is ready"
        break
    fi
    echo -n "."
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "\n${RED}Error: PostgreSQL did not start in time${NC}"
    exit 1
fi

# Test PostGIS
echo -e "\n${YELLOW}Testing PostGIS installation...${NC}"
docker-compose exec -T postgres psql -U gis_user -d gis_oss -c "SELECT PostGIS_Version();" &>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ PostGIS is working"
else
    echo -e "${RED}Error: PostGIS test failed${NC}"
fi

# Summary
echo -e "\n${GREEN}=== Setup Complete ===${NC}"
echo
echo "Services running:"
echo "  • PostgreSQL with PostGIS: localhost:5432"
echo "  • Redis: localhost:6379"
echo "  • TiTiler: http://localhost:8081"
echo
echo "Next steps:"
echo "  1. Edit .env file with your configuration"
echo "  2. Activate Python environment: source venv/bin/activate"
echo "  3. Run tests: pytest tests/"
echo "  4. Start development: python src/api/main.py"
echo
echo "To stop services: docker-compose down"
echo "To view logs: docker-compose logs -f"
echo
echo -e "${GREEN}Happy coding!${NC}"
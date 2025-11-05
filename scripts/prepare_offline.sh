#!/bin/bash

# GIS-OSS Offline Preparation Script
# Downloads all required data and dependencies for air-gapped deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== GIS-OSS Offline Preparation ===${NC}"
echo "This script downloads all dependencies for offline/air-gapped deployment"
echo

# Create necessary directories
mkdir -p data cache models offline-deps

# Download sample data
echo -e "${YELLOW}Downloading sample datasets...${NC}"

# US States GeoJSON
if [ ! -f data/us-states.json ]; then
    echo "  Downloading US states boundaries..."
    curl -L -o data/us-states.json \
        "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json" \
        || echo "Failed to download US states data"
fi

# Natural Earth data (public domain)
if [ ! -f data/ne_10m_admin_0_countries.geojson ]; then
    echo "  Downloading Natural Earth countries..."
    curl -L -o data/ne_10m_admin_0_countries.zip \
        "https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/ne_10m_admin_0_countries.zip" \
        2>/dev/null || echo "Failed to download Natural Earth data"
fi

# Download PROJ database for offline CRS lookups
echo -e "\n${YELLOW}Downloading PROJ database...${NC}"
if [ ! -f offline-deps/proj.db ]; then
    echo "  Downloading PROJ database (150MB)..."
    curl -L -o offline-deps/proj.db \
        "https://cdn.proj.org/proj.db" \
        || echo "Failed to download PROJ database"
else
    echo "  PROJ database already exists"
fi

# Download EPSG registry snapshot (for reference)
echo -e "\n${YELLOW}Downloading EPSG registry...${NC}"
if [ ! -f offline-deps/epsg-registry.json ]; then
    echo "  Creating EPSG reference file..."
    # Download common EPSG codes
    cat > offline-deps/epsg-registry.json << 'EOF'
{
  "4326": {"name": "WGS 84", "type": "geographic", "unit": "degree"},
  "3857": {"name": "WGS 84 / Pseudo-Mercator", "type": "projected", "unit": "meter"},
  "3395": {"name": "WGS 84 / World Mercator", "type": "projected", "unit": "meter"},
  "32633": {"name": "WGS 84 / UTM zone 33N", "type": "projected", "unit": "meter"},
  "2163": {"name": "US National Atlas Equal Area", "type": "projected", "unit": "meter"},
  "note": "Full EPSG database available in proj.db"
}
EOF
fi

# Create carbon intensity lookup table (mock data for offline)
echo -e "\n${YELLOW}Creating carbon intensity lookup table...${NC}"
if [ ! -f offline-deps/carbon-intensity.json ]; then
    cat > offline-deps/carbon-intensity.json << 'EOF'
{
  "regions": {
    "US-WEST": {"gCO2_per_kWh": 250, "updated": "2024-01-01"},
    "US-EAST": {"gCO2_per_kWh": 450, "updated": "2024-01-01"},
    "EU-CENTRAL": {"gCO2_per_kWh": 350, "updated": "2024-01-01"},
    "GLOBAL-AVG": {"gCO2_per_kWh": 475, "updated": "2024-01-01"}
  },
  "note": "Static values for offline mode. Connect to WattTime API for real-time data."
}
EOF
fi

# Download Python packages for offline pip install
echo -e "\n${YELLOW}Downloading Python packages...${NC}"
if [ ! -d offline-deps/pip-cache ]; then
    echo "  Downloading Python dependencies..."
    pip download -d offline-deps/pip-cache -r requirements.txt \
        2>/dev/null || echo "Some packages may need manual download"
fi

# Pull Docker images for offline deployment
echo -e "\n${YELLOW}Pulling Docker images...${NC}"
docker pull postgis/postgis:15-3.4 || echo "Failed to pull PostGIS"
docker pull redis:7-alpine || echo "Failed to pull Redis"
docker pull ghcr.io/developmentseed/titiler:latest || echo "Failed to pull TiTiler"

# Save Docker images for transfer
echo -e "\n${YELLOW}Saving Docker images...${NC}"
docker save -o offline-deps/docker-images.tar \
    postgis/postgis:15-3.4 \
    redis:7-alpine \
    ghcr.io/developmentseed/titiler:latest \
    2>/dev/null || echo "Failed to save Docker images"

# Create offline installation instructions
cat > offline-deps/OFFLINE_INSTALL.md << 'EOF'
# Offline Installation Instructions

## Prerequisites
- Docker and Docker Compose installed
- Python 3.8+ installed
- This offline-deps directory copied to target machine

## Installation Steps

1. Load Docker images:
   ```bash
   docker load -i offline-deps/docker-images.tar
   ```

2. Install Python packages:
   ```bash
   pip install --no-index --find-links offline-deps/pip-cache -r requirements.txt
   ```

3. Copy PROJ database:
   ```bash
   cp offline-deps/proj.db /usr/share/proj/
   # Or set PROJ_LIB environment variable to point to offline-deps/
   ```

4. Set environment variable for offline mode:
   ```bash
   echo "ENABLE_OFFLINE_MODE=true" >> .env
   ```

5. Run setup script:
   ```bash
   ./scripts/setup_dev.sh
   ```

## Available Offline Data
- US states boundaries (data/us-states.json)
- PROJ CRS database (offline-deps/proj.db)
- Carbon intensity lookup (offline-deps/carbon-intensity.json)
- EPSG reference (offline-deps/epsg-registry.json)
EOF

# Summary
echo -e "\n${GREEN}=== Offline Preparation Complete ===${NC}"
echo
echo "Downloaded assets:"
echo "  • Sample geodata in ./data/"
echo "  • PROJ database in ./offline-deps/"
echo "  • Carbon intensity lookup table"
echo "  • Docker images saved to tar archive"
echo
echo "To deploy offline:"
echo "  1. Copy entire project directory to air-gapped system"
echo "  2. Follow instructions in offline-deps/OFFLINE_INSTALL.md"
echo
echo -e "${GREEN}Total size:${NC} $(du -sh offline-deps | cut -f1)"
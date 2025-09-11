# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Foodie is a Python application that uses geospatial tools to create maps for food-related locations. The project utilizes the Folium library for map creation and OpenStreetMap's Nominatim API for geocoding addresses.

## Development Environment Setup

### Requirements
- Python 3.13+
- Dependencies managed via `pyproject.toml`

### Installation
```bash
# Install with uv (recommended)
uv pip install -e .

# Alternative: standard pip
pip install -e .
```

## Project Structure

- `foodie/`: Main package directory
  - `agents/`: Contains agents for different functionalities
    - `map_agent.py`: Provides geocoding and map creation functionality

## Key Components

### Map Agent (`foodie/agents/map_agent.py`)
- Converts addresses to coordinates using OpenStreetMap's Nominatim API
- Creates interactive maps with markers for specified addresses
- Outputs maps as HTML files

## Common Development Tasks

### Running the Map Creation
```python
from foodie.agents.map_agent import create_static_map

addresses = [
    "Restaurant A, City, State",
    "Restaurant B, City, State"
]
map_file = create_static_map(addresses)
```

### Important Notes
- The application uses Nominatim's geocoding API which requires a proper User-Agent header
- Currently saves maps as HTML files, which would need manual conversion to static images
- Rate limits apply when using the Nominatim API extensively
import os
import time
from pathlib import Path
from mcp import types
import folium
import requests
from mcp.server.fastmcp import FastMCP
from foodie.util.gdrive import Uploader

# Initialize FastMCP server
mcp = FastMCP("map_agent")


def address_to_coordinates(address):
    """Convert address to lat/lng using Nominatim (free OSM geocoding)"""
    base_url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': address,
        'format': 'json',
        'limit': 1
    }
    headers = {'User-Agent': 'Foodie-App/1.0'}  # Required by Nominatim

    response = requests.get(base_url, params=params, headers=headers)
    data = response.json()

    # Add delay to comply with Nominatim's 1 request per second policy
    time.sleep(1)

    if data:
        return float(data[0]['lat']), float(data[0]['lon'])
    return None, None


@mcp.tool()
def create_static_map(addresses, zoom=12, width=800, height=600, file_name='temp_map.html') -> dict:
    """
    Create map link text for given addresses
    This link is markdown text can be displayed in Claude desktop

    Args:
        addresses (str, list):
        zoom (int): Default zoom is 12
        width (int): Default width is 800
        height (int): Default height is 600
        file_name (str, optional): Defaults to 'temp_map.html'

    Returns:
        dict:

    """
    coordinates = []

    if type(addresses) is str:
        addresses = [addresses]

    try:
    # Convert addresses to coordinates
        for address in addresses:
            lat, lng = address_to_coordinates(address)
            if lat and lng:
                coordinates.append((lat, lng, address))
                print(f"Found: {address} -> {lat}, {lng}")
            else:
                print(f"Could not geocode: {address}")

        if not coordinates:
            print("No valid addresses found!")
            return None

        # Calculate center point
        center_lat = sum(coord[0] for coord in coordinates) / len(coordinates)
        center_lng = sum(coord[1] for coord in coordinates) / len(coordinates)

        # Create map
        m = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=zoom,
            width=width,
            height=height
        )

        # Add markers
        for lat, lng, address in coordinates:
            folium.Marker(
                location=[lat, lng],
                popup=address,
                tooltip=address
            ).add_to(m)

        html_file = os.path.abspath(file_name)
        m.save(html_file)

        # For static image, you can use selenium + webdriver
        # or save as HTML and screenshot manually
        print(f"Map saved as {html_file}")

        # Now, upload to google drive
        gd = Uploader()
        res = gd.upload_and_share(html_file, drive_filename='test.html',
                                  role='reader', folder_id='17PwiYM8pTqLqEXVYwJiyvZD8mafRYjf2')

        if res['success']:
            markdown_link = f"[{'link'}]({res['share_link']})"
        else:


        return {
            "content": [
                {
                    "type": "text",
                    "text": f"[{link_text}]({markdown_link})"
                }
            ]
        }
    except Exception as e:
        return f"Error: {str(e)}"  # Return error message instead of 0


if __name__ == "__main__":
    mcp.run(transport='stdio')

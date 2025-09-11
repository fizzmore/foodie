import time
from pathlib import Path

import folium
import requests
from mcp.server.fastmcp import FastMCP
import io
from PIL import Image


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
def create_static_map(addresses, is_static=True, zoom=12, width=800, height=600):
    """
    Create static map with given addresses
    static map is image data which can be shown in Claude desktop naively

    :param addresses:
    :param zoom:
    :param width:
    :param height:
    :return:
    """
    coordinates = []

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

        # Save as static png file
        if is_static:
            img_data = m._to_png(1)
            # img = Image.open(io.BytesIO(img_data))

            return {
                "image_data": img_data,
                "mime_type": "image/png",  # or image/jpeg
                "width": width,
                "height": height,
            }

            return {"image": f"data:image/png;base64,{img_data}"}
        else:
            html_file = "temp_map.html"
            m.save(html_file)

            # For static image, you can use selenium + webdriver
            # or save as HTML and screenshot manually
            print(f"Map saved as {html_file}")

            file_path = Path(html_file)

            with open(file_path, 'r', encoding='utf-8') as html_file:
                html_content = html_file.read()
                return html_content
    except Exception as e:
        return f"Error: {str(e)}"  # Return error message instead of 0


if __name__ == "__main__":
    mcp.run(transport='stdio')

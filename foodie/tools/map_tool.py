import os
import time
from datetime import datetime
from pathlib import Path
import folium
import requests
from foodie.util.github_util import GitHubUploader
from dotenv import load_dotenv


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


def create_static_map(addresses, zoom=12, width=800, height=600, file_name='temp_map.html', by='surge') -> dict:
    """
    Create map link text for given addresses
    This link is markdown text can be displayed in Claude desktop

    Args:
        addresses (str): If you have multiple addresses, it should be separated by | (pipe string)
        zoom (int): Default zoom is 12
        width (int): Default width is 800
        height (int): Default height is 600
        file_name (str, optional): Defaults to 'temp_map.html'
        by (str): 'surge' or 'github' for hosting service. Default is 'surge'.

    Returns:
        dict:

    """
    coordinates = []

    address_list = [ele.strip().replace('\"', '') for ele in addresses.split('|') if len(ele) > 10]

    try:
    # Convert address_list to coordinates
        error_msg = ""
        for address in address_list:
            lat, lng = address_to_coordinates(address)
            if lat and lng:
                coordinates.append((lat, lng, address))
                print(f"Found: {address} -> {lat}, {lng}")
            else:
                print(f"Could not geocode: {address}")
                error_msg += f"Could not geocode: {address}\n"

        if not coordinates:
            print("No valid addresses found!")
            return {"content": [{"type": "text",
                                 "text": f"[error] No valid addresses found!\n{error_msg}"}]
                    }

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

        if by == 'surge':
            from foodie.util.surge_util import upload_to_surge
            project_name = f"foodie-map-{int(time.time())}"
            surge_result = upload_to_surge(html_file, project_name=project_name)

            # Clean up local file
            try:
                os.remove(html_file)
            except:
                pass

            if surge_result['success']:
                markdown_link = f"[{'link'}]({surge_result['url']})"
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"[link]({markdown_link})"
                        }
                    ]
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"[error]({surge_result['error']}) ({surge_result['output']})"
                        }
                    ]
                }
        elif by == 'github':
            # Now, upload to github
            load_dotenv(Path(Path(__file__).parents[1], '.env'))
            github_token = os.getenv('FIZZ_GITHUB')
            username = "fizzmore"  # Your GitHub username
            repo_name = "foodie"  # Your repository name

            uploader  = GitHubUploader(github_token, username, repo_name)

            # Get date time without '-' and ':' for html path
            now_str = str(datetime.now()).split('.')[0].replace(' ', '_')
            now_str = now_str.replace('-', '').replace(':', '')

            if file_name.endswith('.html'):
                file_name = file_name.split('.html')[0]

            repo_file_path = f'docs/{file_name}__{now_str}.html'
            res = uploader.upload_file(html_file, repo_file_path=repo_file_path)

            # Clean up local file
            try:
                os.remove(html_file)
            except:
                pass

            if res['success']:
                markdown_link = f"[{'link'}]({res['urls']['pages_url']})"
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"[link]({markdown_link})"
                        }
                    ]
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"[error]({res['error_details']})"
                        }
                    ]
                }
        else:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"[error](by should be 'surge' or 'github')"
                    }
                ]
            }

    except Exception as e:
        return {
                "content": [
                    {
                        "type": "text",
                        "text": f"[error]({str(e)})"
                    }
                ]
            }




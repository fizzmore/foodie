import os
import subprocess
import tempfile
import shutil
import random
import string
import time
from pathlib import Path


def upload_to_surge(local_file_path, custom_domain=None, project_name=None):
    """
    Upload HTML file to Surge.sh for instant hosting with no authentication required

    Args:
        local_file_path (str): Path to the HTML file to upload
        custom_domain (str, optional): Custom domain (e.g., my-app.surge.sh)
        project_name (str, optional): Name for the project, used to generate domain
                                      if custom_domain not provided

    Returns:
        dict: Upload result with URL and status
    """
    # Verify file exists
    if not os.path.exists(local_file_path):
        return {
            'success': False,
            'error': f'Local file not found: {local_file_path}'
        }

    try:
        # Check if surge is installed
        try:
            result = subprocess.run(
                ['which', 'surge'],
                capture_output=True,
                text=True,
                check=False
            )

            if not result.stdout.strip():
                return {
                    'success': False,
                    'error': 'Surge CLI not found. Please install with: npm install --global surge',
                    'install_command': 'npm install --global surge'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error checking for Surge CLI: {str(e)}',
                'install_command': 'npm install --global surge'
            }

        # Create a temp directory for the project
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy the HTML file to the temp dir as index.html
            target_file = os.path.join(temp_dir, 'index.html')
            shutil.copy2(local_file_path, target_file)
            print(f"📦 Copied {local_file_path} to {target_file}")

            # Determine the domain
            domain = None
            if custom_domain:
                domain = custom_domain
            elif project_name:
                domain = f"{project_name}.surge.sh"
            else:
                # Generate a random subdomain
                rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
                domain = f"foodie-{rand_str}.surge.sh"

            print(f"🌍 Deploying to domain: {domain}")

            # Deploy to Surge
            surge_cmd = ['surge', temp_dir, domain, '--output', 'json']

            try:
                result = subprocess.run(
                    surge_cmd,
                    capture_output=True,
                    text=True,
                    check=False
                )

                if result.returncode == 0:
                    # Success - parse output if possible
                    try:
                        print(f"🚀 Deployment successful!")

                        # Extract URL from output
                        # The output isn't proper JSON, so we'll have to parse it manually
                        lines = result.stdout.strip().split('\n')
                        url = None

                        for line in lines:
                            if domain in line and 'https://' in line:
                                url = line.strip()
                                break

                        if not url:
                            url = f"https://{domain}"

                        return {
                            'success': True,
                            'url': url,
                            'domain': domain,
                            'message': f"🚀 Site deployed successfully to Surge.sh!",
                            'output': result.stdout
                        }
                    except Exception as e:
                        return {
                            'success': True,
                            'url': f"https://{domain}",
                            'domain': domain,
                            'message': f"🚀 Site deployed successfully to Surge.sh!",
                            'parse_error': str(e),
                            'output': result.stdout
                        }
                else:
                    return {
                        'success': False,
                        'error': f'Surge deployment failed',
                        'details': result.stderr,
                        'output': result.stdout
                    }

            except Exception as e:
                return {
                    'success': False,
                    'error': f'Error executing Surge command: {str(e)}'
                }
    except Exception as e:
        return {
            'success': False,
            'error': f'Surge upload error: {str(e)}'
        }


def create_surge_map(addresses, zoom=12, width=800, height=600, file_name=None, custom_domain=None):
    """
    Create a map and deploy it to Surge.sh for instant public hosting

    Args:
        addresses (str): Pipe-separated addresses to map
        zoom (int): Map zoom level (default: 12)
        width (int): Map width in pixels (default: 800)
        height (int): Map height in pixels (default: 600)
        file_name (str, optional): Local filename for the map
        custom_domain (str, optional): Custom Surge.sh domain

    Returns:
        dict: Result with Surge.sh URL and deployment info
    """
    # Import here to avoid circular imports
    from foodie.tools.map_tool import address_to_coordinates
    import folium

    # Generate unique filename if not provided
    if not file_name:
        rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        file_name = f"surge_map_{rand_str}.html"

    coordinates = []
    address_list = [addr.strip().replace('"', '') for addr in addresses.split('|') if len(addr.strip()) > 10]

    try:
        # Geocode all addresses
        error_messages = []
        for address in address_list:
            lat, lng = address_to_coordinates(address)
            if lat and lng:
                coordinates.append((lat, lng, address))
                print(f"✅ Found: {address} -> {lat}, {lng}")
            else:
                error_msg = f"❌ Could not geocode: {address}"
                print(error_msg)
                error_messages.append(error_msg)

        if not coordinates:
            return {
                "content": [{
                    "type": "text",
                    "text": f"[error] No valid addresses found!\n" + "\n".join(error_messages)
                }]
            }

        # Calculate map center
        center_lat = sum(coord[0] for coord in coordinates) / len(coordinates)
        center_lng = sum(coord[1] for coord in coordinates) / len(coordinates)

        # Create the map
        m = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=zoom,
            width=width,
            height=height
        )

        # Add markers for each location
        for lat, lng, address in coordinates:
            folium.Marker(
                location=[lat, lng],
                popup=folium.Popup(address, max_width=300),
                tooltip=address
            ).add_to(m)

        # Save map locally first
        html_file = os.path.abspath(file_name)
        m.save(html_file)
        print(f"💾 Map saved locally: {html_file}")

        # Deploy to Surge
        project_name = f"foodie-map-{int(time.time())}"
        surge_result = upload_to_surge(html_file, custom_domain=custom_domain, project_name=project_name)

        # Clean up local file
        try:
            os.remove(html_file)
        except:
            pass

        if surge_result['success']:
            return {
                "content": [{
                    "type": "text",
                    "text": f"🗺️ **Map Deployed to Surge.sh!**\n\n" +
                           f"🔗 [View Map]({surge_result['url']})\n\n" +
                           f"⚡ **Instant Access** - No build time required!\n" +
                           f"📍 Locations: {len(coordinates)} mapped\n" +
                           f"🆔 Domain: {surge_result['domain']}\n\n" +
                           f"*Powered by Surge.sh*"
                }]
            }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": f"[error] Surge deployment failed: {surge_result['error']}"
                }]
            }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"[error] Map creation failed: {str(e)}"
            }]
        }
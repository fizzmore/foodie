import unittest
from unittest.mock import patch, Mock
from foodie.agents.map_agent import address_to_coordinates, create_static_map


class TestMapAgent(unittest.TestCase):
    @patch('foodie.agents.map_agent.requests.get')
    def test_address_to_coordinates(self, mock_get):
        # Mock the API response for a successful geocode
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                'lat': '40.7127753',
                'lon': '-74.0059728'
            }
        ]
        mock_get.return_value = mock_response

        # Test successful geocoding
        lat, lng = address_to_coordinates("New York, NY")
        self.assertIsNotNone(lat)
        self.assertIsNotNone(lng)
        self.assertEqual(lat, 40.7127753)
        self.assertEqual(lng, -74.0059728)
        
        # Verify API was called with the correct parameters
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs['params']['q'], "New York, NY")
        self.assertEqual(kwargs['params']['format'], 'json')
        
        # Test with empty response
        mock_response.json.return_value = []
        lat, lng = address_to_coordinates("Invalid Address")
        self.assertIsNone(lat)
        self.assertIsNone(lng)

    @patch('foodie.agents.map_agent.address_to_coordinates')
    @patch('foodie.agents.map_agent.folium.Map')
    @patch('foodie.agents.map_agent.folium.Marker')
    def test_create_static_map(self, mock_marker, mock_map, mock_geocode):
        # Mock the geocoding function to return known coordinates
        mock_geocode.side_effect = [
            (40.7580, -73.9855),  # Times Square
            (40.7812, -73.9665),  # Central Park
            (None, None)          # Failed geocode
        ]
        
        # Mock the map and marker objects
        mock_map_instance = Mock()
        mock_map.return_value = mock_map_instance
        
        mock_marker_instance = Mock()
        mock_marker.return_value = mock_marker_instance
        
        # Test map creation with some valid and some invalid addresses
        addresses = [
            "Times Square, New York, NY",
            "Central Park, New York, NY",
            "Invalid Address"
        ]
        
        result = create_static_map(addresses)

        # Verify geocoding was called for each address
        self.assertEqual(mock_geocode.call_count, 3)
        
        # Verify map was created with the average of valid coordinates
        map_call_args = mock_map.call_args[1]
        self.assertAlmostEqual(map_call_args['location'][0], 40.7696)  # Average lat
        self.assertAlmostEqual(map_call_args['location'][1], -73.976)  # Average lng
        
        # Verify markers were added for valid addresses
        self.assertEqual(mock_marker.call_count, 2)

        print(result)


    def test_run(self):
        addresses = [
            "Golden Gate Bridge, San Francisco, CA",
            "Alcatraz Island, San Francisco, CA",
            "Fisherman's Wharf, San Francisco, CA"
        ]
        print(create_static_map(addresses))

if __name__ == '__main__':
    unittest.main()
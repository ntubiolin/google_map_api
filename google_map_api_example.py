import googlemaps
from pprint import pprint
from datetime import datetime

# 替換成你的 Google Maps API Key
API_KEY = "YOUR_API_KEY"
gmaps = googlemaps.Client(key=API_KEY)

def maps_geocode(address):
    """
    📍 Convert address to geographic coordinates.

    Args:
        address (str): Address to geocode (e.g., "Taipei 101").

    Returns:
        tuple: (location dict with lat/lng, formatted address, place ID)
    """
    print("\n📍 Geocoding address...")
    result = gmaps.geocode(address)
    if result:
        location = result[0]['geometry']['location']
        formatted_address = result[0]['formatted_address']
        place_id = result[0]['place_id']
        pprint({"location": location, "formatted_address": formatted_address, "place_id": place_id})
        return location, formatted_address, place_id

def maps_reverse_geocode(lat, lng):
    """
    📍 Convert geographic coordinates to a human-readable address.

    Args:
        lat (float): Latitude
        lng (float): Longitude

    Returns:
        tuple: (formatted address, place ID, address components)
    """
    print("\n📍 Reverse geocoding coordinates...")
    result = gmaps.reverse_geocode((lat, lng))
    if result:
        formatted_address = result[0]['formatted_address']
        place_id = result[0]['place_id']
        address_components = result[0]['address_components']
        pprint({"formatted_address": formatted_address, "place_id": place_id, "components": address_components})
        return formatted_address, place_id, address_components

def maps_search_places(query, location=None, radius=None):
    """
    🔍 Search for places using a text query, optionally near a location.

    Args:
        query (str): Search keyword (e.g., "coffee").
        location (tuple, optional): (latitude, longitude)
        radius (int, optional): Radius in meters (max 50000)

    Returns:
        list: Places found (name, address, location)
    """
    print("\n🔍 Searching places...")
    result = gmaps.places(query=query, location=location, radius=radius)
    places = []
    for place in result.get("results", []):
        places.append({
            "name": place.get("name"),
            "address": place.get("formatted_address", place.get("vicinity")),
            "location": place.get("geometry", {}).get("location")
        })
    pprint(places)
    return places

def maps_place_details(place_id):
    """
    📄 Retrieve detailed information for a specific place by its ID.

    Args:
        place_id (str): The place ID from a search or geocode result.

    Returns:
        dict: Includes name, address, contact info, rating, and opening hours.
    """
    print("\n📄 Getting place details...")
    result = gmaps.place(place_id=place_id)
    details = result.get("result", {})
    data = {
        "name": details.get("name"),
        "address": details.get("formatted_address"),
        "contact_info": {
            "phone": details.get("formatted_phone_number"),
            "website": details.get("website")
        },
        "rating": details.get("rating"),
        "opening_hours": details.get("opening_hours", {}).get("weekday_text")
    }
    pprint(data)
    return data

def maps_distance_matrix(origins, destinations, mode="driving"):
    """
    📏 Compute distances and durations between multiple origin-destination pairs.

    Args:
        origins (list): List of addresses or coordinates (strings)
        destinations (list): List of destination addresses
        mode (str): Travel mode - driving, walking, bicycling, transit

    Returns:
        list: Distance matrix rows containing durations and distances.
    """
    print("\n📏 Calculating distance matrix...")
    result = gmaps.distance_matrix(origins, destinations, mode=mode)
    pprint(result)
    return result['rows']

def maps_elevation(locations):
    """
    ⛰️ Get elevation data for a list of coordinates.

    Args:
        locations (list): List of dicts with lat/lng pairs

    Returns:
        list: Each element includes elevation, location, and resolution
    """
    print("\n⛰️ Getting elevation data...")
    result = gmaps.elevation(locations)
    pprint(result)
    return result

def maps_directions(origin, destination, mode="driving"):
    """
    🗺️ Get step-by-step directions between two locations.

    Args:
        origin (str): Start address or place
        destination (str): End address or place
        mode (str): Travel mode - driving, walking, bicycling, transit

    Returns:
        list: Directions result with route info and navigation steps
    """
    print("\n🗺️ Getting directions...")
    result = gmaps.directions(origin, destination, mode=mode, departure_time=datetime.now())
    if result:
        route = result[0]
        legs = route['legs'][0]
        steps = [step['html_instructions'] for step in legs['steps']]
        pprint({
            "distance": legs['distance']['text'],
            "duration": legs['duration']['text'],
            "steps": steps
        })
    return result

# ----------------------------
# 🚀 Sample Test
# ----------------------------

if __name__ == "__main__":
    address = "台北101"
    location, formatted_address, place_id = maps_geocode(address)

    lat, lng = location["lat"], location["lng"]
    maps_reverse_geocode(lat, lng)

    maps_search_places("咖啡", location=(lat, lng), radius=500)

    maps_place_details(place_id)

    maps_distance_matrix(["台北101"], ["台大醫院"], mode="walking")

    maps_elevation([{"lat": lat, "lng": lng}])

    maps_directions("台北101", "台北車站", mode="transit")

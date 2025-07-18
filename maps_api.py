import googlemaps
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))

def maps_geocode(address: str):
    """Convert address to geographic coordinates."""
    result = gmaps.geocode(address)
    if result:
        location = result[0]["geometry"]["location"]
        formatted_address = result[0]["formatted_address"]
        place_id = result[0]["place_id"]
        return {"location": location, "formatted_address": formatted_address, "place_id": place_id}

def maps_reverse_geocode(latitude: float, longitude: float):
    """Convert coordinates to a human-readable address."""
    result = gmaps.reverse_geocode((latitude, longitude))
    if result:
        r = result[0]
        return {
            "formatted_address": r["formatted_address"],
            "place_id": r["place_id"],
            "address_components": r["address_components"]
        }

def maps_search_places(query: str, latitude: float = None, longitude: float = None, radius: int = None):
    """Search for places using a text query."""
    location = (latitude, longitude) if latitude and longitude else None
    result = gmaps.places(query=query, location=location, radius=radius)
    places = []
    for p in result.get("results", []):
        places.append({
            "name": p.get("name"),
            "address": p.get("formatted_address", p.get("vicinity")),
            "location": p.get("geometry", {}).get("location")
        })
    return places

def maps_place_details(place_id: str):
    """Get detailed information about a place."""
    result = gmaps.place(place_id=place_id)
    r = result.get("result", {})
    return {
        "name": r.get("name"),
        "address": r.get("formatted_address"),
        "contact_info": {
            "phone": r.get("formatted_phone_number"),
            "website": r.get("website")
        },
        "rating": r.get("rating"),
        "opening_hours": r.get("opening_hours", {}).get("weekday_text")
    }

def maps_distance_matrix(origins: list, destinations: list, mode: str = "driving"):
    """Calculate distance and duration between origin-destination pairs."""
    result = gmaps.distance_matrix(origins, destinations, mode=mode)
    return result.get("rows", [])

def maps_elevation(locations: list):
    """Get elevation data for one or more locations."""
    return gmaps.elevation(locations)

def maps_directions(origin: str, destination: str, mode: str = "driving"):
    """Get step-by-step directions between two locations."""
    result = gmaps.directions(origin, destination, mode=mode, departure_time=datetime.now())
    if result:
        legs = result[0]["legs"][0]
        return {
            "distance": legs["distance"]["text"],
            "duration": legs["duration"]["text"],
            "steps": [step["html_instructions"] for step in legs["steps"]]
        }

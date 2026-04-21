from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

geolocator = Nominatim(user_agent="osnit_shield")


def geocode_location(location_name: str):
    try:
        location = geolocator.geocode(location_name, timeout=5)
        if location:
            return location.latitude, location.longitude
    except GeocoderTimedOut:
        return None, None

    return None, None

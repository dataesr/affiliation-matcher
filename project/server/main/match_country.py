from opencage.geocoder import OpenCageGeocode

from project.server.main.config import config


def get_address_from_query(query) -> dict:
    geocoder = OpenCageGeocode(config['OPENCAGE_API_KEY'])
    results = geocoder.geocode(query)
    return results[0]

from geopy.geocoders import Nominatim
from matcher.server.main.logger import get_logger

geolocator = Nominatim(user_agent='another_user_agent')
logger = get_logger(__name__)


def retrieve_country(query) -> str:
    geocode = geolocator.geocode(query)
    if geocode is None:
        split_query = query.split(',', 1)
        if len(split_query) > 1:
            country = retrieve_country(split_query[1])
        else:
            country = None
    else:
        lat = geocode.raw.get('lat', None)
        lon = geocode.raw.get('lon', None)
        location = geolocator.reverse('{}, {}'.format(lat, lon))
        country = location.raw.get('address', None).get('country_code', None)
    return country


def get_country_from_query(query) -> str:
    country = retrieve_country(query)
    if country is None:
        logger.error('No country found for {}'.format(query))
    return country

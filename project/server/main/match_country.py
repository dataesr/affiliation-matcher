import logging

from geopy.geocoders import Nominatim

logging.basicConfig(filename='matcher.log', level=logging.DEBUG,
                    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s')
geolocator = Nominatim(user_agent='another_user_agent')


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
        logging.error('No country found for {}'.format(query))
    return country

import logging

from geopy.geocoders import Nominatim


def get_address_from_query(query) -> dict:
    logging.basicConfig(filename='matcher.log', level=logging.DEBUG,
                        format='%(asctime)s | %(name)s | %(levelname)s | %(message)s')
    geolocator = Nominatim(user_agent="another_user_agent")
    geocode = geolocator.geocode(query)
    if geocode is None:
        logging.error('No country found for {}'.format(query))
        country = None
    else:
        lat = geocode.raw.get('lat', None)
        lon = geocode.raw.get('lon', None)
        location = geolocator.reverse('{}, {}'.format(lat, lon))
        country = location.raw.get('address', None).get('country_code', None)
    return {'match': country}

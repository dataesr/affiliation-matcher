import logging

from opencage.geocoder import OpenCageGeocode

from project.server.main.config import config


def get_address_from_query(query) -> dict:
    logging.basicConfig(filename='matcher.log', level=logging.DEBUG,
                        format='%(asctime)s | %(name)s | %(levelname)s | %(message)s')
    geocoder = OpenCageGeocode(config['OPENCAGE_API_KEY'])
    results = geocoder.geocode(query)
    if len(results) == 0:
        logging.error('No country found for {}'.format(query))
        country = None
    else:
        country = results[0].get('components', None).get('ISO_3166-1_alpha-2', None)
    return {'match': country}

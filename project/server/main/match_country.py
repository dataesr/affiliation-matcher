from opencage.geocoder import OpenCageGeocode

from project.server.main.config import config


def get_address_from_query(query) -> dict:
    geocoder = OpenCageGeocode(config['OPENCAGE_API_KEY'])
    results = geocoder.geocode(query)
    logs = 'We found {} result(s):'.format(len(results))
    logs += '<br>'
    logs += results[0].get('components', None).get('ISO_3166-1_alpha-3', None)
    return {'match': results, 'logs': logs}

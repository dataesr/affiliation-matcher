import json
import os

from elasticsearch import Elasticsearch, helpers
from matcher.server.main.config import config

ES_INDEX = 'country'
FILE_COUNTRY_KEYWORDS = 'country_keywords.json'
FILE_COUNTRY_FORBIDDEN = 'country_forbidden.json'


# TODO: Add logger
def generate_data(file_name: str = None, index: str = '', category: str = None) -> dict:
    dirname = os.path.dirname(__file__)
    with open(os.path.join(dirname, file_name), 'r') as file:
        country_keywords = json.load(file)
        for country in country_keywords.keys():
            for keyword in country_keywords[country]:
                yield {
                    '_index': index,
                    'category': category,
                    'regex': keyword,
                    'lang': 'fr',
                    'country': country.lower()
                }


def init_country() -> None:
    es = Elasticsearch(config['ELASTICSEARCH_HOST'])
    es.indices.create(index=ES_INDEX, ignore=400)
    es.delete_by_query(index=ES_INDEX, body={'query': {'match_all': {}}})
    # TODO: use helpers.parallel_bulk
    count, errors = helpers.bulk(es, generate_data(FILE_COUNTRY_KEYWORDS, ES_INDEX, 'keyword'))
    print(str(count) + ' added to ES as keyword')
    if len(errors) > 0:
        print(errors)
    count, errors = helpers.bulk(es, generate_data(FILE_COUNTRY_FORBIDDEN, ES_INDEX, 'forbidden'))
    print(str(count) + ' added to ES as forbidden')
    if len(errors) > 0:
        print(errors)


if __name__ == '__main__':
    init_country()

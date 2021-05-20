from matcher.server.main.my_elastic import MyElastic
from matcher.server.main.utils import get_common_words, download_data_from_grid

ES_INDEX = 'index-grid'

es = MyElastic()


def init_grid() -> None:
    grid = get_data_from_grid()
    main_cities = [c for c in get_common_words(grid, 'cities', split=True, threshold=0) if len(c) > 2]
    main_countries = [c for c in get_common_words(grid, 'country', split=True, threshold=0) if len(c) > 1]
    main_country_code = [c for c in get_common_words(grid, 'country_code', split=True, threshold=0) if len(c) > 1]
    main_acronyms = get_common_words(grid, 'acronyms', split=True, threshold=5)
    main_names = list(set(get_common_words(grid, 'names', threshold=50)) - set(main_cities))
    filters = get_filters(main_cities, main_names, main_acronyms, main_countries, main_country_code)
    char_filters = get_char_filters()
    tokenizers = get_tokenizers()
    analyzers = get_analyzers()
    reset_index_grid(filters, char_filters, tokenizers, analyzers)
    actions = [{'_index': ES_INDEX, '_source': j} for j in grid]
    es.parallel_bulk(actions=actions)


def get_filters(main_cities, main_names, main_acronyms, main_countries, main_country_code) -> dict:
    return {
        'french_stop': {
            'type': 'stop',
            'stopwords': '_french_'
        }, 'english_stop': {
            'type': 'stop',
            'stopwords': '_english_'
        }, 'extract_digits': {
            'type': 'keep_types',
            'types': ['<NUM>']
        }, 'length_min_2_char': {
            'type': 'length',
            'min': 2
        }, 'length_min_3_char': {
            'type': 'length',
            'min': 3
        }, 'length_min_4_char': {
            'type': 'length',
            'min': 4
        }, 'length_min_5_char': {
            'type': 'length',
            'min': 5
        }, 'length_2_5_char': {
            'type': 'length',
            'min': 2,
            'max': 5
        }, 'french_elision': {
            'type': 'elision',
            'articles_case': True,
            'articles': ['l', 'm', 't', 'qu', 'n', 's', 'j', 'd', 'c', 'jusqu', 'quoiqu', 'lorsqu', 'puisqu']
        }, 'french_stemmer': {
            'type': 'stemmer',
            'language': 'light_french'
        }, 'english_stemmer': {
            'type': 'stemmer',
            'language': 'light_english'
        }, 'underscore_remove': {
            'type': 'pattern_replace',
            'pattern': '(-|_)',
            'replacement': ' '
        }, 'city_remover': {
            'type': 'stop',
            'ignore_case': True,
            'stopwords': main_cities
        }, 'custom_filter_name': {
            'type': 'stop',
            'ignore_case': True,
            'stopwords': []
        }, 'keep_cities': {
            'type': 'keep',
            'keep_words': main_cities
        }, 'keep_countries': {
            'type': 'keep',
            'keep_words': main_countries
        }, 'keep_country_code': {
            'type': 'keep',
            'keep_words': main_country_code
        }, 'common_acronyms_filter': {
            'type': 'stop',
            'ignore_case': True,
            'stopwords': main_acronyms
        }, 'common_names_filter': {
            'type': 'stop',
            'ignore_case': True,
            'stopwords': main_names
        }, 'city_synonym': {
            'type': 'synonym_graph',
            'synonyms': [
                'pierre benite, lyon',
                'pierre bénite, lyon'
            ]
        }, 'name_synonym': {
            'type': 'synonym_graph',
            'synonyms': [
                'modelling, modelisation',
                'antimicrobials, antimicrobien'
            ]
        }, 'remove_space': {
            'type': 'pattern_replace',
            'pattern': ' ',
            'replacement': ''
        }
    }


def get_char_filters() -> dict:
    return {
        'keep_digits_only': {
            'type': 'pattern_replace',
            'pattern': '\D+',
            'replacement': ' '
        }, 'remove_digits': {
            'type': 'pattern_replace',
            'pattern': '[0-9]',
            'replacement': ' '
        }, 'remove_space': {
            'type': 'pattern_replace',
            'pattern': ' |_',
            'replacement': ''
        }
    }


def get_tokenizers() -> dict:
    return {
        'tokenizer_ngram_3_8': {
            'type': 'ngram',
            'min_gram': 3,
            'max_gram': 8,
            'token_chars': [
                'letter',
                'digit'
            ]
        }
    }


def get_analyzers() -> dict:
    return {
        'light': {
            'tokenizer': 'icu_tokenizer',
            'filter': [
                'icu_folding'
            ]
        }, 'heavy': {
            'tokenizer': 'icu_tokenizer',
            'filter': [
                'length_min_2_char',
                'icu_folding',
                'english_stop',
                'english_stemmer'
            ]
        }, 'analyzer_city': {
            'tokenizer': 'icu_tokenizer',
            'filter': [
                'length_min_2_char',
                'lowercase',
                'icu_folding',
                'keep_cities',
                'city_synonym'
            ]
        }, 'analyzer_country': {
            'tokenizer': 'icu_tokenizer',
            'filter': [
                'icu_folding',
                'length_min_2_char',
                'lowercase',
                'keep_countries'
            ]
        }, 'analyzer_country_code': {
            'tokenizer': 'icu_tokenizer',
            'filter': [
                'icu_folding',
                'lowercase',
                'keep_country_code'
            ]
        }, 'analyzer_acronym': {
            'tokenizer': 'icu_tokenizer',
            'filter': [
                'length_min_3_char',
                'lowercase',
                'city_remover',
                'icu_folding',
                'english_stemmer'
            ]
        }, 'analyzer_name': {
            'tokenizer': 'icu_tokenizer',
            'filter': [
                'icu_folding',
                'english_stop',
                'length_min_5_char',
                'lowercase',
                'city_remover',
                'name_synonym',
                'custom_filter_name'
            ]
        }
    }


def reset_index_grid(filters, char_filters, tokenizers, analyzers):
    es.delete_index(index=ES_INDEX)
    settings = {
        'index': {
            'max_ngram_diff': 8
        },
        'analysis': {
            'char_filter': char_filters,
            'filter': filters,
            'analyzer': analyzers,
            'tokenizer': tokenizers
        }
    }
    mappings = {
        'properties': {
            'names': {
                'type': 'text',
                'boost': 5,
                'analyzer': 'analyzer_name'
            },
            'acronyms': {
                'type': 'text',
                'boost': 5,
                'analyzer': 'analyzer_acronym'
            },
            'cities': {
                'type': 'text',
                'boost': 2,
                'analyzer': 'analyzer_city'
            },
            'country': {
                'type': 'text',
                'boost': 2,
                'analyzer': 'analyzer_country'
            },
            'country_code': {
                'type': 'text',
                'boost': 2,
                'analyzer': 'analyzer_country_code'
            },
        }
    }
    return es.create_index(index=ES_INDEX, mappings=mappings, settings=settings)


def get_data_from_grid() -> list:
    data = []
    grids = download_data_from_grid()
    for grid in grids['institutes']:
        if grid.get('status') != 'active':
            continue
        datum = {'id': grid.get('id')}
        # NAMES
        names = [grid.get('name')] + grid.get('aliases', [])
        names += [label.get('label') for label in grid.get('labels', [])]
        datum['names'] = names
        # ACRONYMS
        datum['acronyms'] = grid.get('acronyms', [])
        # CITIES
        cities = []
        addresses = grid.get('addresses', [])
        for address in addresses:
            if 'city' in address and address.get('city'):
                cities.append(address.get('city'))
            if 'geonames_city' in address and address.get('geonames_city'):
                if 'city' in address.get('geonames_city') and address.get('geonames_city').get('city'):
                    cities.append(address.get('geonames_city').get('city'))
                if 'geonames_admin1' in address.get('geonames_city') and \
                        address.get('geonames_city').get('geonames_admin1'):
                    if 'name' in address.get('geonames_city').get('geonames_admin1') and \
                            address.get('geonames_city').get('geonames_admin1').get('name'):
                        cities.append(address.get('geonames_city').get('geonames_admin1').get('name'))
                if 'nuts_level2' in address.get('geonames_city') and address.get('geonames_city').get('nuts_level2'):
                    if 'name' in address.get('geonames_city').get('nuts_level2') and \
                            address.get('geonames_city').get('nuts_level2').get('name'):
                        cities.append(address.get('geonames_city').get('nuts_level2').get('name'))
                if 'nuts_level3' in address.get('geonames_city') and address.get('geonames_city').get('nuts_level3'):
                    if 'name' in address.get('geonames_city').get('nuts_level3') and \
                            address.get('geonames_city').get('nuts_level3').get('name'):
                        cities.append(address.get('geonames_city').get('nuts_level3').get('name'))
        datum['cities'] = list(set(cities))
        datum['country'] = [address.get('country') for address in addresses if 'country' in address]
        datum['country_code'] = [address.get('country_code') for address in addresses if 'country_code' in address]
        data.append(datum)
    return data


if __name__ == '__main__':
    init_grid()

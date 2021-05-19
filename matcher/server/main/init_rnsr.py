import os
import requests

from matcher.server.main.config import config
from matcher.server.main.my_elastic import MyElastic
from matcher.server.main.strings import normalize_text
from matcher.server.main.utils import has_a_digit

es = MyElastic()


def init_rnsr() -> None:
    rnsr = get_es_rnsr()
    main_cities = [c for c in get_common_words(rnsr, 'cities', split=True, threshold=0) if len(c) > 2]
    main_cities += ['alpes', 'quentin', 'yvelines', 'aquitaine']
    main_cities_for_removal = main_cities.copy()
    for w in ['france', 'francois', 'jacob', 'michel', 'marcel',
              'maisons', 'paul', 'martin', 'laurent', 'yvette', 'plage', 'roche',
              'jean', 'ville', 'bois', 'maurice', 'antoine', 'pierre', 'germain',
              'hopital', 'etoile', 'riviere', 'flots', 'cloud', 'anne', 'claude', 'esprit']:
        if w in main_cities:
            main_cities_for_removal.remove(w)
    main_acronyms = get_common_words(rnsr, 'acronyms', split=True, threshold=5) + ['brgm']
    main_names = list(set(get_common_words(rnsr, 'names', threshold=50)) - set(main_cities))
    main_supervisors_name = list(
        set(get_common_words(rnsr, 'supervisors_name', split=True, threshold=5)) - set(main_acronyms))
    main_supervisors_acronym = list(
        set(get_common_words(rnsr, 'supervisors_acronym', split=True, threshold=1)) - set(main_acronyms))
    labels_in_code = [k for k in get_common_words(rnsr, 'code_numbers', split=True, threshold=1) if
                      not (has_a_digit(k))]
    stop_code = ['insa', 'inserm', 'pasteur', 'de', 'cnrs', 'team', 'inra', 'inria', 'inrae', 'cea', 'siege', 'tech',
                 'idf', 'ouest']
    filters = get_filters(stop_code, main_cities, main_cities_for_removal, main_supervisors_name,
                          main_supervisors_acronym,
                          main_names, main_acronyms, labels_in_code)
    char_filters = get_char_filters()
    tokenizers = get_tokenizers()
    analyzers = get_analyzers()
    actions = []
    for year in rnsr:
        reset_index_rnsr(year, filters, char_filters, tokenizers, analyzers)
        index = 'index-rnsr-{year}'.format(year=year)
        actions += [{'_index': index, '_source': j} for j in rnsr[year]]
    es.parallel_bulk(actions=actions)


def get_filters(stop_code, main_cities, main_cities_for_removal, main_supervisors_name, main_supervisors_acronym,
                main_names, main_acronyms, labels_in_code) -> dict:
    return {
        'french_stop': {
            'type': 'stop',
            'stopwords': '_french_'
        },
        'english_stop': {
            'type': 'stop',
            'stopwords': '_english_'
        },
        'extract_digits': {
            'type': 'keep_types',
            'types': ['<NUM>']
        },
        'length_min_2_char': {
            'type': 'length',
            'min': 2
        },
        'length_min_3_char': {
            'type': 'length',
            'min': 3
        },
        'length_min_4_char': {
            'type': 'length',
            'min': 4
        },
        'length_min_5_char': {
            'type': 'length',
            'min': 5
        },
        'length_2_5_char': {
            'type': 'length',
            'min': 2,
            'max': 5
        },
        'french_elision': {
            'type': 'elision',
            'articles_case': True,
            'articles': ['l', 'm', 't', 'qu', 'n', 's', 'j', 'd', 'c', 'jusqu', 'quoiqu', 'lorsqu', 'puisqu']
        },
        'french_stemmer': {
            'type': 'stemmer',
            'language': 'light_french'
        },
        'english_stemmer': {
            'type': 'stemmer',
            'language': 'light_english'
        },
        'underscore_remove': {
            'type': 'pattern_replace',
            'pattern': '(-|_)',
            'replacement': ' '
        },
        'city_remover': {
            'type': 'stop',
            'ignore_case': True,
            'stopwords': main_cities_for_removal
        },
        'code_filter': {
            'type': 'stop',
            'ignore_case': True,
            'stopwords': stop_code
        },
        'custom_filter_acronym': {
            'type': 'stop',
            'ignore_case': True,
            'stopwords': ['cedex', 'medecine', 'ums', 'umr', 'pole', 'umi', 'care', 'métiers', 'ur', 'ea', 'dmu']
        },
        'custom_filter_supervisor': {
            'type': 'stop',
            'ignore_case': True,
            'stopwords': ['institut', 'institute', 'universite', 'university', 'centre', 'pole', 'national']
        },
        'custom_filter_code': {
            'type': 'stop',
            'ignore_case': True,
            'stopwords': ['cnrs', 'pasteur', 'inserm', 'insa']
        },
        'custom_filter_name': {
            'type': 'stop',
            'ignore_case': True,
            'stopwords': ['france']
        },
        'etab_stop': {
            'type': 'stop',
            'ignore_case': True,
            'stopwords': ['universite', 'hospice', 'hospices', 'hopital', 'hospital',
                          'hospitalo', 'universitaire', 'chu', 'centre', 'hospitalier',
                          'inserm', 'cnrs', 'inria', 'inrae', 'insa', 'pasteur',
                          'service', 'APHP', 'APHM', 'AP', 'HP', 'HM']
        },
        'keep_code_labels': {
            'type': 'keep',
            'keep_words': labels_in_code
        },
        'keep_cities': {
            'type': 'keep',
            'keep_words': main_cities
        },
        'common_acronyms_filter': {
            'type': 'stop',
            'ignore_case': True,
            'stopwords': main_acronyms
        },
        'supervisors_filter': {
            'type': 'stop',
            'ignore_case': True,
            'stopwords': main_supervisors_name + main_supervisors_acronym
        },
        'common_names_filter': {
            'type': 'stop',
            'ignore_case': True,
            'stopwords': main_names
        },
        'city_synonym': {
            'type': 'synonym_graph',
            'synonyms': ['pierre benite, lyon', 'pierre bénite, lyon']
        },
        'name_synonym': {
            'type': 'synonym_graph',
            'synonyms': ['modelling, modelisation', 'antimicrobials, antimicrobien']
        },
        'remove_space': {
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
        },
        'remove_digits': {
            'type': 'pattern_replace',
            'pattern': '[0-9]',
            'replacement': ' '
        },
        'remove_space': {
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
        },
        'code_tokenizer': {
            'type': 'pattern',
            'pattern': '_|\W+'
        },
        'code_tokenizer_lucky': {
            'type': 'simple_pattern',
            'pattern': '(UMR|U|FR|EA|UPR|UR|CIC|GDR)(.{0,4})([0-9]{2,4})'
        }
    }


def get_analyzers() -> dict:
    return {
        'analyzer_digits': {
            'tokenizer': 'standard',
            'char_filter': ['keep_digits_only'],
            'filter': ['length_2_5_char']
        },
        'analyzer_code_labels': {
            'tokenizer': 'code_tokenizer',
            'char_filter': ['remove_digits'],
            'filter': ['lowercase',
                       'icu_folding',
                       'custom_filter_code',
                       'keep_code_labels'
                       ]
        },
        'analyzer_code': {
            'tokenizer': 'code_tokenizer_lucky',
            'filter': ['lowercase', 'custom_filter_code']
        },
        'light': {
            'tokenizer': 'icu_tokenizer',
            'filter': [
                'french_elision',
                'icu_folding'
            ]
        },
        'heavy': {
            'tokenizer': 'icu_tokenizer',
            'filter': [
                'french_elision',
                'length_min_2_char',
                'icu_folding',
                'french_stop',
                'english_stop',
                'french_stemmer'
            ]
        },
        'analyzer_address': {
            'tokenizer': 'icu_tokenizer',
            'filter': [
                'french_elision',
                'length_min_2_char',
                'lowercase',
                'icu_folding',
                'french_stop',
                'keep_cities',
                'city_synonym'
            ]
        },
        'analyzer_acronym': {
            'tokenizer': 'icu_tokenizer',
            'filter': [
                'length_min_3_char',
                'lowercase',
                'city_remover',
                'supervisors_filter',
                'etab_stop',
                'custom_filter_acronym',
                'icu_folding',
                'french_stemmer'
            ]
        },
        'analyzer_name': {
            'tokenizer': 'icu_tokenizer',
            'filter': [
                'french_elision',
                'icu_folding',
                'french_stop',
                'english_stop',
                'length_min_5_char',
                'lowercase',
                'city_remover',
                'etab_stop',
                'name_synonym',
                'custom_filter_name'
            ]
        },
        'analyzer_supervisor': {
            'tokenizer': 'icu_tokenizer',
            'filter': [
                'icu_folding',
                'length_min_2_char',
                'lowercase',
                'french_stop',
                'english_stop',
                'custom_filter_supervisor'
            ]
        },
        'analyzer_supervisor_acronym': {
            'tokenizer': 'icu_tokenizer',
            'filter': [
                'icu_folding',
                'length_min_2_char',
                'lowercase',
                'french_stop',
                'english_stop',
                'city_remover',
                'custom_filter_supervisor'
            ]
        }
    }


def reset_index_rnsr(year, filters, char_filters, tokenizers, analyzers) -> None:
    index = 'index-rnsr-{}'.format(year)
    es.delete_index(index=index)
    settings = {
        'index': {
            'max_ngram_diff': 8
        },
        'analysis': {
            'analyzer': analyzers,
            'char_filter': char_filters,
            'filter': filters,
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
            'code_numbers': {
                'type': 'text',
                'analyzer': 'analyzer_code',

                'fields': {
                    'digits': {
                        'type': 'text',
                        'analyzer': 'analyzer_digits'
                    },
                    'labels': {
                        'type': 'text',
                        'analyzer': 'analyzer_code_labels'
                    }
                }
            },
            'supervisors_id': {
                'type': 'text'
            },
            'supervisors_name': {
                'type': 'text',
                'boost': 2,
                'analyzer': 'analyzer_supervisor'
            },
            'supervisors_acronym': {
                'type': 'text',
                'boost': 2,
                'analyzer': 'analyzer_supervisor_acronym'
            },
            'supervisors_city': {
                'type': 'text',
                'boost': 2,
                'analyzer': 'analyzer_address'
            },
            'addresses': {
                'type': 'text',
                'boost': 2,
                'analyzer': 'analyzer_address'
            }
        }
    }
    return es.create_index(index=index, mappings=mappings, settings=settings)


def get_common_words(rnsr, field, split=True, threshold=10) -> list:
    common = {}
    for elt in rnsr['all']:
        for c in elt.get(field, []):
            if split:
                v = normalize_text(c, remove_separator=False).split(' ')
            else:
                v = [normalize_text(c, remove_separator=False)]
            for w in v:
                if w not in common:
                    common[w] = 0
                common[w] += 1
    result = []
    for w in common:
        if common[w] > threshold:
            result.append(w)
    return result


def get_es_rnsr() -> dict:
    url = '{root_url}/organizations/?where={{"rnsr":{{"$exists":true}}}}&max_results={page_size}&projection={{' \
          '"active":1,"alias":1,"names":1,"id":1,"code_numbers":1,"supervisors":1,"addresses":1,"dates":1,' \
          '"sirene":1}}&page='.format(root_url=config['APP_ORGA'], page_size=500)
    es_rnsrs = {'all': [], 2011: [], 2012: [], 2013: [], 2014: [], 2015: [], 2016: [], 2017: [], 2018: [], 2019: [],
                2020: []}
    supervisors_acronyms = {}
    supervisors_cities = {}
    supervisors_names = {}
    page = 1
    while True:
        rnsrs = requests.get(url + str(page), headers=header).json().get('data', [])
        if len(rnsrs) == 0:
            break
        for rnsr in rnsrs:
            es_rnsr = {'id': rnsr['id']}
            # ACRONYMS & NAMES
            acronyms = []
            names = []
            for name in rnsr.get('names', []):
                acronyms.append(name.get('acronym_fr'))
                acronyms.append(name.get('acronym_en'))
                names.append(name.get('name_fr'))
                names.append(name.get('name_en'))
            es_rnsr['acronyms'] = list(filter(None, acronyms))
            es_rnsr['names'] = list(filter(None, names))
            # CODE_NUMBERS
            code_numbers = []
            for code in rnsr.get('code_numbers', []):
                code_numbers.extend([code, code.replace(' ', ''), code.replace(' ', '-'), code.replace(' ', '_')])
            es_rnsr['code_numbers'] = code_numbers
            # SUPERVISORS ID
            es_rnsr['supervisors_id'] = [supervisor.get('id') for supervisor in rnsr.get('supervisors', [])
                                         if 'id' in supervisor]
            if 'sirene' in rnsr:
                es_rnsr['supervisors_id'].append(rnsr['sirene'])
            # SUPERVISORS ACRONYM, NAME AND CITY
            es_rnsr['supervisors_acronym'] = []
            es_rnsr['supervisors_name'] = [k.get('name') for k in rnsr.get('supervisors', []) if 'name' in k]
            es_rnsr['supervisors_city'] = []
            for supervisor_id in es_rnsr['supervisors_id']:
                if supervisor_id not in supervisors_names:
                    supervisor = requests.get(config['APP_ORGA'] + '/organizations/' + supervisor_id,
                                              headers=header).json()
                    supervisors_acronyms[supervisor_id] = []
                    supervisors_names[supervisor_id] = []
                    for name in supervisor.get('names', []):
                        supervisors_acronyms[supervisor_id].append(name.get('acronym_fr'))
                        supervisors_acronyms[supervisor_id].append(name.get('acronym_en'))
                        supervisors_names[supervisor_id].append(name.get('name_fr'))
                        supervisors_names[supervisor_id].append(name.get('name_en'))
                    supervisors_names[supervisor_id] = filter(None, supervisors_names[supervisor_id])
                    supervisors_acronyms[supervisor_id] = filter(None, supervisors_acronyms[supervisor_id])
                    supervisors_cities[supervisor_id] = []
                    for address in supervisor.get('addresses', []):
                        supervisors_cities[supervisor_id].append(address.get('city'))
                    supervisors_cities[supervisor_id] = filter(None, supervisors_cities[supervisor_id])
                es_rnsr['supervisors_acronym'] += supervisors_acronyms[supervisor_id]
                es_rnsr['supervisors_name'] += supervisors_names[supervisor_id]
                es_rnsr['supervisors_city'] += supervisors_cities[supervisor_id]
                es_rnsr['supervisors_acronym'] = list(set(es_rnsr['supervisors_acronym']))
                es_rnsr['supervisors_name'] = list(set(es_rnsr['supervisors_name']))
                es_rnsr['supervisors_city'] = list(set(es_rnsr['supervisors_city']))
            # ADDRESSES
            es_rnsr['addresses'] = [k.get('input_address') for k in rnsr.get('addresses', []) if
                                    'input_address' in k]
            es_rnsr['cities'] = [k.get('city') for k in rnsr.get('addresses', []) if 'city' in k]
            if len(es_rnsr['addresses']) == 0:
                es_rnsr['addresses'] = es_rnsr['supervisors_city']
            # Create an es_rnsr by date
            for year in range(2011, 2021):
                for d in rnsr.get('dates', []):
                    if d.get('start_date')[0:4] <= str(year) and (d.get('end_date') is None or
                                                                  d.get('end_date')[0:4] >= str(year)):
                        es_rnsrs[year].append(es_rnsr)
            es_rnsrs['all'].append(es_rnsr)
        page += 1
    return es_rnsrs


if __name__ == '__main__':
    init_rnsr()

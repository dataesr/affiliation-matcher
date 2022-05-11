def get_mappings(analyzer) -> dict:
    return {
        'properties': {
            'content': {
                'type': 'text',
                'analyzer': analyzer
            },
            'ids': {
                'type': 'text',
                'analyzer': 'keyword'
            },
            'query': {
                'type': 'percolator'
            }
        }
    }


def get_filters() -> dict:
    return {
        'acronym_stop': {
            'type': 'stop',
            'ignore_case': True,
            'stopwords': ['pasteur', 'cedex', 'paris', 'ea', 'team', 'innovation', 'sphere', 'st', 'and', 'gu', 'care', 'medecine']
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
        'length_min_2_char': {
            'type': 'length',
            'min': 2
        },
        'length_min_3_char': {
            'type': 'length',
            'min': 3
        },
        'linked_words': {
            'type': 'common_grams',
            'common_words': ['saint', 'sainte'],
            'ignore_case': True,
            'query_mode': True
        },
        'common_synonym': {
            'type': 'synonym',
            'lenient': True,
            'synonyms': [
                'acad => academy',
                'cent => central',
                'ctr => center',
                'dev => development',
                'inst => institute',
                'lab => laboratory',
                'labs => laboratories',
                'med => medical',
                'newyork => new york',
                'ntl => national',
                'res => research',
                'st => saint',
                'trop => tropical',
                'univ => university',
                'universite => university',
                'universitaet => university',
                'universitat => university'
            ]
        },
        'name_synonym': {
            'type': 'synonym',
            'lenient': True,
            'synonyms': ["cic => centres d'investigation clinique"]
        }
    }


def get_char_filters() -> dict:
    return {
        'remove_char_btw_digits': {
            'type': 'pattern_replace',
            'pattern': r'(\\d+)\D(?=\\d)',
            'replacement': '$1'
        }
    }


def get_analyzers() -> dict:
    return {
        'light': {
            'tokenizer': 'icu_tokenizer',
            'filter': [
                'lowercase',
                'french_elision',
                'icu_folding'
            ]
        },
        'city_analyzer': {
            'tokenizer': 'icu_tokenizer',
            'filter': [
                'lowercase',
                'french_elision',
                'icu_folding',
                'common_synonym'
            ]
        },
        'acronym_analyzer': {
            'tokenizer': 'icu_tokenizer',
            'filter': [
                'lowercase',
                'french_elision',
                'icu_folding',
                'acronym_stop'
            ]
        },
        'name_analyzer': {
            'tokenizer': 'icu_tokenizer',
            'filter': [
                'lowercase',
                'french_elision',
                'icu_folding'
            ]
        },
        'code_analyzer': {
            'tokenizer': 'icu_tokenizer',
            'filter': [
                'lowercase',
                'french_elision',
                'icu_folding'
            ],
            'char_filter': [
                'remove_char_btw_digits'
            ]
        },
        'heavy_fr': {
            'tokenizer': 'icu_tokenizer',
            'filter': [
                'lowercase',
                'icu_folding',
                'common_synonym',
                'linked_words',
                'french_elision',
                'french_stemmer'
            ]
        },
        'heavy_en': {
            'tokenizer': 'icu_tokenizer',
            'filter': [
                'lowercase',
                'icu_folding',
                'common_synonym',
                'english_stemmer'
            ]
        }
    }


def get_index_name(index_name: str, source: str, index_prefix: str = '') -> str:
    names = list(filter(lambda x: x != '', [index_prefix, source, index_name]))
    return '_'.join(names)

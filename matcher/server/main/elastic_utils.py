def get_filters():
    return {
        'french_stop': {
            'type': 'stop',
            'stopwords': '_french_'
        },
        'english_stop': {
            'type': 'stop',
            'stopwords': '_english_'
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
        }
    }


def get_analyzers():
    return {
        'light': {
            'tokenizer': 'icu_tokenizer',
            'filter': [
                'lowercase',
                'french_elision',
                'icu_folding'
            ]
        },
        'heavy_fr': {
            'tokenizer': 'icu_tokenizer',
            'filter': [
                'lowercase',
                'icu_folding',
                'french_stop',
                'english_stop',
                'french_elision',
                'french_stemmer'
            ]
        },
        'heavy_en': {
            'tokenizer': 'icu_tokenizer',
            'filter': [
                'lowercase',
                'icu_folding',
                'english_stop',
                'english_stemmer'
            ]
        }
    }

import pickle

from elasticsearch import Elasticsearch
from elasticsearch import helpers

from project.server.main.utils import normalize_text

es = Elasticsearch(['localhost', 'elasticsearch'])
INDEX = 'index_finess'


def init_es_finess():
    finess = pickle.load(open("matcher/server/main/dict_finess.pkl", "rb"))

    docs_to_index = []
    for k in finess:
        new_elt = {"name": [], "city": [], "id": k}

        for elt in finess[k]:

            if elt.get('dataesr_city'):
                new_elt['city'].append(elt.get('dataesr_city'))
            if elt.get('Ligne d’acheminement (CodePostal+Lib commune) ligneacheminement'):
                new_elt['city'].append(elt.get('Ligne d’acheminement (CodePostal+Lib commune) ligneacheminement'))

            if elt.get('Raison sociale rs'):
                new_elt['name'].append(elt.get('Raison sociale rs'))
            if elt.get('Raison sociale longue rslongue'):
                new_elt['name'].append(elt.get('Raison sociale longue rslongue'))
            if elt.get('dataesr_name'):
                new_elt['name'].append(elt.get('dataesr_name'))

        docs_to_index.append(new_elt)

    known_cities = []
    for k in finess:
        for elt in finess[k]:
            if elt.get('dataesr_city'):
                known_cities.append(normalize_text(text=elt.get('dataesr_city'), remove_separator=False))
            if elt.get('Ligne d’acheminement (CodePostal+Lib commune) ligneacheminement'):
                known_cities.append(
                    normalize_text(text=elt.get('Ligne d’acheminement (CodePostal+Lib commune) ligneacheminement'),
                                   remove_separator=False))
    known_cities = list(set(known_cities) - set('france'))
    names_to_remove = ["france", "cedex", "institut"]

    filters = get_filters(known_cities, names_to_remove)
    char_filters = get_char_filters()
    tokenizers = get_tokenizers()
    analyzers = get_analyzers()
    res = {}

    reset_index_finess(filters, char_filters, tokenizers, analyzers)

    actions = [
        {
            "_index": INDEX,
            "_source": docs_to_index[j]
        }
        for j in range(0, len(docs_to_index))
    ]
    print(helpers.bulk(es, actions), flush=True)

    res[INDEX] = len(docs_to_index)
    res['ok'] = 1
    return res


def get_char_filters():
    char_filters = {"keep_digits_only": {
        "type": "pattern_replace",
        "pattern": r"\D+",
        "replacement": " "
    }, "remove_digits": {
        "type": "pattern_replace",
        "pattern": "[0-9]",
        "replacement": " "
    }, "remove_space": {
        "type": "pattern_replace",
        "pattern": " |_",
        "replacement": ""
    }, "curie": {
        "type": "pattern_replace",
        "pattern": "(pierre).*(marie).*(curie)",
        "replacement": ""
    }}
    return char_filters


def get_filters(main_cities, main_names):
    filters = {"keep_cities": {
        "type": "keep",
        "keep_words": main_cities
    }, "city_remover": {
        "type": "stop",
        "ignore_case": True,
        "stopwords": main_cities
    }, "common_names_filter": {
        "type": "stop",
        "ignore_case": True,
        "stopwords": main_names
    }, "french_stop": {
        "type": "stop",
        "stopwords": "_french_"
    }, "english_stop": {
        "type": "stop",
        "stopwords": "_english_"
    }, "extract_digits": {
        "type": "keep_types",
        "types": ["<NUM>"]
    }, "length_min_2_char": {
        "type": "length",
        "min": 2
    }, "length_min_3_char": {
        "type": "length",
        "min": 3
    }, "length_min_4_char": {
        "type": "length",
        "min": 4
    }, "length_min_5_char": {
        "type": "length",
        "min": 5
    }, "length_2_5_char": {
        "type": "length",
        "min": 2,
        "max": 5
    }, "french_elision": {
        "type": "elision",
        "articles_case": True,
        "articles": ["l", "m", "t", "qu", "n", "s", "j", "d", "c", "jusqu", "quoiqu", "lorsqu", "puisqu"]
    }, "french_stemmer": {
        "type": "stemmer",
        "language": "light_french"
    }, "english_stemmer": {
        "type": "stemmer",
        "language": "light_english"
    }, "underscore_remove": {
        "type": "pattern_replace",
        "pattern": "(-|_)",
        "replacement": " "
    }, "remove_space": {
        "type": "pattern_replace",
        "pattern": " ",
        "replacement": ""
    }, "name_synonym": {
        "type": "synonym_graph",
        "synonyms": [
            "ch ,centre hospitalier",
            "chu ,centre hospitalier universitaire"
        ]
    }}

    return filters


def get_tokenizers():
    tokenizers = {"tokenizer_ngram_3_8": {
        "type": "ngram",
        "min_gram": 3,
        "max_gram": 8,
        "token_chars": [
            "letter",
            "digit"
        ]
    }, 'code_tokenizer': {
        "type": "pattern",
        "pattern": r"_|\W+"
    }, "code_tokenizer_lucky": {
        "type": "simple_pattern",
        "pattern": "(UMR|U|FR|EA|UPR|UR|CIC|GDR)(.{0,4})([0-9]{2,4})"
    }}
    # tokenizers["code_tokenizer"]= {
    #          "type": "simple_pattern",
    #          "pattern": "([A-Za-z\-\_]{1,5})(.{0,1})([0-9]{1,5})"
    #        }

    return tokenizers


def get_analyzers():
    analyzers = {'analyzer_digits': {
        "tokenizer": "standard",
        "char_filter": ["keep_digits_only"],
        "filter": ["length_2_5_char"]
    }, "analyzer_city": {
        "tokenizer": "standard",
        "char_filter": ["remove_digits"],
        "filter": ["lowercase",
                   "icu_folding",
                   "keep_cities"
                   ]
    }, "analyzer_name": {
        "tokenizer": "icu_tokenizer",
        "char_filter": ["curie"],
        "filter": [
            "french_elision",
            "icu_folding",
            "french_stop",
            "english_stop",
            "lowercase",
            "city_remover",
            "common_names_filter",
            "name_synonym"
        ]
    }}

    return analyzers


def delete_index_finess():
    print("deleting " + INDEX, end=':', flush=True)
    del_docs = es.delete_by_query(index=INDEX, body={"query": {"match_all": {}}})
    print(del_docs, flush=True)
    del_index = es.indices.delete(index=INDEX, ignore=[400, 404])
    print(del_index, flush=True)
    return


def reset_index_finess(filters, char_filters, tokenizers, analyzers):
    try:
        delete_index_finess()
    except:
        pass

    setting_finess = {
        "index": {
            "max_ngram_diff": 8
        },
        "analysis": {
            "char_filter": char_filters,
            "filter": filters,
            "analyzer": analyzers,
            "tokenizer": tokenizers
        }
    }

    mapping_finess = {
        "properties": {
            "name": {
                "type": "text",
                "boost": 5,
                "analyzer": "analyzer_name"
            },
            "city": {
                "type": "text",
                "analyzer": "analyzer_name",

                "fields": {
                    "digits": {
                        "type": "text",
                        "analyzer": "analyzer_digits"
                    },
                    "city": {
                        "type": "text",
                        "analyzer": "analyzer_city"
                    }
                }
            }
        }
    }

    response = es.indices.create(
        index=INDEX,
        body={
            "settings": setting_finess,
            "mappings": mapping_finess

        },
        ignore=400  # ignore 400 already exists code
    )

    if 'acknowledged' in response:
        if response['acknowledged']:
            print("INDEX MAPPING SUCCESS FOR INDEX:", response['index'], flush=True)

    print(response, flush=True)

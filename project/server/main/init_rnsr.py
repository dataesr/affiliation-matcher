import math
import os
import requests
import string
import unicodedata

from elasticsearch import Elasticsearch
from elasticsearch import helpers

from project.server.main.config import config


header = {'Authorization': 'Basic {}'.format(os.getenv('DATAESR_HEADER'))}
print('header', flush=True)
print(header, flush=True)
es = Elasticsearch(config['ELASTICSEARCH_HOST'])


def strip_accents(w: str) -> str:
    """Normalize accents and stuff in string."""
    w2 = w.replace("’", " ")
    return "".join(
        c for c in unicodedata.normalize("NFD", w2)
        if unicodedata.category(c) != "Mn")


def delete_punctuation(w: str) -> str:
    """Delete all punctuation in a string."""
    return w.lower().translate(
        str.maketrans(string.punctuation, len(string.punctuation) * " "))


def normalize_text(text: str) -> str:
    """Normalize string. Delete punctuation and accents."""
    if isinstance(text, str):
        text = delete_punctuation(text)
        text = strip_accents(text)
        text = text.replace('\xa0', ' ')
        text = " ".join(text.split())
    return text or ""


def normalize(text):
    return normalize_text(text).lower().replace('-', ' ') \
        .replace('‐', ' ').replace('  ', ' ')


def normalize_for_count(text):
    return normalize_text(text)[0:6]


def init_es():
    rnsr = get_rnsr()

    main_cities = [c for c in get_common_words(rnsr, 'cities', split=True, threshold=0) if len(c) > 2]
    main_cities += ['alpes', 'quentin', "yvelines", "aquitaine"]
    main_cities_for_removal = main_cities.copy()
    for w in ['france', 'francois', 'jacob', 'michel', 'marcel',
              'maisons', 'paul', 'martin', 'laurent', 'yvette', 'plage', 'roche',
              'jean', 'ville', 'bois', 'maurice', 'antoine', 'pierre', 'germain',
              'hopital', 'etoile', 'riviere', 'flots', 'cloud', 'anne', 'claude', 'esprit']:
        if w in main_cities:
            main_cities_for_removal.remove(w)

    main_acronyms = get_common_words(rnsr, 'acronyms', split=True, threshold=5) + ['brgm']
    main_names = list(set(get_common_words(rnsr, 'names', 50)) - set(main_cities))

    main_supervisors_name = list(
        set(get_common_words(rnsr, 'supervisors_name', split=True, threshold=5)) - set(main_acronyms))
    main_supervisors_acronym = list(
        set(get_common_words(rnsr, 'supervisors_acronym', split=True, threshold=1)) - set(main_acronyms))

    labels_in_code = [k for k in get_common_words(rnsr, 'code_numbers', split=True, threshold=1) if
                      not (has_a_digit(k))]

    stop_code = ["insa", "inserm", "pasteur", "de", "cnrs", "team", "inra", "inria", "inrae", "cea", "siege", "tech",
                 "idf", "ouest"]
    filters = get_filters(stop_code, main_cities, main_cities_for_removal, main_supervisors_name,
                          main_supervisors_acronym,
                          main_names, main_acronyms, labels_in_code)
    char_filters = get_char_filters()
    tokenizers = get_tokenizers()
    analyzers = get_analyzers()
    res = {}
    for year in rnsr:
        reset_index_rnsr(year, filters, char_filters, tokenizers, analyzers)

        actions = [
            {
                "_index": "index-rnsr-{}".format(year),
                "_type": "_doc",
                "_id": j,
                "_source": rnsr[year][j]
            }
            for j in range(0, len(rnsr[year]))
        ]
        res["index-rnsr-{}".format(year)] = len(rnsr[year])
        print(helpers.bulk(es, actions), flush=True)
    res['ok'] = 1
    return res


def get_filters(stop_code, main_cities, main_cities_for_removal, main_supervisors_name, main_supervisors_acronym,
                main_names, main_acronyms, labels_in_code):
    filters = {}
    filters["french_stop"] = {
        "type": "stop",
        "stopwords": "_french_"
    }
    filters["english_stop"] = {
        "type": "stop",
        "stopwords": "_english_"
    }

    filters["extract_digits"] = {
        "type": "keep_types",
        "types": ["<NUM>"]
    }

    filters["length_min_2_char"] = {
        "type": "length",
        "min": 2
    }

    filters["length_min_3_char"] = {
        "type": "length",
        "min": 3
    }

    filters["length_min_4_char"] = {
        "type": "length",
        "min": 4
    }

    filters["length_min_5_char"] = {
        "type": "length",
        "min": 5
    }

    filters["length_2_5_char"] = {
        "type": "length",
        "min": 2,
        "max": 5
    }

    filters["french_elision"] = {
        "type": "elision",
        "articles_case": True,
        "articles": ["l", "m", "t", "qu", "n", "s", "j", "d", "c", "jusqu", "quoiqu", "lorsqu", "puisqu"]
    }

    filters["french_stemmer"] = {
        "type": "stemmer",
        "language": "light_french"
    }

    filters["english_stemmer"] = {
        "type": "stemmer",
        "language": "light_english"
    }

    filters["underscore_remove"] = {
        "type": "pattern_replace",
        "pattern": "(-|_)",
        "replacement": " "
    }

    filters["city_remover"] = {
        "type": "stop",
        "ignore_case": True,
        "stopwords": main_cities_for_removal
    }
    filters["code_filter"] = {
        "type": "stop",
        "ignore_case": True,
        "stopwords": stop_code
    }
    filters["custom_filter_acronym"] = {
        "type": "stop",
        "ignore_case": True,
        "stopwords": ['cedex', "medecine", "ums", "umr", "pole",
                      "umi", "care", "métiers", "ur", "ea", "dmu"]
    }

    filters["custom_filter_supervisor"] = {
        "type": "stop",
        "ignore_case": True,
        "stopwords": ['institut', 'institute', 'universite', 'university',
                      'centre', 'pole', 'national']
    }

    filters["custom_filter_code"] = {
        "type": "stop",
        "ignore_case": True,
        "stopwords": ['cnrs', 'pasteur', 'inserm', 'insa']
    }

    filters["custom_filter_name"] = {
        "type": "stop",
        "ignore_case": True,
        "stopwords": ['france']
    }

    filters["etab_stop"] = {
        "type": "stop",
        "ignore_case": True,
        "stopwords": ['universite', 'hospice', 'hospices', 'hopital', 'hospital',
                      'hospitalo', 'universitaire', 'chu', 'centre', 'hospitalier',
                      'inserm', 'cnrs', 'inria', 'inrae', 'insa', 'pasteur',
                      'service', "APHP", "APHM", "AP", "HP", "HM"]
    }

    filters["keep_code_labels"] = {
        "type": "keep",
        "keep_words": labels_in_code
    }

    filters["keep_cities"] = {
        "type": "keep",
        "keep_words": main_cities
    }

    filters["common_acronyms_filter"] = {
        "type": "stop",
        "ignore_case": True,
        "stopwords": main_acronyms
    }

    filters["supervisors_filter"] = {
        "type": "stop",
        "ignore_case": True,
        "stopwords": main_supervisors_name + main_supervisors_acronym
    }

    filters["common_names_filter"] = {
        "type": "stop",
        "ignore_case": True,
        "stopwords": main_names
    }

    filters["city_synonym"] = {
        "type": "synonym_graph",
        "synonyms": [
            "pierre benite, lyon",
            "pierre bénite, lyon"
        ]
    }

    filters["name_synonym"] = {
        "type": "synonym_graph",
        "synonyms": [
            "modelling, modelisation",
            "antimicrobials, antimicrobien"
        ]
    }
    filters["remove_space"] = {
        "type": "pattern_replace",
        "pattern": " ",
        "replacement": ""
    }
    return filters


def get_char_filters():
    char_filters = {}
    char_filters["keep_digits_only"] = {
        "type": "pattern_replace",
        "pattern": "\D+",
        "replacement": " "
    }
    char_filters["remove_digits"] = {
        "type": "pattern_replace",
        "pattern": "[0-9]",
        "replacement": " "
    }
    char_filters["remove_space"] = {
        "type": "pattern_replace",
        "pattern": " |_",
        "replacement": ""
    }
    return char_filters


def get_tokenizers():
    tokenizers = {}
    tokenizers["tokenizer_ngram_3_8"] = {
        "type": "ngram",
        "min_gram": 3,
        "max_gram": 8,
        "token_chars": [
            "letter",
            "digit"
        ]
    }
    # tokenizers["code_tokenizer"]= {
    #          "type": "simple_pattern",
    #          "pattern": "([A-Za-z\-\_]{1,5})(.{0,1})([0-9]{1,5})"
    #        }

    tokenizers['code_tokenizer'] = {
        "type": "pattern",
        "pattern": "_|\W+"
    }

    tokenizers["code_tokenizer_lucky"] = {
        "type": "simple_pattern",
        "pattern": "(UMR|U|FR|EA|UPR|UR|CIC|GDR)(.{0,4})([0-9]{2,4})"
    }
    return tokenizers


def get_analyzers():
    analyzers = {}
    analyzers['analyzer_digits'] = {
        "tokenizer": "standard",
        "char_filter": ["keep_digits_only"],
        "filter": ["length_2_5_char"]
    }
    analyzers["analyzer_code_labels"] = {
        "tokenizer": "code_tokenizer",
        "char_filter": ["remove_digits"],
        "filter": ["lowercase",
                   "icu_folding",
                   "custom_filter_code",
                   "keep_code_labels"
                   ]
    }
    analyzers["analyzer_code"] = {
        "tokenizer": "code_tokenizer_lucky",
        "char_filter": ["remove_space"],
        "filter": [
            "lowercase",
            "icu_folding"
        ]
    }

    analyzers["light"] = {
        "tokenizer": "icu_tokenizer",
        "filter": [
            "french_elision",
            "icu_folding"
        ]
    }

    analyzers["heavy"] = {
        "tokenizer": "icu_tokenizer",
        "filter": [
            "french_elision",
            "length_min_2_char",
            "icu_folding",
            "french_stop",
            "english_stop",
            #    "common_names_filter",
            "french_stemmer"
        ]
    }

    analyzers["analyzer_address"] = {
        "tokenizer": "icu_tokenizer",
        "filter": [
            "french_elision",
            "length_min_2_char",
            "lowercase",
            "icu_folding",
            "french_stop",
            "keep_cities",
            "city_synonym"
        ]
    }

    # analyzers["analyzer_address_test"] = {
    #          "tokenizer": "city_tokenizer",
    #          "filter": [
    #              "lowercase",
    #             "icu_folding"
    #          ]
    #        }

    analyzers["analyzer_code"] = {
        "tokenizer": "code_tokenizer_lucky",
        "filter": ["lowercase", "custom_filter_code"]
    }
    analyzers["analyzer_acronym"] = {
        "tokenizer": "icu_tokenizer",
        "filter": [
            "length_min_3_char",
            "lowercase",
            "city_remover",
            "supervisors_filter",
            "etab_stop",
            #    "common_acronyms_filter",
            "custom_filter_acronym",
            "icu_folding",
            "french_stemmer"
        ]
    }
    analyzers["analyzer_name"] = {
        "tokenizer": "icu_tokenizer",
        "filter": [
            "french_elision",
            "icu_folding",
            "french_stop",
            "english_stop",
            "length_min_5_char",
            "lowercase",
            "city_remover",
            "etab_stop",
            "name_synonym",
            "custom_filter_name"
            # "french_stemmer",
            #  "english_stemmer"
        ]
    }
    analyzers["analyzer_supervisor"] = {
        "tokenizer": "icu_tokenizer",
        "filter": [
            "icu_folding",
            "length_min_2_char",
            "lowercase",
            "french_stop",
            "english_stop",
            "custom_filter_supervisor"
            #  "city_remover",
            #  "common_acronyms_filter",
            #  "common_names_filter",
            #  "french_stemmer"
        ]
    }

    analyzers["analyzer_supervisor_acronym"] = {
        "tokenizer": "icu_tokenizer",
        "filter": [
            "icu_folding",
            "length_min_2_char",
            "lowercase",
            "french_stop",
            "english_stop",
            "city_remover",
            "custom_filter_supervisor"
            #  "common_acronyms_filter",
            #  "common_names_filter",
            #  "french_stemmer"
        ]
    }
    return analyzers


def delete_index_rnsr(year):
    myIndex = 'index-rnsr-{}'.format(year)
    print("deleting " + myIndex, end=':', flush=True)
    del_docs = es.delete_by_query(index=myIndex, body={"query": {"match_all": {}}})
    print(del_docs, flush=True)
    del_index = es.indices.delete(index=myIndex, ignore=[400, 404])
    print(del_index, flush=True)
    return


def reset_index_rnsr(year, filters, char_filters, tokenizers, analyzers):
    myIndex = 'index-rnsr-{}'.format(year)
    try:
        delete_index_rnsr(year)
    except:
        pass

    setting_rnsr = {
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

    mapping_rnsr = {
        "properties": {
            "names": {
                "type": "text",
                "boost": 5,
                "analyzer": "analyzer_name"
            },
            "acronyms": {
                "type": "text",
                "boost": 5,
                "analyzer": "analyzer_acronym"
            },
            "code_numbers": {
                "type": "text",
                "analyzer": "analyzer_code",

                "fields": {
                    "digits": {
                        "type": "text",
                        "analyzer": "analyzer_digits"
                    }
                    , "labels": {
                        "type": "text",
                        "analyzer": "analyzer_code_labels"
                    }
                }
            },
            "supervisors_id": {
                "type": "text"
            },
            "supervisors_name": {
                "type": "text",
                "boost": 2,
                "analyzer": "analyzer_supervisor"
            },
            "supervisors_acronym": {
                "type": "text",
                "boost": 2,
                "analyzer": "analyzer_supervisor_acronym"
            },
            "supervisors_city": {
                "type": "text",
                "boost": 2,
                "analyzer": "analyzer_address"
            },
            "addresses": {
                "type": "text",
                "boost": 2,
                "analyzer": "analyzer_address"
            }
        }
    }

    response = es.indices.create(
        index=myIndex,
        body={
            "settings": setting_rnsr,
            "mappings": mapping_rnsr

        },
        ignore=400  # ignore 400 already exists code
    )

    if 'acknowledged' in response:
        if response['acknowledged'] == True:
            print("INDEX MAPPING SUCCESS FOR INDEX:", response['index'], flush=True)

    print(response, flush=True)


def has_a_digit(x):
    for c in x:
        if c.isdigit():
            return True
    return False


def get_common_words(rnsr, field, split=True, threshold=10):
    common = {}
    for elt in rnsr['all']:
        for c in elt.get(field, []):
            if split:
                v = normalize(c).split(' ')
            else:
                v = [normalize(c)]
            for w in v:
                if w not in common:
                    common[w] = 0
                common[w] += 1
    result = []
    for w in common:
        if common[w] > threshold:
            result.append(w)
    return result


def get_rnsr():
    supervisors_names = {}
    supervisors_acronyms = {}
    supervisors_cities = {}

    url_dataesr = config['APP_ORGA'] + "/organizations/?where={\"rnsr\":{\"$exists\":true}}&max_results=500&projection={\"active\":1,\"alias\":1,\"names\":1,\"id\":1,\"code_numbers\":1,\"supervisors\":1,\"addresses\":1,\"dates\":1,\"sirene\":1}&page="
    r_page = requests.get(url_dataesr + str(1), headers=header)
    print(r_page.text, flush=True)
    nb_page = math.ceil(r_page.json()['meta']['total'] / 500)
    print("GET RNSR", flush=True)
    print(url_dataesr, flush=True)

    print(nb_page, flush=True)
    rnsr = {}
    for p in range(1, nb_page + 1):
        print(p, flush=True)
        data = requests.get(url_dataesr + str(p), headers=header).json()['data']
        for elt in data:

            new_elt = {}
            new_elt['id'] = elt['id']

            ################### NAMES
            names = []
            for n in elt.get('names', []):
                name = {}
                for f in ['name_fr', 'name_en']:
                    if f in n:
                        names.append(n[f])
            new_elt['names'] = names

            ################### ACRONYMS

            acronyms = []
            for n in elt.get('names', []):
                for f in ['acronym_fr', 'acronym_en']:
                    if f in n:
                        acronyms.append(n[f])
            new_elt['acronyms'] = acronyms

            ################### CODE_NUMBERS

            new_elt['code_numbers'] = []
            for code in elt.get('code_numbers', []):
                new_elt['code_numbers'].append(code)
                new_elt['code_numbers'].append(code.replace(' ', ''))
                new_elt['code_numbers'].append(code.replace(' ', '-'))
                new_elt['code_numbers'].append(code.replace(' ', '_'))

            ################### SUPERVISORS ID & NAME

            new_elt['supervisors_id'] = [k.get('id') for k in elt.get('supervisors', []) if 'id' in k]
            if 'sirene' in elt:
                new_elt['supervisors_id'].append(elt['sirene'])

            new_elt['supervisors_acronym'] = []
            new_elt['supervisors_name'] = [k.get('name') for k in elt.get('supervisors', []) if 'name' in k]
            new_elt['supervisors_city'] = []

            for supervisor_id in new_elt['supervisors_id']:
                if supervisor_id not in supervisors_names:
                    supervisors_names[supervisor_id] = []
                    supervisors_acronyms[supervisor_id] = []
                    supervisors_cities[supervisor_id] = []

                    supervisor_elt = requests.get(config['APP_ORGA'] + '/organizations/' + supervisor_id, headers=header).json()
                    for n in supervisor_elt.get('names', []):
                        for f in ['name_fr', 'name_en']:
                            if f in n:
                                supervisors_names[supervisor_id].append(n[f])

                        for f in ['acronym_fr', 'acronym_en']:
                            if f in n:
                                supervisors_acronyms[supervisor_id].append(n[f])

                    for ad in supervisor_elt.get('addresses', []):
                        if 'city' in ad:
                            supervisors_cities[supervisor_id].append(ad['city'])

                    supervisors_names[supervisor_id] = list(set(supervisors_names[supervisor_id]))
                    supervisors_acronyms[supervisor_id] = list(set(supervisors_acronyms[supervisor_id]))
                    supervisors_cities[supervisor_id] = list(set(supervisors_cities[supervisor_id]))

                new_elt['supervisors_acronym'] += supervisors_acronyms[supervisor_id]
                new_elt['supervisors_name'] += supervisors_acronyms[supervisor_id]
                new_elt['supervisors_city'] += supervisors_cities[supervisor_id]

                new_elt['supervisors_acronym'] = list(set(new_elt['supervisors_acronym']))
                new_elt['supervisors_name'] = list(set(new_elt['supervisors_name']))
                new_elt['supervisors_city'] = list(set(new_elt['supervisors_city']))

            ################### ADDRESSES

            new_elt['addresses'] = [k.get('input_address') for k in elt.get('addresses', []) if 'input_address' in k]
            new_elt['cities'] = [k.get('city') for k in elt.get('addresses', []) if 'city' in k]
            if len(new_elt['addresses']) == 0:
                new_elt['addresses'] = new_elt['supervisors_city']

            ################## INDEX in ES
            for current_year in range(2011, 2021):
                keep = False
                dates = elt.get('dates', [])
                for d in dates:
                    if d.get('start_date')[0:4] <= str(current_year):
                        if d.get('end_date') is None or d.get('end_date')[0:4] >= str(current_year):
                            keep = True
                            break
                if keep:
                    if current_year not in rnsr:
                        rnsr[current_year] = []
                    rnsr[current_year].append(new_elt)
            if 'all' not in rnsr:
                rnsr['all'] = []
            rnsr['all'].append(new_elt)
            # res = es.index(index="index-rnsr", body=new_elt)
    return rnsr

import os

import requests
import datetime
import math
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Q, Search
from elasticsearch import helpers
import string
import unicodedata
import zipfile, json


es = Elasticsearch(['localhost', 'elasticsearch'])

def strip_accents(w: str) -> str:
    """Normalize accents and stuff in string."""
    w2 = w.replace("’", " ")
    return "".join(
      c for c in unicodedata.normalize("NFD", w2)
      if unicodedata.category(c) != "Mn")


def delete_punct(w: str) -> str:
    """Delete all puctuation in a string."""
    return w.lower().translate(
          str.maketrans(string.punctuation, len(string.punctuation)*" "))

def normalize_text(text: str) -> str:
    """Normalize string. Delete puctuation and accents."""
    if isinstance(text, str):
        text = delete_punct(text)
        text = strip_accents(text)
        text = text.replace('\xa0', ' ')
        text = " ".join(text.split())
    return text or ""


def normalize(text):
    return normalize_text(text).lower().replace('-', ' ')\
              .replace('‐', ' ').replace('  ', ' ')

def normalize_for_count(x):
    return normalize_text(x)[0:6]

def init_grid_es():
    grid = get_grid()

    main_cities = [c for c in get_common_words(grid, 'cities',split=True, threshold=0) if len(c)>2]
    main_countries = [c for c in get_common_words(grid, 'country',split=True, threshold=0) if len(c)>1]
    main_country_code = [c for c in get_common_words(grid, 'country_code',split=True, threshold=0) if len(c)>1]

    main_acronyms = get_common_words(grid, 'acronyms',split=True, threshold=5)
    main_names = list(set(get_common_words(grid, 'names',50)) - set(main_cities))

    filters = get_filters(main_cities, main_names, main_acronyms, main_countries, main_country_code)
    char_filters = get_char_filters()
    tokenizers = get_tokenizers()
    analyzers = get_analyzers()
    res = {}
        
    reset_index_grid(filters, char_filters, tokenizers, analyzers)

    actions = [
    {
        "_index": "index-grid",
        "_type": "_doc",
        "_id": j,
        "_source": grid[j] 
    }
    for j in range(0, len(grid))
    ]
    res["index-grid"] = len(grid)
    print(helpers.bulk(es, actions), flush=True)
    res['ok'] = 1
    return res

def get_filters(main_cities, main_names, main_acronyms, main_countries, main_country_code):
    filters = {}
    filters["french_stop"] = {
              "type":       "stop",
              "stopwords":  "_french_" 
    }
    filters["english_stop"] = {
          "type":       "stop",
          "stopwords":  "_english_" 
        }

    filters["extract_digits"]={
      "type": "keep_types",
      "types": [ "<NUM>" ]
    }

    filters["length_min_2_char"]= {
          "type": "length",
          "min": 2
        }

    filters["length_min_3_char"]= {
          "type": "length",
          "min": 3
        }

    filters["length_min_4_char"]= {
          "type": "length",
          "min": 4
        }

    filters["length_min_5_char"]= {
          "type": "length",
          "min": 5
        }

    filters["length_2_5_char"]= {
          "type": "length",
          "min": 2,
          "max": 5
        }

    filters["french_elision"]= {
          "type": "elision",
          "articles_case": True,
          "articles": ["l", "m", "t", "qu", "n", "s", "j", "d", "c", "jusqu", "quoiqu", "lorsqu", "puisqu"]
        }

    filters["french_stemmer"]= {
          "type":       "stemmer",
          "language":   "light_french"
        }

    filters["english_stemmer"]= {
          "type":       "stemmer",
          "language":   "light_english"
        }

    filters["underscore_remove"]= {
        "type": "pattern_replace",
        "pattern": "(-|_)",
        "replacement": " "
      }
              

    filters["city_remover"]= {
        "type": "stop",
        "ignore_case": True,
        "stopwords": main_cities
      }


    filters["custom_filter_name"]= {
        "type": "stop",
        "ignore_case": True,
        "stopwords": []
      }

    filters["keep_cities"]= {
      "type": "keep",
      "keep_words": main_cities
    }
    
    filters["keep_countries"]= {
      "type": "keep",
      "keep_words": main_countries
    }
    
    filters["keep_country_code"]= {
      "type": "keep",
      "keep_words": main_country_code
    }

    filters["common_acronyms_filter"]= {
        "type": "stop",
        "ignore_case": True,
        "stopwords": main_acronyms
      }
    
    filters["common_names_filter"]= {
        "type": "stop",
        "ignore_case": True,
        "stopwords": main_names
      }


    filters["city_synonym"] = {
                        "type" : "synonym_graph",
                        "synonyms" : [
                            "pierre benite, lyon",
                            "pierre bénite, lyon"
                        ]
                    } 

    filters["name_synonym"] = {
                        "type" : "synonym_graph",
                        "synonyms" : [
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
    char_filters =  {}
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

    return tokenizers

def get_analyzers():

    analyzers = {}

    analyzers["light"] = {
          "tokenizer": "icu_tokenizer",
          "filter": [
            "icu_folding"
          ]
        }

    analyzers["heavy"] = {
          "tokenizer": "icu_tokenizer",
          "filter": [
             "length_min_2_char",
             "icu_folding",
             "english_stop",
         #    "common_names_filter",
             "english_stemmer"
          ]
        }

    analyzers["analyzer_city"] = {
          "tokenizer": "icu_tokenizer",
          "filter": [
             "length_min_2_char",
              "lowercase",
             "icu_folding",
            "keep_cities",
              "city_synonym"
          ]
        }
    
    analyzers["analyzer_country"] =  {
            "tokenizer": "icu_tokenizer",
            "filter": [
                "icu_folding",
                "length_min_2_char",
                "lowercase",
                "keep_countries"
            ]
          }
    
    analyzers["analyzer_country_code"] =  {
            "tokenizer": "icu_tokenizer",
            "filter": [
                "icu_folding",
                "lowercase",
                "keep_country_code"
            ]
          }

    analyzers["analyzer_acronym"] =  {
            "tokenizer": "icu_tokenizer",
            "filter": [
                "length_min_3_char",
                "lowercase",
                "city_remover",
                "icu_folding",
                "english_stemmer"
            ]
          }
    analyzers["analyzer_name"] =  {
            "tokenizer": "icu_tokenizer",
            "filter": [
                "icu_folding",
                "english_stop",
                "length_min_5_char",
                "lowercase",
                "city_remover",
                "name_synonym",
                "custom_filter_name"
            ]
          }

    return analyzers



def delete_index_grid():
    myIndex = 'index-grid'
    print("deleting "+myIndex, end=':', flush=True)
    del_docs = es.delete_by_query(index=myIndex, body={"query": {"match_all": {}}})
    print(del_docs, flush=True)
    del_index = es.indices.delete(index=myIndex, ignore=[400, 404])
    print(del_index, flush=True)
    return 

def reset_index_grid(filters, char_filters, tokenizers, analyzers):

    myIndex = 'index-grid'
    try:
        delete_index_grid() 
    except:
        pass
    
    setting_grid = {
        "index":{
            "max_ngram_diff":8
        },
        "analysis": {        
            "char_filter": char_filters,
            "filter": filters,
            "analyzer": analyzers,
            "tokenizer": tokenizers
        }
      }
    
                
    mapping_grid={
      "properties": {
        "names":    { 
            "type": "text",
             "boost": 5,
            "analyzer": "analyzer_name"
        },
        "acronyms":    { 
            "type": "text",
             "boost": 5,
            "analyzer": "analyzer_acronym"  
        },
        "cities":    { 
            "type": "text",
            "boost": 2,
            "analyzer": "analyzer_city"   
        },
        "country":    { 
            "type": "text",
            "boost": 2,
            "analyzer": "analyzer_country"   
        },
        "country_code":    { 
            "type": "text",
            "boost": 2,
            "analyzer": "analyzer_country_code"   
        },
      }
    }
    
    response = es.indices.create(
        index=myIndex,
        body={
            "settings": setting_grid,
            "mappings": mapping_grid
            
        },
        ignore=400 # ignore 400 already exists code
    )

    if 'acknowledged' in response:
        if response['acknowledged'] == True:
            print ("INDEX MAPPING SUCCESS FOR INDEX:", response['index'], flush=True)
            
    print(response, flush=True)
    

def has_a_digit(x):
    for c in x:
        if c.isdigit():
            return True
    return False

def get_common_words(x, field, split=True, threshold = 10):
    common = {}
    for elt in x:
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

def download_url(url, save_path, chunk_size=128):
    r = requests.get(url, stream=True)
    with open(save_path, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            fd.write(chunk)


def get_grid():
    grid_data = []
    url_grid = "https://digitalscience.figshare.com/ndownloader/files/23552738"
    try:
        os.mkdir("grid_data")
    except:
        pass
    download_url(url_grid,"grid_data_dump.zip")
    with zipfile.ZipFile("grid_data_dump.zip", 'r') as zip_ref:
        zip_ref.extractall("grid_data")
    grid = json.load(open('grid_data/grid.json', 'r'))

    for elt in grid['institutes']:

        if elt.get('status') != 'active':
            continue
        new_elt = {}
        new_elt['id'] = elt['id']

        ################### NAMES
        names=[]
        if 'name' in elt:
            names.append(elt['name'])
        names += elt.get('aliases', [])
        for lab in elt.get('labels', []):
            if 'label' in lab:
                names.append(lab.get('label'))
        new_elt['names']=names

        ################### ACRONYMS

        acronyms=elt.get('acronyms', [])
        new_elt['acronyms']=acronyms

        ################### ADDRESSES

        cities=[]
        for ad in elt.get('addresses', []):
            if 'city' in ad:
                cities.append(ad['city'])
            if 'geonames_city' in ad and ad['geonames_city']:
                if 'nuts_level3' in ad['geonames_city'] and ad['geonames_city']['nuts_level3']:
                    if 'name' in ad['geonames_city']['nuts_level3']:
                        cities.append(ad['geonames_city']['nuts_level3']['name'])
                if 'nuts_level2' in ad['geonames_city'] and ad['geonames_city']['nuts_level2']:
                    if 'name' in ad['geonames_city']['nuts_level2']:
                        cities.append(ad['geonames_city']['nuts_level2']['name'])
        new_elt['cities'] = list(set(cities))

        new_elt['country'] = [k.get('country') for k in elt.get('addresses', []) if 'country' in k]
        new_elt['country_code'] = [k.get('country_code') for k in elt.get('addresses', []) if 'country_code' in k]

        ################## INDEX in ES
        grid_data.append(new_elt)
    return grid_data


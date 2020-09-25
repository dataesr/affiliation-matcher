import os

import requests
import datetime
import math
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Q, Search
from elasticsearch import helpers
import string
import unicodedata
import pickle

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

def init_es_finess():
    finess = pickle.load(open("dict_finess.pkl", "rb"))

    docs_to_index = []
    for k in finess:
        new_elt = {"name":[], "city":[], "id": k}

        for elt in finess[k]:

            if elt.get('dataesr_city'):
                new_elt['city'].append( elt.get('dataesr_city') )
            if elt.get('Ligne d’acheminement (CodePostal+Lib commune) ligneacheminement'):
                new_elt['city'].append( elt.get('Ligne d’acheminement (CodePostal+Lib commune) ligneacheminement') )

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
                known_cities.append(normalize(elt.get('dataesr_city')))
            if elt.get('Ligne d’acheminement (CodePostal+Lib commune) ligneacheminement'):
                known_cities.append(normalize(elt.get('Ligne d’acheminement (CodePostal+Lib commune) ligneacheminement')))
    known_cities = list(set(known_cities) - set('france'))
    names_to_remove = []

    filters = get_filters(known_cities, names_to_remove)
    char_filters = get_char_filters()
    tokenizers = get_tokenizers()
    analyzers = get_analyzers()
    res = {}

    reset_index_finess(filters, char_filters, tokenizers, analyzers)


    actions = [
    {
        "_index": "index-finess",
        "_type": "_doc",
        "_id": j,
        "_source": docs_to_index[j]
    }
            for j in range(0, len(docs_to_index))
    ]
    print(helpers.bulk(es, actions), flush=True)

    res["index-finess"] = len(docs_to_index)
    res['ok'] = 1
    return res

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

def get_filters(main_cities, main_names):
    filters = {}
    filters["keep_cities"]= {
      "type": "keep",
      "keep_words": main_cities
    }
    filters["city_remover"]= {
        "type": "stop",
        "ignore_case": True,
        "stopwords": main_cities
      }
    filters["common_names_filter"]= {
        "type": "stop",
        "ignore_case": True,
        "stopwords": main_names
      }
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

    filters["remove_space"] = {
      "type": "pattern_replace",
      "pattern": " ",
      "replacement": ""
    }
    return filters

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
#tokenizers["code_tokenizer"]= {
#          "type": "simple_pattern",
#          "pattern": "([A-Za-z\-\_]{1,5})(.{0,1})([0-9]{1,5})"
#        }

    tokenizers['code_tokenizer']=  {
          "type": "pattern",
          "pattern": "_|\W+"
        }

    tokenizers["code_tokenizer_lucky"]= {
          "type": "simple_pattern",
          "pattern": "(UMR|U|FR|EA|UPR|UR|CIC|GDR)(.{0,4})([0-9]{2,4})"
        }
    return tokenizers

def get_analyzers():

    analyzers = {}
    analyzers['analyzer_digits'] ={
        "tokenizer": "standard",
        "char_filter": ["keep_digits_only"],
        "filter": [ "length_2_5_char" ]
        }


    analyzers["analyzer_city"] = {
            "tokenizer": "standard",
            "char_filter": ["remove_digits"],
            "filter": ["lowercase",
                       "icu_folding",
                       "keep_cities"
                      ]
          }


    analyzers["analyzer_name"] =  {
            "tokenizer": "icu_tokenizer",
            "filter": [
                "french_elision",
                "icu_folding",
                "french_stop",
                "english_stop",
                "lowercase",
                "city_remover",
                "common_names_filter"
            ]
          }

    return analyzers


def delete_index_finess():
    myIndex = 'index-finess'
    print("deleting "+myIndex, end=':', flush=True)
    del_docs = es.delete_by_query(index=myIndex, body={"query": {"match_all": {}}})
    print(del_docs, flush=True)
    del_index = es.indices.delete(index=myIndex, ignore=[400, 404])
    print(del_index, flush=True)
    return

def reset_index_finess(filters, char_filters, tokenizers, analyzers):

    myIndex = 'index-finess'
    try:
        delete_index_finess()
    except:
        pass

    setting_finess = {
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


    mapping_finess={
      "properties": {
        "name":    {
            "type": "text",
             "boost": 5,
            "analyzer": "analyzer_name"
        },
        "city":    {
            "type": "text",
            "analyzer":"analyzer_name",

            "fields":{
                  "digits":{
                     "type":"text",
                     "analyzer":"analyzer_digits"
                  }
                ,"city":{
                     "type":"text",
                     "analyzer":"analyzer_city"
                  }
            }
        }
      }
    }

    response = es.indices.create(
        index=myIndex,
        body={
            "settings": setting_finess,
            "mappings": mapping_finess

        },
        ignore=400 # ignore 400 already exists code
    )

    if 'acknowledged' in response:
        if response['acknowledged'] == True:
            print ("INDEX MAPPING SUCCESS FOR INDEX:", response['index'], flush=True)

    print(response, flush=True)




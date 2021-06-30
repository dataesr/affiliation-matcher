import requests
from matcher.server.main.tasks import create_task_match

def get_annotated_data():
    url = 'https://storage.gra.cloud.ovh.net/v1/AUTH_32c5d10cb0fe4519b957064a111717e3/models/match_pubmed_affiliations_with_countries_v3.json'
    data = requests.get(url).json()
    return data

def compute_precision_recall(match_type, index_prefix=''):

    data = get_annotated_data()

    nb_TP, nb_FP, nb_FN = 0, 0, 0
    false_positive, false_negative = [], []
    for ix, d in enumerate(data):
        if d.get(match_type):
            res = create_task_match({'query': d['label'], 'year':'2020', 'type': match_type, 'index_prefix': index_prefix})
            for x in res['results']:
                if x in d[match_type]:
                    nb_TP += 1
                else:
                    nb_FP += 1
                    false_positive.append(d)
            for x in d[match_type]:
                if x not in res['results']:
                    nb_FN += 1
                    false_negative.append(d)

    precision = nb_TP / (nb_TP + nb_FP)
    recall = nb_TP / (nb_TP + nb_FN)
    res = {'precision' : precision, 'recall' : recall}
    return res

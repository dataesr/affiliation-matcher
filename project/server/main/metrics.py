import requests

from project.server.main.tasks import create_task_match


def get_annotated_data() -> dict:
    url = 'https://storage.gra.cloud.ovh.net/v1/AUTH_32c5d10cb0fe4519b957064a111717e3/models/' \
          'pubmed_and_h2020_affiliations.json'
    data = requests.get(url).json()
    return data


def compute_precision_recall(match_type: str, index_prefix: str = '') -> dict:
    data = get_annotated_data()
    nb_tp = 0
    false_positive, false_negative = [], []
    for ix, d in enumerate(data):
        if d.get(match_type):
            matches = create_task_match({'query': d['label'], 'year': '2020', 'type': match_type,
                                         'index_prefix': index_prefix})
            for x in matches['results']:
                if x in d[match_type]:
                    nb_tp += 1
                else:
                    false_positive.append(d)
            for x in d[match_type]:
                if x not in matches['results']:
                    false_negative.append(d)
    nb_fn = len(false_negative)
    nb_fp = len(false_positive)
    precision = nb_tp / (nb_tp + nb_fp)
    recall = nb_tp / (nb_tp + nb_fn)
    return {'precision': precision, 'recall': recall}

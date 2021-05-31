import requests
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

from matcher.server.main.config import config

es = Elasticsearch(config['ELASTICSEARCH_HOST'])


def normalize_for_count(x, matching_field):
    analyzer = None
    if matching_field in ['name', 'city']:
        analyzer = "analyzer_{}".format(matching_field)

    if analyzer:
        try:
            r = requests.post(config['ELASTICSEARCH_URL'] + "index-finess/_analyze", json={
                "analyzer": analyzer,
                "text": x
            }).json()
            return r['tokens'][0]['token']
        except:
            pass
    return x.lower()[0:6]


def match_unstructured_finess(query=''):
    logs = ""
    logs += "<h1> &#128269; {}</h1>".format(query)
    x = query

    matching_info = {}
    matching_info['city'] = get_match_city(x)
    matching_info['name'] = get_match_name(x)

    strategies = []

    strategies.append("name;city")

    return match_structured(matching_info, strategies, logs)


def match_structured(matching_info, strategies, logs):
    all_matches = {}
    field_matches = {}
    min_match_for_field = {}
    for f in matching_info:
        for match_id in matching_info[f].get('nb_matches', {}):
            if match_id not in all_matches:
                all_matches[match_id] = 0
                field_matches[match_id] = []
            all_matches[match_id] += matching_info[f].get('nb_matches', {})[match_id]
            if f not in field_matches[match_id]:
                field_matches[match_id].append(f)

        min_match_for_field[f] = 1

    relevant_matches = {}

    final_results = {}
    forbidden_id = []

    logs += "<ol> "
    for strat in strategies:
        stop_current_start = False
        current_strat_answers = []
        strat_fields = strat.split(';')
        logs += "<li>Strategie testée : {}".format(strat)

        indiv_ids = [matching_info[field]['ids'] for field in strat_fields]
        strat_ids = set(indiv_ids[0]).intersection(*indiv_ids)

        if len(strat_ids) == 0:
            logs += " &empty; </li>"
            continue
        logs += "</li></br>"

        max_number = {}
        logs += "<ol> "

        potential_sirens = []

        for potential_id in strat_ids:
            logs += " <li> Id potentiel : {}<br/></li>".format(potential_id)
            current_match = {'id': potential_id}

            if 'sire' in potential_id:
                potential_sirens.append(potential_id[5:14])

            for field in strat_fields:
                current_match[field + '_match'] = 0
                # probleme avec les highlights
                bbb = matching_info[field]['nb_matches'][potential_id]
                if potential_id in matching_info[field]['nb_matches']:
                    current_match[field + '_match'] = matching_info[field]['nb_matches'][potential_id]

                    current_highlights = matching_info[field]['highlights'][potential_id]
                    current_highlights = [e.replace('<em>', '<strong>').replace('</em>', '</strong>') for e in
                                          current_highlights]
                    logs += "     - {} {} : {}<br/>".format(
                        matching_info[field]['nb_matches'][potential_id],
                        field,
                        current_highlights)

                if field not in max_number:
                    max_number[field] = 0
                    # if field == 'name':
                    #    max_number[field] = 2

                max_number[field] = max(max_number[field], current_match[field + '_match'])

            current_strat_answers.append(current_match)

        if len(max_number) > 0:
            logs += "<li> &#9989; Nombre de match par champ : {}<br/></li>".format(max_number)

        logs += "</ol>"  # end of potential ids

        if len(strat_ids) == 0:
            continue

        current_potential_ids = strat_ids
        retained_id_for_strat = []
        ignored_id = []
        logs += "Parcours des champs de la stratégie :"
        for field in strat_fields:
            logs += "{}...".format(field)
            if field in ["city", "code_fuzzy"]:
                logs += "(ignoré)..."
                continue

            for potential_id in current_potential_ids:
                if potential_id in matching_info[field]['nb_matches']:
                    if matching_info[field]['nb_matches'][potential_id] == max_number[field]:
                        if max_number[field] >= min_match_for_field[field]:
                            retained_id_for_strat.append(potential_id)
                        else:
                            logs += "<br/> &#128584; " + potential_id + " ignoré car {} {} est insuffisant ({} attendus au min)".format(
                                max_number[field], field, min_match_for_field[field])
                            ignored_id.append(potential_id)
                    elif potential_id not in matching_info.get('code', {}).get('ids', []):
                        logs += "<br/> &#10060; {} ajouté à la black-list car seulement {} {} vs le max est {}".format(
                            potential_id,
                            matching_info[field]['nb_matches'][potential_id],
                            field,
                            max_number[field])
                        forbidden_id.append(potential_id)
            if len(retained_id_for_strat) == 1:
                if ('code' in strat_fields) or ('code_digit' in strat_fields) or ('acronym' in strat_fields) or (
                        'code_fuzzy' in strat_fields):
                    logs += "<br/> &#9209;&#65039; Arrêt au champ " + field
                    break
                else:
                    pass
                    # if verbose:
                    # print("not stopping because strategy has no code or acronym")
                    # print(matching_info.get('name',{}).get('highlights', {}).get(potential_id))
            else:
                current_potential_ids = retained_id_for_strat
                retained_id_for_strat = []
        for x in ignored_id:
            if x in retained_id_for_strat:
                retained_id_for_strat.remove(x)
        final_results[strat] = list(set(retained_id_for_strat))

        # for res in final_results:
        if len(final_results[strat]) == 1:
            logs += "<br/> 1&#65039;&#8419; unique match pour cette stratégie : {} ".format(final_results[strat][0])
            if final_results[strat][0] in forbidden_id:
                logs += "&#10060; car dans la black-list"
                continue


            else:
                logs += " &#128076;<br/>"
                logs += "<h3>{}</h3>".format(final_results[strat][0])
                return {'match': final_results[strat][0], 'logs': logs}


        else:
            potential_sirens = list(set(potential_sirens))
            if len(potential_sirens) == 1:
                logs += "<br/> all potential match have the same siren " + potential_sirens[0]
                logs += " &#128076;<br/>"
                logs += "<h3>{}</h3>".format(potential_sirens[0])
                return {'match': "siren" + potential_sirens[0], 'logs': logs}

    return {'match': None, 'logs': logs}


def get_match_name(x, verbose=False):
    return get_info(x, ['name'], size=2000, verbose=verbose, highlights=['name'])


def get_match_city(x, verbose=False):
    return get_info(x, ['city.city'], size=2000, verbose=verbose, highlights=['city.city'])


def get_info(input_str, search_fields, size=20, verbose=False, highlights=[], fuzzy_ok=False):
    myIndex = "index-finess"
    s = Search(using=es, index=myIndex)
    for f in highlights:
        s = s.highlight(f)

    s = s.query("multi_match", query=input_str,
                minimum_should_match=1,
                # fuzziness="auto",
                fields=search_fields)

    s = s[0:size]
    res = s.execute()
    hits = res.hits

    id_res = ""
    if len(hits) > 0:
        max_score = hits[0].meta.score

    res_ids = []
    scores = []
    highlights = {}
    nb_matches = {}
    matches_frag = {}

    for hit in hits:

        res_ids.append(hit.id)
        scores.append(hit.meta.score)
        highlights[hit.id] = []

        for matching_field in hit.meta.highlight:
            for fragment in hit.meta.highlight[matching_field]:
                highlights[hit.id].append(fragment)

                matches = [normalize_for_count(e.get_text(), matching_field) for e in
                           BeautifulSoup(fragment, 'lxml').find_all('em')]

                if hit.id not in nb_matches:
                    nb_matches[hit.id] = 0
                    matches_frag[hit.id] = []
                matches_frag[hit.id] += matches
                matches_frag[hit.id] = list(set(matches_frag[hit.id]))
                nb_matches[hit.id] = len(matches_frag[hit.id])

    # print(scores)
    return {'ids': res_ids, 'highlights': highlights, 'nb_matches': nb_matches}

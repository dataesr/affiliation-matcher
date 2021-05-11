import requests

from bs4 import BeautifulSoup
from elasticsearch_dsl import Search

from matcher.server.main.config import config
from matcher.server.main.my_elastic import MyElastic

es = MyElastic()


def normalize_for_count(x, matching_field):
    if 'code' in matching_field:
        return x.upper()
    analyzer = None
    if matching_field in ['name', 'acronym']:
        analyzer = "analyzer_{}".format(matching_field)
    elif matching_field in ['city', 'supervisors_city']:
        analyzer = "analyzer_address"
    elif matching_field in ['supervisors_acronym']:
        analyzer = "analyzer_supervisor_acronym"
    elif matching_field in ['supervisors_name']:
        analyzer = "analyzer_supervisor"
    if analyzer:
        try:
            r = requests.post(config['ELASTICSEARCH_URL'] + 'index-rnsr-all/_analyze', json={
                'analyzer': analyzer,
                'text': x
            }).json()
            return r['tokens'][0]['token']
        except:
            pass
    return x.lower()[0:6]


def match_unstructured(year: str = '2020', query: str = '') -> dict:
    matching_info = {
        'code': get_match_code(year, query),
        'code_digit': get_match_code_digit(year, query),
        'code_label': get_match_code_label(year, query),
        'code_fuzzy': get_match_code_fuzzy(year, query),
        'supervisors_acronym': get_match_supervisors_acronym(year, query),
        'supervisors_name': get_match_supervisors_name(year, query),
        'city': get_match_city(year, query),
        'name': get_match_name(year, query),
        'acronym': get_match_acronym(year, query)
    }
    strategies = [
        'code;supervisors_acronym;supervisors_name;city',
        'code;supervisors_name;city',
        'code;acronym',
        'code;name',
        'code;supervisors_acronym',
        'code;supervisors_name',
        'code;city',
        'code_digit;supervisors_acronym;supervisors_name;city',
        'code_digit;supervisors_name;city',
        'code_digit;acronym',
        'code_digit;name',
        'code_digit;supervisors_acronym',
        'code_digit;supervisors_name',
        'acronym;name;supervisors_name;city',
        'acronym;name;supervisors_acronym;city',
        'acronym;supervisors_acronym;city',
        'acronym;supervisors_name;city',
        'name;supervisors_acronym;city',
        'name;supervisors_name;city',
        'name;acronym;city',
        'name;acronym;supervisors_acronym',
        'name;acronym;supervisors_name',
        'acronym;city',
        'code_fuzzy;city'
    ]
    logs = '<h1> &#128269; {query}</h1>'.format(query=query)
    return match_structured(matching_info=matching_info, strategies=strategies, logs=logs)


# Todo: Deprecated
def match_fields(year, code, name, city, acronym, supervisors_id) -> dict:
    matching_info = {
        'code': get_match_code(year, code),
        'name': get_match_name(year, name),
        'city': get_match_city(year, city),
        'acronym': get_match_acronym(year, acronym),
        'supervisors_id': get_match_supervisors_id(year, supervisors_id)
    }
    strategies = [
        'code;city;name;acronym;supervisors_id',
        'code;city;name;supervisors_id',
        'code;city;acronym;supervisors_id',
        'code;acronym;supervisors_id',
        'code;name;supervisors_id',
        'city;name;acronym;supervisors_id',
        'city;acronym;supervisors_id'
    ]
    return match_structured(matching_info=matching_info, strategies=strategies)


def match_structured(matching_info: dict = None, strategies: list = None, logs: str = '') -> dict:
    has_code = False
    if len(matching_info.get('code', {}).get('ids', [])) > 0:
        has_code = True
    has_acronym = False
    if len(matching_info.get('acronym', {}).get('ids', [])) > 0:
        has_acronym = True
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
    min_match_for_field['supervisors_name'] = 3
    min_match_for_field['supervisors_acronym'] = 2
    final_results = {}
    forbidden_id = []
    logs += "<ol> "
    for strat in strategies:
        current_strat_answers = []
        current_strat_avoid = []
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
        for potential_id in strat_ids:
            logs += " <li> Id potentiel : {}<br/></li>".format(potential_id)
            current_match = {'id': potential_id}
            for field in strat_fields:
                current_match[field + '_match'] = 0
                if potential_id in matching_info[field]['nb_matches']:
                    current_match[field + '_match'] = matching_info[field]['nb_matches'][potential_id]
                    current_highlights = matching_info[field]['highlights'][potential_id]
                    current_highlights = [highlight.replace('<em>', '<strong>').replace('</em>', '</strong>')
                                          for highlight in current_highlights]
                    logs += "     - {} {} : {}<br/>".format(
                        matching_info[field]['nb_matches'][potential_id],
                        field,
                        current_highlights)
                if field not in max_number:
                    max_number[field] = 0
                max_number[field] = max(max_number[field], current_match[field + '_match'])
            current_strat_answers.append(current_match)
        if len(max_number) > 0:
            logs += "<li> &#9989; Nombre de match par champ : {}<br/></li>".format(max_number)
        logs += "</ol>"
        if len(strat_ids) == 0:
            continue
        current_potential_ids = strat_ids
        retained_id_for_strat = []
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
                            logs += "<br/> &#128584; " + potential_id + " ignoré car {} {} est insuffisant ({} " \
                                    "attendus au min)".format(max_number[field], field, min_match_for_field[field])
                            current_strat_avoid.append(potential_id)
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
            else:
                current_potential_ids = retained_id_for_strat
                retained_id_for_strat = []
        final_results[strat] = list(set(retained_id_for_strat))
        for x in current_strat_avoid:
            if x in final_results[strat]:
                final_results[strat].remove(x)
        if len(final_results[strat]) == 1:
            logs += "<br/> 1&#65039;&#8419; unique match pour cette stratégie : {} ".format(final_results[strat][0])
            if final_results[strat][0] in forbidden_id:
                logs += "&#10060; car dans la black-list"
                continue
            if has_code:
                if final_results[strat][0] in matching_info.get('code', {}).get('ids', []):
                    logs += " &#128076; car a bien un label numéro <br/>"
                    logs += "<h3>{}</h3>".format(final_results[strat][0])
                    return_id = final_results[strat][0]
                    return_val = {'match': return_id, 'logs': logs}
                    return_val.update(get_supervisors(return_id))
                    return return_val
                elif final_results[strat][0] in matching_info.get('code_digit', {}).get('ids', []):
                    logs += " &#128076; car a bien les chiffres du label numéro <br/>"
                    logs += "<h3>{}</h3>".format(final_results[strat][0])
                    return_id = final_results[strat][0]
                    return_val = {'match': return_id, 'logs': logs}
                    return_val.update(get_supervisors(return_id))
                    return return_val
                else:
                    logs += " &#128078; car n'a pas le label numéro"
                    continue
            elif has_acronym:
                if final_results[strat][0] in matching_info.get('acronym', {}).get('ids', []):
                    logs += " &#128076; car a bien un acronyme <br/>"
                    logs += "<h3>{}</h3>".format(final_results[strat][0])
                    return_id = final_results[strat][0]
                    return_val = {'match': return_id, 'logs': logs}
                    return_val.update(get_supervisors(return_id))
                    return return_val
                else:
                    logs += " &#128078; car n'a pas l'acronyme"
                    continue
            else:
                logs += " &#128076;<br/>"
                logs += "<h3>{}</h3>".format(final_results[strat][0])
                return_id = final_results[strat][0]
                return_val = {'match': return_id, 'logs': logs}
                return_val.update(get_supervisors(return_id))
                return return_val
    return {'match': None, 'logs': logs}


def get_match_code(year, query) -> dict:
    return get_info(year, query, ['code_numbers'], size=20, highlights=['code_numbers'])


def get_match_code_label(year, query) -> dict:
    return get_info(year, query, ['code_numbers.labels'], size=10000, highlights=['code_numbers.labels'])


def get_match_code_digit(year, query) -> dict:
    return get_info(year, query, ['code_numbers.digits'], size=20, highlights=['code_numbers.digits'])


def get_match_code_fuzzy(year, query) -> dict:
    return get_info(year, query, ['code_numbers', 'code_numbers.digits'], size=1000,
                    highlights=['code_numbers', 'code_numbers.digits'], fuzzy_ok=True)


def get_match_city(year, query) -> dict:
    return get_info(year, query, ['addresses'], size=5000, highlights=['addresses'])


def get_match_name(year, query) -> dict:
    return get_info(year, query, ['names'], size=200, highlights=['names'])


def get_match_acronym(year, query) -> dict:
    return get_info(year, query, ['acronyms'], size=5000, highlights=['acronyms'])


def get_match_supervisors_name(year, query) -> dict:
    return get_info(year, query, ['supervisors_name'], size=10000, highlights=['supervisors_name'])


def get_match_supervisors_id(year, query) -> dict:
    return get_info(year, query, ['supervisors_id'], size=2000, highlights=['supervisors_id'])


def get_match_supervisors_acronym(year, query) -> dict:
    return get_info(year, query, ['supervisors_acronym'], size=2000, highlights=['supervisors_acronym'])


def get_info(year, query: str = None, search_fields: list = None, size=20, highlights: list = None,
             fuzzy_ok=False) -> dict:
    if query is None:
        query = ''
    if search_fields is None:
        search_fields = []
    if highlights is None:
        highlights = []
    index = 'index-rnsr-{year}'.format(year=year)
    s = Search(using=es, index=index)
    for f in highlights:
        s = s.highlight(f)
    if search_fields == ['names']:
        s = s.query('multi_match', query=query, minimum_should_match=1, fuzziness='auto', fields=search_fields)
    else:
        s = s.query('multi_match', query=query, minimum_should_match=1, fields=search_fields)
    s = s[0:size]
    results = s.execute()
    hits = results.hits
    if len(hits) == 0 and fuzzy_ok:
        s = Search(using=es, index=index)
        for f in highlights:
            s = s.highlight(f)
        s = s.query('multi_match', query=query,
                    fuzziness=1,
                    fields=search_fields)
        s = s[0:size]
        results = s.execute()
        hits = results.hits
    ids = []
    scores = []
    highlights = {}
    nb_matches = {}
    matches_frag = {}
    for hit in hits:
        if search_fields == ['names'] and hit.meta.score < hits.max_score * 0.5:
            continue
        ids.append(hit.id)
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
    return {'ids': ids, 'highlights': highlights, 'nb_matches': nb_matches}


def get_supervisors(rnsr_id) -> dict:
    index = config['ELASTICSEARCH_INDEX']
    s = Search(using=es, index=index)
    s = s.query('multi_match', query=rnsr_id, fields='id')
    hit = s.execute().hits[0]
    return {
        'supervisors_id': list(hit.supervisors_id),
        'supervisors_name': list(hit.supervisors_name),
        'supervisors_acronym': list(hit.supervisors_acronym)
    }

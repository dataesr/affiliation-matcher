import requests
from bs4 import BeautifulSoup
from elasticsearch_dsl import Search

from matcher.server.main.config import ELASTICSEARCH_URL
from matcher.server.main.my_elastic import MyElastic

es = MyElastic()
ES_INDEX = 'grid'


def normalize_for_count(text: str = None, matching_field: str = None) -> str:
    if matching_field in ['name', 'acronym']:
        analyzer = f'analyzer_{matching_field}'
    elif matching_field in ['city']:
        analyzer = 'analyzer_city'
    elif matching_field in ['country']:
        analyzer = 'analyzer_country'
    elif matching_field in ['country_code']:
        analyzer = 'analyzer_country_code'
    else:
        analyzer = None
    if analyzer:
        try:
            url = f'{ELASTICSEARCH_URL}/{ES_INDEX}/_analyze'
            response = requests.post(url, json={'analyzer': analyzer, 'text': text}).json()
            return response['tokens'][0]['token']
        except:
            pass
    return text.lower()[0:6]


def match_grid_unstructured(query: str = None) -> dict:
    logs = f'<h1> &#128269; {query}</h1>'
    matching_info = {
        'country': get_match_country(query),
        'country_code': get_match_country_code(query),
        'city': get_match_city(query),
        'name': get_match_name(query),
        'acronym': get_match_acronym(query)
    }
    strategies = [
        'name;acronym;city;country_code',
        'name;acronym;city;country',
        'name;city;country_code',
        'name;city;country',
        'acronym;city;country_code',
        'acronym;city;country'
    ]
    return match_grid_structured(matching_info=matching_info, strategies=strategies, logs=logs)


def match_grid_fields(name: str = None, city: str = None, acronym: str = None, country: str = None,
                      country_code: str = None) -> dict:
    matching_info = {
        'name': get_match_name(query=name),
        'city': get_match_city(query=city),
        'acronym': get_match_acronym(query=acronym),
        'country': get_match_country(query=country),
        'country_code': get_match_country_code(query=country_code)
    }
    strategies = [
        'name;acronym;city;country_code',
        'name;acronym;city;country',
        'name;city;country_code',
        'name;city;country',
        'acronym;city;country_code',
        'acronym;city;country'
    ]
    return match_grid_structured(matching_info=matching_info, strategies=strategies)


def match_grid_structured(matching_info: dict = None, strategies: list = None, logs: str = None) -> dict:
    if matching_info is None:
        matching_info = {}
    if strategies is None:
        strategies = []
    if logs is None:
        logs = ''
    has_acronym = len(matching_info.get('acronym', {}).get('ids', [])) > 0
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
    logs += '<ol>'
    for strat in strategies:
        current_strat_answers = []
        current_strat_avoid = []
        strat_fields = strat.split(';')
        logs += f'<li>Strategie testée : {strat}'
        indiv_ids = [matching_info[field]['ids'] for field in strat_fields]
        strat_ids = set(indiv_ids[0]).intersection(*indiv_ids)
        if len(strat_ids) == 0:
            logs += ' &empty; </li>'
            continue
        logs += '</li></br>'
        max_number = {}
        logs += '<ol>'
        for potential_id in strat_ids:
            logs += f'<li> Id potentiel : {potential_id}<br/></li>'
            current_match = {'id': potential_id}
            for field in strat_fields:
                current_match[field + '_match'] = 0
                if potential_id in matching_info[field]['nb_matches']:
                    current_match[field + '_match'] = matching_info[field]['nb_matches'][potential_id]
                    current_highlights = matching_info[field]['highlights'][potential_id]
                    current_highlights = [e.replace('<em>', '<strong>').replace('</em>', '</strong>')
                                          for e in current_highlights]
                    logs += f'     - {matching_info[field]["nb_matches"][potential_id]} {field} : ' \
                            f'{current_highlights}<br/>'
                if field not in max_number:
                    max_number[field] = 0
                max_number[field] = max(max_number[field], current_match[field + '_match'])
            current_strat_answers.append(current_match)
        if len(max_number) > 0:
            logs += f'<li> &#9989; Nombre de match par champ : {max_number}<br/></li>'
        logs += '</ol>'
        if len(strat_ids) == 0:
            continue
        current_potential_ids = strat_ids
        retained_id_for_strat = []
        logs += 'Parcours des champs de la stratégie :'
        for field in strat_fields:
            logs += f'{field}...'
            if field in ['city', 'code_fuzzy']:
                logs += '(ignoré)...'
                continue
            for potential_id in current_potential_ids:
                if potential_id in matching_info[field]['nb_matches']:
                    if matching_info[field]['nb_matches'][potential_id] == max_number[field]:
                        if max_number[field] >= min_match_for_field[field]:
                            retained_id_for_strat.append(potential_id)
                        else:
                            logs += '<br/> &#128584; ' + potential_id
                            logs += f' ignoré car {max_number[field]} {field} est insuffisant' \
                                    f' ({min_match_for_field[field]} attendus au min)'
                            current_strat_avoid.append(potential_id)
                    elif potential_id not in matching_info.get('code', {}).get('ids', []):
                        logs += f'<br/> &#10060; {potential_id} ajouté à la black-list car seulement' \
                                f' {matching_info[field]["nb_matches"][potential_id]} {field} vs le max' \
                                f' est {max_number[field]}'
                        forbidden_id.append(potential_id)
            if len(retained_id_for_strat) == 1:
                if ('code' in strat_fields) or ('code_digit' in strat_fields) or ('acronym' in strat_fields) \
                        or ('code_fuzzy' in strat_fields):
                    logs += '<br/> &#9209;&#65039; Arrêt au champ ' + field
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
            logs += f'<br/> 1&#65039;&#8419; unique match pour cette stratégie : {final_results[strat][0]} '
            if final_results[strat][0] in forbidden_id:
                logs += '&#10060; car dans la black-list'
                continue
            if has_acronym:
                if final_results[strat][0] in matching_info.get('acronym', {}).get('ids', []):
                    logs += ' &#128076; car a bien un acronyme <br/>'
                    logs += f'<h3>{final_results[strat][0]}</h3>'
                    return {'match': final_results[strat][0], 'logs': logs}
                else:
                    logs += ' &#128078; car n\'a pas l\'acronyme'
                    continue
            else:
                logs += ' &#128076;<br/>'
                logs += f'<h3>{final_results[strat][0]}</h3>'
                return {'match': final_results[strat][0], 'logs': logs}
    return {'match': None, 'logs': logs}


def get_match_city(query: str = None) -> dict:
    return get_info(query=query, fields=['cities'], size=50000)


def get_match_name(query: str = None) -> dict:
    return get_info(query=query, fields=['names'], size=200)


def get_match_acronym(query: str = None) -> dict:
    return get_info(query=query, fields=['acronyms'], size=5000)


def get_match_country(query: str = None) -> dict:
    return get_info(query=query, fields=['country'], size=100000)


def get_match_country_code(query: str = None) -> dict:
    return get_info(query=query, fields=['country_code'], size=100000)


def get_info(query: str = None, fields: list = None, size: int = 20, highlights: list = None, fuzzy_ok: bool = False) \
        -> dict:
    if fields is None:
        fields = []
    if highlights is None:
        highlights = fields
    s = Search(using=es, index=ES_INDEX)
    for f in highlights:
        s = s.highlight(f)
    if fields == ['names']:
        s = s.query('multi_match', query=query, minimum_should_match=1, fuzziness='auto', fields=fields)
    else:
        s = s.query('multi_match', query=query, minimum_should_match=1, fields=fields)
    s = s[0:size]
    res = s.execute()
    hits = res.hits
    if len(hits) == 0 and fuzzy_ok:
        s = Search(using=es, index=ES_INDEX)
        for f in highlights:
            s = s.highlight(f)
        s = s.query('multi_match', query=query, fuzziness=1, fields=fields)
        s = s[0:size]
        res = s.execute()
        hits = res.hits
    ids = []
    scores = []
    highlights = {}
    nb_matches = {}
    matches_frag = {}
    for hit in hits:
        if fields == ['names'] and hit.meta.score < hits.max_score * 0.5:
            continue
        ids.append(hit.id)
        scores.append(hit.meta.score)
        highlights[hit.id] = []
        for matching_field in hit.meta.highlight:
            for fragment in hit.meta.highlight[matching_field]:
                highlights[hit.id].append(fragment)
                matches = [normalize_for_count(e.get_text(), matching_field)
                           for e in BeautifulSoup(fragment, 'lxml').find_all('em')]
                if hit.id not in nb_matches:
                    nb_matches[hit.id] = 0
                    matches_frag[hit.id] = []
                matches_frag[hit.id] += matches
                matches_frag[hit.id] = list(set(matches_frag[hit.id]))
                nb_matches[hit.id] = len(matches_frag[hit.id])
    return {'ids': ids, 'highlights': highlights, 'nb_matches': nb_matches}

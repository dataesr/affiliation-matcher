import requests
import datetime
from bs4 import BeautifulSoup

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Q, Search
from elasticsearch import helpers
es = Elasticsearch(['elasticsearch', 'localhost'])

#def normalize_for_count(x):
#    return x.lower()[0:6]

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
            r = requests.post("http://localhost:9200/index-rnsr-all/_analyze", json={
              "analyzer" : analyzer,
              "text" : x
            }).json()
            return r['tokens'][0]['token']
        except:
            pass
    return x.lower()[0:6]

def match_unstructured(year, query=''):

    logs = ""
    logs += "<h1> &#128269; {}</h1>".format(query)
    x = query

    matching_info={}
    matching_info['code'] = get_match_code(year, x)
    matching_info['code_digit'] = get_match_code_digit(year, x)
    matching_info['code_label'] = get_match_code_label(year, x)
    matching_info['code_fuzzy'] = get_match_code_fuzzy(year, x)
    matching_info['supervisors_acronym'] = get_match_supervisors_acronym(year, x)
    matching_info['supervisors_name'] = get_match_supervisors_name(year, x)
    matching_info['city'] = get_match_city(year, x)
    matching_info['name'] = get_match_name(year, x)
    matching_info['acronym'] = get_match_acronym(year, x)

    strategies=[]

    strategies.append("code;supervisors_acronym;supervisors_name;city")
    strategies.append("code;supervisors_name;city")
    strategies.append("code;acronym")
    strategies.append("code;name")
    strategies.append("code;supervisors_acronym")
    strategies.append("code;supervisors_name")
    strategies.append("code;city")

    strategies.append("code_digit;supervisors_acronym;supervisors_name;city")
    strategies.append("code_digit;supervisors_name;city")
    strategies.append("code_digit;acronym")
    strategies.append("code_digit;name")
    strategies.append("code_digit;supervisors_acronym")
    strategies.append("code_digit;supervisors_name")


    strategies.append("acronym;name;supervisors_name;city")
    strategies.append("acronym;name;supervisors_acronym;city")

    strategies.append("acronym;supervisors_acronym;city")
    strategies.append("acronym;supervisors_name;city")

    strategies.append("name;supervisors_acronym;city")
    strategies.append("name;supervisors_name;city")


    strategies.append("name;acronym;city")


    strategies.append("name;acronym;supervisors_acronym")
    strategies.append("name;acronym;supervisors_name")

    strategies.append("acronym;city")

    strategies.append("code_fuzzy;city")

    return match_structured(matching_info, strategies, logs)

def match_fields(year, code, name, city, acronym, supervisors_id):

    matching_info={}

    matching_info['code'] = get_match_code(year, code)
    matching_info['name'] = get_match_name(year, name)
    matching_info['city'] = get_match_city(year, city)
    matching_info['acronym'] = get_match_acronym(year, acronym)
    matching_info['supervisors_id'] = get_match_supervisors_id(year, supervisors_id)

    logs=""
    strategies=[]
    strategies.append("code;city;name;acronym;supervisors_id")
    strategies.append("code;city;name;supervisors_id")
    strategies.append("code;city;acronym;supervisors_id")
    strategies.append("city;name;acronym;supervisors_id")
    return match_structured(matching_info, strategies, logs)

def match_structured(matching_info, strategies, logs):
    
    has_code = False
    if len(matching_info.get('code', {}).get('ids', [])) > 0:
        has_code = True
    
    has_acronym=False
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
    relevant_matches = {}
    
    
    final_results = {}
    forbidden_id = []
    
    logs += "<ol> "
    for strat in strategies:
        stop_current_start = False
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
                current_match[field+'_match'] = 0
                #probleme avec les highlights
                bbb =  matching_info[field]['nb_matches'][potential_id]
                if potential_id in matching_info[field]['nb_matches']:
                    current_match[field+'_match'] = matching_info[field]['nb_matches'][potential_id]
                    
                    current_highlights = matching_info[field]['highlights'][potential_id]
                    current_highlights = [e.replace('<em>', '<strong>').replace('</em>', '</strong>') for e in current_highlights]
                    logs += "     - {} {} : {}<br/>".format(
                            matching_info[field]['nb_matches'][potential_id],
                            field,
                            current_highlights)    
          
                
                if field not in max_number:
                    max_number[field] = 0
                    #if field == 'name':
                    #    max_number[field] = 2

                max_number[field] = max(max_number[field], current_match[field+'_match'])

            current_strat_answers.append(current_match)
        
        
        
        if len(max_number)>0:
            logs += "<li> &#9989; Nombre de match par champ : {}<br/></li>".format(max_number)
            
        logs += "</ol>" # end of potential ids
                
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
                    if  matching_info[field]['nb_matches'][potential_id] == max_number[field]:
                        if max_number[field] >= min_match_for_field[field]:
                            retained_id_for_strat.append(potential_id)
                        else:
                            logs +="<br/> &#128584; "+potential_id+" ignoré car {} {} est insuffisant ({} attendus au min)".format(
                                max_number[field], field, min_match_for_field[field])
                            current_strat_avoid.append(potential_id)
                    elif potential_id not in matching_info.get('code', {}).get('ids', []):
                        logs += "<br/> &#10060; {} ajouté à la black-list car seulement {} {} vs le max est {}".format(
                            potential_id,
                            matching_info[field]['nb_matches'][potential_id],
                            field,
                            max_number[field])
                        forbidden_id.append(potential_id)
            if len(retained_id_for_strat) == 1:
                if ('code' in strat_fields) or ('code_digit' in strat_fields) or ('acronym' in strat_fields) or ('code_fuzzy' in strat_fields):
                    logs +="<br/> &#9209;&#65039; Arrêt au champ "+field
                    break
                else:
                    pass
                    #if verbose:
                        #print("not stopping because strategy has no code or acronym")
                        #print(matching_info.get('name',{}).get('highlights', {}).get(potential_id))
            else:
                current_potential_ids = retained_id_for_strat
                retained_id_for_strat = []
        final_results[strat] = list(set(retained_id_for_strat))
        for x in current_strat_avoid:
            final_results[strat].remove(x)
            
    #for res in final_results:
        if len(final_results[strat]) == 1:
            logs += "<br/> 1&#65039;&#8419; unique match pour cette stratégie : {} ".format(final_results[strat][0])
            if final_results[strat][0] in forbidden_id:
                logs += "&#10060; car dans la black-list"
                continue
                
            if has_code: 
                if final_results[strat][0] in matching_info['code']['ids']:
                    logs += " &#128076; car a bien un label numéro <br/>"
                    logs += "<h3>{}</h3>".format(final_results[strat][0])
                    return {'match': final_results[strat][0], 'logs': logs}
                elif final_results[strat][0] in matching_info['code_digit']['ids']:
                    logs += " &#128076; car a bien les chiffres du label numéro <br/>"
                    logs += "<h3>{}</h3>".format(final_results[strat][0])
                    return {'match': final_results[strat][0], 'logs': logs}
                else:
                    logs += " &#128078; car n'a pas le label numéro"
                    continue
            elif has_acronym:
                if final_results[strat][0] in matching_info['acronym']['ids']:
                    logs += " &#128076; car a bien un acronyme <br/>"
                    logs += "<h3>{}</h3>".format(final_results[strat][0])
                    return {'match': final_results[strat][0], 'logs': logs}
                else:
                    logs += " &#128078; car n'a pas l'acronyme"
                    continue
                
            else:
                logs += " &#128076;<br/>"
                logs += "<h3>{}</h3>".format(final_results[strat][0])
                return {'match': final_results[strat][0], 'logs': logs}
    
    return {'match': None, 'logs': logs}

def get_match_code(year, x, verbose=False):
    return get_info(year, x, ["code_numbers"], size=20, verbose=verbose, 
                    highlights=["code_numbers"])
def get_match_code_label(year, x, verbose=False):
    return get_info(year, x, ["code_numbers.labels"], size=10000, verbose=verbose, 
                    highlights=["code_numbers.labels"])
def get_match_code_digit(year, x, verbose=False):
    return get_info(year, x, ["code_numbers.digits"], size=20, verbose=verbose, 
                    highlights=["code_numbers.digits"])
    #return get_info(year, x, ["code_numbers", "code_numbers.digits_only"], size=20, verbose=verbose, 
    #                highlights=["code_numbers", "code_numbers.digits_only"])
def get_match_code_fuzzy(year, x, verbose=False):
    return get_info(year, x, ["code_numbers", "code_numbers.digits"], size=1000, verbose=verbose, 
                    highlights=["code_numbers", "code_numbers.digits"], fuzzy_ok=True)
def get_match_city(year, x, verbose=False):
    return get_info(year, x, ['addresses'], size=5000, verbose=verbose, highlights=['addresses'])
def get_match_name(year, x, verbose=False):
    return get_info(year, x, ['names'], size=200, verbose=verbose, highlights=['names'])
def get_match_acronym(year, x, verbose=False):
    return get_info(year, x, ['acronyms'], size=5000, verbose=False, highlights=['acronyms'])
def get_match_supervisors_name(year, x, verbose=False):
    return get_info(year, x, ['supervisors_name'], size=10000, verbose=False, highlights=['supervisors_name'])
def get_match_supervisors_id(year, x, verbose=False):
    return get_info(year, x, ['supervisors_id'], size=2000, verbose=False, highlights=['supervisors_id'])
def get_match_supervisors_acronym(year, x, verbose=False):
    return get_info(year, x, ['supervisors_acronym'], size=2000, verbose=False, highlights=['supervisors_acronym'])

def get_info(year, input_str, search_fields, size=20, verbose=False, highlights=[], fuzzy_ok=False):
    if input_str is None:
        input_str = ""
    myIndex = "index-rnsr-{}".format(year)
    s = Search(using=es, index=myIndex)
    for f in highlights:
        s = s.highlight(f)

    if search_fields==['names']:
        s = s.query("multi_match", query=input_str,
                minimum_should_match=1,
                fuzziness="auto",
                fields=search_fields)
    else:
        s = s.query("multi_match", query=input_str,
                    minimum_should_match=1,
                    fields=search_fields)
    s = s[0:size]
    res = s.execute()
    hits = res.hits

    if len(hits) == 0 and fuzzy_ok:
        if verbose:
            print("fuzzy {}".format(search_fields))
        s = Search(using=es, index=myIndex)
        for f in highlights:
            s = s.highlight(f)
        s = s.query("multi_match", query=input_str,
                   fuzziness=1,
                    fields=search_fields)
        s = s[0:size]
        res = s.execute()
        hits = res.hits


    id_res=""
    if len(hits)>0:
        max_score = hits[0].meta.score


    res_ids = []
    scores = []
    highlights={}
    nb_matches = {}
    matches_frag = {}

    for hit in hits:

        if search_fields==['names'] and hit.meta.score < hits.max_score*0.5:
            continue

        res_ids.append(hit.id)
        scores.append(hit.meta.score)
        highlights[hit.id]=[]


        for matching_field in hit.meta.highlight:
            for fragment in hit.meta.highlight[matching_field]:
                highlights[hit.id].append(fragment)

                matches = [normalize_for_count(e.get_text(), matching_field) for e in BeautifulSoup(fragment, 'lxml').find_all('em')]


                if hit.id not in nb_matches:
                    nb_matches[hit.id] = 0
                    matches_frag[hit.id] = []
                matches_frag[hit.id] += matches
                matches_frag[hit.id] = list(set(matches_frag[hit.id]))
                nb_matches[hit.id] = len(matches_frag[hit.id])



    #print(scores)
    return {'ids': res_ids, 'highlights': highlights, 'nb_matches': nb_matches}

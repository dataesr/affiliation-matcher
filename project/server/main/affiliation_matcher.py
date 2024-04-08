from project.server.main.logger import get_logger
from project.server.main.match_country import match_country
from project.server.main.match_grid import match_grid
from project.server.main.match_rnsr import match_rnsr
from project.server.main.match_ror import match_ror
from project.server.main.match_paysage import match_paysage
from project.server.main.my_elastic import MyElastic
from project.server.main.utils import chunks

logger = get_logger(__name__)
client = MyElastic()
use_cache = False


def check_matcher_health() -> bool:
    try:
        res = match_country(conditions={'query': 'france'})
        logger.debug(res)
        assert('fr' in res['results'])
        logger.debug('Matcher seems healthy')
        return True
    except:
        logger.debug('Matcher does not seem loaded, lets load it')
        return False


def get_query_from_affiliation(affiliation):
    query_elts = []
    keys = list(affiliation.keys())
    keys.sort()
    for f in affiliation:
        if f.lower() in ['name', 'ror', 'grid', 'rnsr', 'paysage', 'country', 'city']:
            if isinstance(affiliation.get(f), str) and affiliation[f]:
                query_elts.append(affiliation[f])
    return ' '.join(query_elts)


def get_country(affiliation):
    in_cache = False
    params = {
        "size": 1,
        "query": {
            "term": {
                "affiliation.keyword": affiliation
            }
        }
    }
    hits_in_cache = []
    if use_cache:
        try:
            r = client.search(index='bso-cache-country', body=params)
            hits_in_cache = r['hits']['hits']
        except:
            logger.debug("error in search in bso-cache-country")
    if len(hits_in_cache) >= 1:
        in_cache = True
        countries = hits_in_cache[0]['_source']['countries']
    else:
        countries = match_country(conditions={'query': affiliation})['results']
    return {'countries': countries, 'in_cache': in_cache}


def get_matches(affiliation, match_types):
    results = []
    other_ids = []
    if 'country' in match_types:
        countries = match_country(conditions={'query': affiliation})
        results += [{'id': e, 'type': 'country'} for e in countries['results']]
    if 'grid' in match_types:
        grids = match_grid(conditions={'query': affiliation})
        results += [{'id': e, 'type': 'grid'} for e in grids['results']]
        if 'other_ids' in grids:
            other_ids += grids['other_ids']
    if 'rnsr' in match_types:
        rnsrs = match_rnsr(conditions={'query': affiliation})
        results += [{'id': e, 'type': 'rnsr'} for e in rnsrs['results']]
        if 'other_ids' in rnsrs:
            other_ids += rnsrs['other_ids']
    if 'ror' in match_types:
        rors = match_ror(conditions={'query': affiliation})
        results += [{'id': e, 'type': 'country'} for e in rors['results']]
    if 'paysage' in match_types:
        paysages = match_paysage(conditions={'query': affiliation})
        results += [{'id': e, 'type': 'paysage'} for e in paysages['results']]
    for r in other_ids:
        if r['type'] in ['siren', 'sirene', 'siret'] and r not in results:
            results.append(r)
    return results


def is_na(x):
    return not(not x)


def enrich_and_filter_publications_by_country(publications: list, countries_to_keep: list = None) -> dict:
    logger.debug(f'Filter {len(publications)} publication against {",".join(countries_to_keep)} countries.')
    if countries_to_keep is None:
        countries_to_keep = []
    field_name = 'detected_countries'
    # Retrieve all affiliations
    all_affiliations = []
    for publication in publications:
        affiliations = publication.get('affiliations', [])
        affiliations = [] if affiliations is None else affiliations
        all_affiliations += [get_query_from_affiliation(affiliation) for affiliation in affiliations]
        authors = publication.get('authors', [])
        for author in authors:
            affiliations = author.get('affiliations', [])
            affiliations = [] if affiliations is None else affiliations
            all_affiliations += [get_query_from_affiliation(affiliation) for affiliation in affiliations]
    logger.debug(f'Found {len(all_affiliations)} affiliations in total.')
    # Deduplicate affiliations
    all_affiliations_list = list(filter(is_na, list(set(all_affiliations))))
    logger.debug(f'Found {len(all_affiliations_list)} different affiliations in total.')
    # Transform list into dict
    all_affiliations_dict = {}
    # Retrieve countries for all publications
    assert(check_matcher_health())
    for all_affiliations_list_chunk in chunks(all_affiliations_list, 1000):
        for affiliation in all_affiliations_list_chunk:
            all_affiliations_dict[affiliation] = get_country(affiliation)
        logger.debug(f'{len(all_affiliations_dict)} / {len(all_affiliations_list)} treated in country_matcher')
        if use_cache:
            logger.debug('Loading in cache')
            cache = []
            for ix, affiliation in enumerate(all_affiliations_list_chunk):
                if affiliation in all_affiliations_dict and all_affiliations_dict[affiliation]['in_cache'] is False:
                    cache.append({'_index': 'bso-cache-country', 'affiliation': affiliation,
                                  'countries': all_affiliations_dict[affiliation]['countries']})
            client.parallel_bulk(actions=cache)
    logger.debug('All countries of all affiliations have been retrieved.')
    # Map countries with affiliations
    for publication in publications:
        countries_by_publication = []
        affiliations = publication.get('affiliations', [])
        affiliations = [] if affiliations is None else affiliations
        for affiliation in affiliations:
            query = get_query_from_affiliation(affiliation)
            if query in all_affiliations_dict:
                countries = all_affiliations_dict[query]['countries']
                affiliation[field_name] = countries
                countries_by_publication += countries
        authors = publication.get('authors', [])
        for author in authors:
            affiliations = author.get('affiliations', [])
            for affiliation in affiliations:
                query = get_query_from_affiliation(affiliation)
                if query in all_affiliations_dict:
                    countries = all_affiliations_dict[query]['countries']
                    affiliation[field_name] = countries
                    countries_by_publication += countries
        publication[field_name] = list(set(countries_by_publication))
    if not countries_to_keep:
        filtered_publications = publications
    else:
        countries_to_keep_set = set(countries_to_keep)
        filtered_publications = [publication for publication in publications
                                 if len(set(publication[field_name]).intersection(countries_to_keep_set)) > 0]
    logger.debug(f'After filtering by countries, {len(filtered_publications)} publications have been kept.')
    return {'publications': publications, 'filtered_publications': filtered_publications}

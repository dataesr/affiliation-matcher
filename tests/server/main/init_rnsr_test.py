from matcher.server.main.config import SCANR_DUMP_URL
from matcher.server.main.init_rnsr import get_es_rnsr


def test_get_es_rnsr(requests_mock) -> None:
    url = SCANR_DUMP_URL
    data = [
        {'id': '1'},
        {'id': '000000000B', 'label': {'default': 'label_01'}, 'alias': ['alias_01'], 'acronym':
            {'default': 'acronym_01'}},
        {'id': '000000000C', 'externalIds': [{'id': 'code_01', 'type': 'another_type'},
                                             {'id': 'code_02', 'type': 'label_numero'}]},
        {'id': '000000000D', 'institutions': [{'structure': 'supervisor_01'}], 'externalIds': [{'id': 'siren_12345', 'type': 'siren'}]},
        {'id': '000000000E'}
    ]
    requests_mock.get(url=url, json=data)
    rnsrs = get_es_rnsr()
    assert len(rnsrs) == 4
    names = rnsrs[0]['names']
    names.sort()
    assert names == ['alias_01', 'label_01']
    assert rnsrs[0]['acronyms'] == ['acronym_01']
    assert rnsrs[1]['code_numbers'] == ['code_02']
    supervisors_ids = rnsrs[2]['supervisors_id']
    supervisors_ids.sort()
    assert supervisors_ids == ['siren_123', 'supervisor_01']

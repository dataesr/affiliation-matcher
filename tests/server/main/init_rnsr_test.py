import pytest

from matcher.server.main.config import SCANR_DUMP_URL
from matcher.server.main.init_rnsr import init_rnsr
from matcher.server.main.my_elastic import MyElastic


class TestInitRnsr:
    @pytest.fixture(scope='class')
    def setup(self) -> None:
        es = MyElastic()
        yield {'es': es}
        es.delete_index(index='rnsr-name')
        es.delete_index(index='rnsr-supervisor_acronym')
        es.delete_index(index='rnsr-acronym')
        es.delete_index(index='rnsr-supervisor_name')
        es.delete_index(index='rnsr-city')
        es.delete_index(index='rnsr-code_number')

    def test_get_es_rnsr(self, setup, requests_mock) -> None:
        url = SCANR_DUMP_URL
        data = [
            {'id': 'id_01',
             'externalIds': [{'type': 'other-type'}], 'address': [{'city': 'city_01'}]},
            {'id': 'id_02',
             'externalIds': [{'type': 'rnsr'}], 'address': [{'city': 'city_02'}],
             'label': {'default': 'label_01'}},
            {'id': 'id_03',
             'externalIds': [{'type': 'rnsr'}], 'address': [{'city': 'city_03'}],
             'label': {'default': 'label_02'}},
            {'id': 'id_04',
             'externalIds': [{'type': 'rnsr'}], 'address': [{'city': 'city_03'}],
             'label': {'default': 'label_03'}}
        ]
        requests_mock.get(url=url, json=data)
        init_rnsr()
        es = setup['es']
        cities = es.count(index='rnsr-city')
        assert cities['count'] == 2
        names = es.count(index='rnsr-name')
        assert names['count'] == 3

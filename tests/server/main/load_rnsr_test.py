import pytest

from matcher.server.main.config import SCANR_DUMP_URL
from matcher.server.main.load_rnsr import load_rnsr
from matcher.server.main.my_elastic import MyElastic


class TestLoadRnsr:
    @pytest.fixture(scope='class')
    def setup(self) -> None:
        es = MyElastic()
        yield {'es': es}
        es.delete_index(index='test_rnsr_name')
        es.delete_index(index='test_rnsr_supervisor_acronym')
        es.delete_index(index='test_rnsr_acronym')
        es.delete_index(index='test_rnsr_supervisor_name')
        es.delete_index(index='test_rnsr_city')
        es.delete_index(index='test_rnsr_code_number')

    def test_load_rnsr(self, setup, requests_mock) -> None:
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
        load_rnsr('test')
        es = setup['es']
        cities = es.count(index='test_rnsr_city')
        assert cities['count'] == 2
        names = es.count(index='test_rnsr_name')
        assert names['count'] == 3

import pytest

from project.server.main.config import SCANR_DUMP_URL
from project.server.main.load_rnsr import load_rnsr
from project.server.main.my_elastic import MyElastic


class TestLoadRnsr:
    @pytest.fixture(scope='class')
    def setup(self) -> None:
        es = MyElastic()
        yield {'es': es}
        es.delete_index(index='test_rnsr_*')

    def test_load_rnsr(self, setup, requests_mock) -> None:
        requests_mock.real_http = True
        data = [
            {
                'id': 'id_01',
                'externalIds': [{'type': 'other-type'}],
                'city': ['city_01']
            }, {
                'id': 'id_02',
                'externalIds': [{'type': 'rnsr', 'id': 'rnsr_id_02'}],
                'acronym': {'fr': 'acronym_02', 'en': 'acronym_02'},
                'label': {'fr': 'This is a really complex label', 'en': 'This is a really complex label'},
                'address': [{'city': 'city_02'}],
                'institutions': [{'structure': 'structure_02'}]
            }, {
                'id': 'id_03',
                'externalIds': [{'type': 'rnsr', 'id': 'rnsr_id_03'}],
                'label': {'fr': 'This is a more than complex label', 'en': 'This is a more than complex label'},
                'address': [{'city': 'city_03'}]
            }, {
                'id': 'id_04',
                'externalIds': [{'type': 'rnsr', 'id': 'rnsr_id_04'}],
                'label': {'fr': 'This is a another complex label', 'en': 'This is a another complex label'},
                'address': [{'city': 'city_03'}]
            }
        ]
        requests_mock.get(url=SCANR_DUMP_URL, json=data)
        load_rnsr(index_prefix='test')
        es = setup['es']
        cities = es.count(index='test_rnsr_city')
        assert cities['count'] == 2
        names = es.count(index='test_rnsr_name')
        assert names['count'] == 3

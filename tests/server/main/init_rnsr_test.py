import json

from matcher.server.main.init_rnsr import get_es_rnsr


def test_get_es_rnsr(requests_mock) -> None:
    url = 'http://185.161.45.213/organizations/organizations/?where=%7B%22rnsr%22:%7B%22$exists%22:true%7D%7D' \
          '&max_results=500&projection=%7B%22active%22:1,%22alias%22:1,%22names%22:1,%22id%22:1,%22' \
          'code_numbers%22:1,%22supervisors%22:1,%22addresses%22:1,%22dates%22:1,%22sirene%22:1%7D&page={page}'
    data = [
        {'id': 0, 'dates': [{'start_date': '2013', 'end_date': '2013'}, {'start_date': '2020'}]},
        {'id': 1, 'dates': [{'start_date': '2018'}], 'names': [{'name_fr': 'french_name_01',
                                                                'name_en': 'english_name_01'},
                                                               {'name_fr': 'french_name_02'},
                                                               {'name_en': 'english_name_02'}, {}]},
        {'id': 2, 'names': [{'acronym_fr': 'french_acronym_01', 'acronym_en': 'english_acronym_01'},
                            {'acronym_fr': 'french_acronym_02'}, {'acronym_en': 'english_acronym_02'}, {}]},
        {'id': 3, 'code_numbers': ['code 01', 'code 02'], 'sirene': 'sirene_01'},
        {'id': 4, 'supervisors': [{'id': 'supervisor_01', 'name': 'supervisor_name_01'}, {'id': 'supervisor_02'}]}
    ]
    requests_mock.get(url.format(page=1), text='{{"meta": {{"total": 12}}, "data": {data}}}'.format(
        data=json.dumps(data)))
    requests_mock.get(url.format(page=2), text='{{"meta": {{"total": 12}}, "data": {data}}}'.format(data=[]))
    data_supervisor_01 = {'names': [{'name_fr': 'supervisor_name_fr_01', 'name_en': 'supervisor_name_en_01'},
                                    {'name_fr': 'supervisor_name_fr_02'}, {'acronym_fr': 'supervisor_acronym_fr_01'}],
                          'addresses': [{'city': 'supervisor_city_01'}, {}]}
    requests_mock.get('http://185.161.45.213/organizations/organizations/supervisor_01',
                      text='{data}'.format(data=json.dumps(data_supervisor_01)))
    requests_mock.get('http://185.161.45.213/organizations/organizations/supervisor_02', text='{"data": []}')
    requests_mock.get('http://185.161.45.213/organizations/organizations/sirene_01', text='{"data": []}')
    rnsr = get_es_rnsr()
    assert len(rnsr.keys()) == 11
    assert set(list(rnsr.keys())) == {2016, 2017, 2018, 2019, 2020, 'all', 2011, 2012, 2013, 2014, 2015}
    assert len(rnsr.get(2016, [])) == 0
    assert len(rnsr.get(2017, [])) == 0
    assert len(rnsr.get(2018, [])) == 1
    assert len(rnsr.get(2019, [])) == 1
    assert len(rnsr.get(2020, [])) == 2
    assert len(rnsr.get('all', [])) == 5
    assert len(rnsr.get(2011, [])) == 0
    assert len(rnsr.get(2012, [])) == 0
    assert len(rnsr.get(2013, [])) == 1
    assert len(rnsr.get(2014, [])) == 0
    assert len(rnsr.get(2015, [])) == 0
    element_1 = list(filter(lambda x: x.get('id') == 1, rnsr.get('all', [])))[0]
    element_2 = list(filter(lambda x: x.get('id') == 2, rnsr.get('all', [])))[0]
    element_3 = list(filter(lambda x: x.get('id') == 3, rnsr.get('all', [])))[0]
    element_4 = list(filter(lambda x: x.get('id') == 4, rnsr.get('all', [])))[0]
    assert sorted(element_1.get('names')) == ['english_name_01', 'english_name_02', 'french_name_01',
                                              'french_name_02']
    assert element_2.get('names') == []
    assert element_1.get('acronyms') == []
    assert sorted(element_2.get('acronyms')) == ['english_acronym_01', 'english_acronym_02', 'french_acronym_01',
                                                 'french_acronym_02']
    assert element_3.get('names') == []
    assert element_3.get('acronyms') == []
    assert element_1.get('code_numbers') == []
    assert element_2.get('code_numbers') == []
    assert element_3.get('code_numbers') == ['code 01', 'code01', 'code-01', 'code_01', 'code 02', 'code02', 'code-02',
                                             'code_02']
    assert element_1.get('supervisors_id') == []
    assert element_3.get('supervisors_id') == ['sirene_01']
    assert element_4.get('supervisors_id') == ['supervisor_01', 'supervisor_02']
    assert sorted(element_4.get('supervisors_name')) == ['supervisor_name_01', 'supervisor_name_en_01',
                                                         'supervisor_name_fr_01', 'supervisor_name_fr_02']
    assert element_4.get('supervisors_acronym') == ['supervisor_acronym_fr_01']
    assert element_4.get('supervisors_city') == ['supervisor_city_01']

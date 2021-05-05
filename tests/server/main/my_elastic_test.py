from matcher.server.main.myelastic import MyElastic


class TestMyElastic:
    def test_constructor(self) -> None:
        es = MyElastic()
        assert type(es) == MyElastic

    def test_create_index(self) -> None:
        index = 'index_test_creation'
        es = MyElastic()
        indices = es.indices.get_alias('*').keys()
        assert len(indices) == 0
        es.create_index(index=index)
        indices = es.indices.get_alias('*').keys()
        assert len(indices) == 1
        assert index in indices
        es.delete_index(index=index)

    def test_delete_index(self) -> None:
        index = 'index_test_deletion'
        es = MyElastic()
        es.create_index(index=index)
        indices = es.indices.get_alias('*').keys()
        assert len(indices) == 1
        es.delete_index(index=index)
        indices = es.indices.get_alias('*').keys()
        assert len(indices) == 0
        es.delete_index(index=index)

    def test_my_index(self) -> None:
        index = 'index_test_indexation'
        es = MyElastic()
        body = {'key_01': 'value_01', 'key_02': 'value_02'}
        es.my_index(index=index, id='12', body=body)
        es.my_index(index=index, id='13', body=body)
        count = es.count(index=index)['count']
        assert count == 2
        es.delete_index(index=index)

    def test_my_search(self) -> None:
        index = 'index_test_search'
        es = MyElastic()
        body = {'key_01': 'value_01', 'key_02': 'value_02'}
        es.my_index(index=index, id='12', body=body)
        es.my_index(index=index, id='13', body=body)
        es.my_index(index=index, id='14', body=body)
        hits = es.search(index=index)['hits']['hits']
        assert len(hits) == 3
        es.delete_index(index=index)

    def test_delete_by_query(self) -> None:
        index = 'index_test_search'
        es = MyElastic()
        body = {'key_01': 'value_01', 'key_02': 'value_02'}
        es.my_index(index=index, id='12', body=body)
        es.my_index(index=index, id='13', body=body)
        es.my_index(index=index, id='14', body=body)
        es.my_index(index=index, id='15', body=body)
        hits = es.search(index=index)['hits']['hits']
        assert len(hits) == 4
        es.my_delete_by_query(index=index)
        hits = es.search(index=index)['hits']['hits']
        assert len(hits) == 0
        es.delete_index(index=index)

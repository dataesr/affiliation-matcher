from project.server.main.my_elastic import MyElastic


class TestMyElastic:
    def test_constructor(self) -> None:
        es = MyElastic()
        assert type(es) == MyElastic

    def test_create_index(self) -> None:
        index = 'create'
        es = MyElastic()
        indices = es.indices.get_alias('*').keys()
        assert len(indices) == 0
        es.create_index(index=index)
        indices = es.indices.get_alias('*').keys()
        assert len(indices) == 1
        assert index in indices
        es.delete_index(index=index)

    def test_delete_index(self) -> None:
        index = 'delete'
        es = MyElastic()
        es.create_index(index=index)
        indices = es.indices.get_alias('*').keys()
        assert len(indices) == 1
        es.delete_index(index=index)
        indices = es.indices.get_alias('*').keys()
        assert len(indices) == 0
        es.delete_index(index=index)

    def test_delete_all_by_query(self) -> None:
        index = 'delete_all'
        es = MyElastic()
        es.create_index(index=index)
        es.index(index=index, body={'key': 'value_01'}, refresh=True)
        es.index(index=index, body={'key': 'value_02'}, refresh=True)
        hits = es.search(index=index)['hits']['hits']
        assert len(hits) == 2
        es.delete_all_by_query(index=index)
        hits = es.search(index=index)['hits']['hits']
        assert len(hits) == 0
        es.delete_index(index=index)

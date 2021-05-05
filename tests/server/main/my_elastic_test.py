from matcher.server.main.my_elastic import MyElastic


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

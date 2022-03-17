from project.server.main.elastic_utils import get_index_name


class TestElasticUtils:
    def test_get_index_name(self) -> None:
        result_without_prefix = get_index_name(index_name='index', source='source')
        assert result_without_prefix == 'source_index'
        result_with_prefix = get_index_name(index_name='index', source='source', index_prefix='test')
        assert result_with_prefix == 'test_source_index'

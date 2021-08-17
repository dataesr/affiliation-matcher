import pytest

from matcher.server.main.matcher import filter_submatching_results


class TestMatcher:
    @pytest.mark.parametrize(
        'highlights,results,expected_results', [
            ({'us': {'grid_city': ['<em>Paris</em>', '<em>Philadelphia</em>']},
              'fr': {'grid_city': ['<em>Paris</em>']}}, ['us', 'fr'], ['us']),
            ({'us': {'grid_name': ['<em>Cambridge Public School</em>', '<em>Cambridge School</em>']},
              'pt': {'grid_name': ['<em>Cambridge School</em>']}}, ['us', 'pt'], ['us'])
        ])
    def test_filter_submatching_results(self, highlights, results, expected_results) -> None:
        res = {'highlights': highlights, 'logs': '', 'results': results}
        results = filter_submatching_results(res=res)
        assert len(results['results']) == len(expected_results)
        assert results['results'][0] == expected_results[0]

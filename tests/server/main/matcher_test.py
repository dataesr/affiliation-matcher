import pytest

from matcher.server.main.matcher import filter_submatching_results


class TestMatcher:
    @pytest.mark.parametrize(
        'highlights,results,expected_results', [
            ({'us': {'grid_name': ['<em>Cambridge University</em>', '<em>Medical Cambridge University</em>']},
              'pt': {'grid_name': ['<em>Cambridge University</em>']}},
             ['us', 'pt'], ['us']),
            ({'us': {'grid_name': ['<em>Cambridge University</em>']},
              'pt': {'grid_name': ['<em>Cambridge University</em>', '<em>Medical Cambridge University</em>']}},
             ['us', 'pt'], ['pt']),
            ({'us': {'grid_name': ['<em>Cambridge University</em>', '<em>Medical Cambridge University</em>']},
              'pt': {'grid_name': ['<em>Cambridge University</em>', '<em>University of Porto</em>']}},
             ['us', 'pt'], ['us', 'pt']),
            ({'us': {'grid_city': ['<em>Paris</em>', '<em>Philadelphia</em>']},
              'fr': {'grid_city': ['<em>Paris</em>']}}, ['us', 'fr'], ['us', 'fr']),
            ({'us': {'grid_city': ['<em>Paris</em>']},
              'fr': {'grid_city': ['<em>Paris</em>', '<em>Philadelphia</em>']}}, ['us', 'fr'], ['us', 'fr'])
        ])
    def test_filter_submatching_results(self, highlights, results, expected_results) -> None:
        res = {'highlights': highlights, 'logs': '', 'results': results}
        results = filter_submatching_results(res=res)
        assert len(results['results']) == len(expected_results)
        assert results['results'][0] == expected_results[0]

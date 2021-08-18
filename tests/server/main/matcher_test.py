import pytest

from matcher.server.main.matcher import filter_submatching_results


class TestMatcher:
    @pytest.mark.parametrize(
        'highlights,results,expected_results', [
            ({'grid.1': {'grid_name': ['<em>Medical</em> <em>Cambridge</em> <em>University</em>'], 'grid_country': ['<em>United</em> <em>Kingdom</em>']},
              'grid.2': {'grid_name': ['<em>Cambridge</em> <em>University</em>'], 'grid_country': ['<em>United</em> <em>Kingdom</em>']},
              'grid.3': {'grid_name': ['<em>Cambridge</em> <em>University</em>'], 'grid_country': ['<em>United</em> <em>States</em>']},
              },
             ['grid.1', 'grid.2', 'grid.3'], ['grid.1', 'grid.3']),
            ({'us': {'grid_city': ['<em>Paris</em>', '<em>Philadelphia</em>'], 'grid_name': ['<em>University</em> of <em>Philadelphia</em>']},
              'fr': {'grid_city': ['<em>Paris</em>'], 'grid_name': ['<em>University</em> of <em>Paris</em>']}},
             ['us', 'fr'], ['us', 'fr']),
            # Cas limite
            ({'us': {'grid_city': ['<em>New</em>', '<em>York</em>'],
                     'grid_name': ['<em>University</em> of <em>New</em> <em>York</em>']},
              'uk': {'grid_city': ['<em>York</em>'], 'grid_name': ['<em>University</em> of <em>York</em>']}},
             ['us', 'uk'], ['us'])
        ])
    def test_filter_submatching_results(self, highlights, results, expected_results) -> None:
        res = {'highlights': highlights, 'logs': '', 'results': results}
        results = filter_submatching_results(res=res)
        assert len(results['results']) == len(expected_results)
        assert results['results'][0] == expected_results[0]

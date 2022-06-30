import pytest

from project.server.main.matcher import filter_submatching_results_by_all, filter_submatching_results_by_criterion


class TestMatcher:
    @pytest.mark.parametrize(
        'highlights,results,expected_results', [
            ({
                'grid_name;grid_country': {
                    'grid.1': {
                        'grid_name': ['<em>Medical</em> <em>Cambridge</em> <em>University</em>'],
                        'grid_country': ['<em>United</em> <em>Kingdom</em>']
                    },
                    'grid.2': {
                        'grid_name': ['<em>Cambridge</em> <em>University</em>'],
                        'grid_country': ['<em>United</em> <em>Kingdom</em>']
                    },
                    'grid.3': {
                        'grid_name': ['<em>Cambridge</em> <em>University</em>'],
                        'grid_country': ['<em>United</em> <em>States</em>']
                    }
                }
            },
             ['grid.1', 'grid.2', 'grid.3'], ['grid.1', 'grid.3']),
            ({
                'grid_city;grid_name': {
                    'us': {
                        'grid_city': ['<em>Paris</em>', '<em>Philadelphia</em>'],
                        'grid_name': ['<em>University</em> of <em>Philadelphia</em>']
                    },
                    'fr': {
                        'grid_city': ['<em>Paris</em>'],
                        'grid_name': ['<em>University</em> of <em>Paris</em>']
                    }
                }
            },
             ['us', 'fr'], ['us', 'fr']),
            ({
                'grid_city': {
                    'us': {
                        'grid_city': [['Tour Mirabeau <em>Paris</em>']]
                    },
                    'fr': {
                        'grid_city': [['Tour Mirabeau <em>Paris</em>']]
                    },
                    'ca': {
                        'grid_city': [['Tour Mirabeau <em>Paris</em>']]
                    }
                }
            },
             ['us', 'fr', 'ca'], ['us', 'fr', 'ca']),
            # Edge cases
            ({
                'grid_city;grid_name': {
                    'us': {
                        'grid_city': ['<em>New</em>', '<em>York</em>'],
                        'grid_name': ['<em>University</em> of <em>New</em> <em>York</em>']
                    },
                    'uk': {
                        'grid_city': ['<em>York</em>'],
                        'grid_name': ['<em>University</em> of <em>York</em>']
                    }
                }
            },
             ['us', 'uk'], ['us'])
        ])
    def test_filter_submatching_results_by_criterion(self, highlights, results, expected_results) -> None:
        res = {'highlights': highlights, 'logs': '', 'results': results}
        results = filter_submatching_results_by_criterion(res=res)
        assert len(results['results']) == len(expected_results)
        assert results['results'][0] == expected_results[0]

    @pytest.mark.parametrize(
        'highlights,results,expected_results', [
            ({
                'grid_name;grid_city;grid_country': {
                    'grid.1': {
                        'grid_name': [['<em>Paris</em> <em>University</em>']],
                        'grid_city': [['<em>Paris</em>']],
                        'grid_country': [['<em>France</em>']]
                    },
                    'grid.2': {
                        'grid_name': [['<em>Sorbonne</em> <em>University</em>']],
                        'grid_city': [['<em>Paris</em>']],
                        'grid_country': [['<em>France</em>']]
                    }
                }
            },
             ['grid.1', 'grid.2'], ['grid.2'])
        ])
    def test_filter_submatching_results_by_all(self, highlights, results, expected_results) -> None:
        res = {'highlights': highlights, 'logs': '', 'results': results}
        results2 = filter_submatching_results_by_all(res=res)
        assert len(results2['results']) == len(expected_results)
        assert results2['results'][0] == expected_results[0]

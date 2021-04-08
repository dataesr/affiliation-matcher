import pytest

from project.server.main.init_rnsr import strip_accents, delete_punctuation, normalize_text, normalize, normalize_for_count


@pytest.mark.parametrize('text,expected_stripped_text', [
    ('guivarc’h', 'guivarc h'),
    ('énervant', 'enervant'),
    ('agaçant', 'agacant')
])
def test_strip_accents(text: str, expected_stripped_text: str) -> None:
    result = strip_accents(text)
    assert result == expected_stripped_text


@pytest.mark.parametrize('text,expected_without_punctuation_text', [
    ('with.dot', 'with dot'),
    ('no,comma', 'no comma'),
    ('UPPERCASE', 'uppercase')
])
def test_delete_punctuation(text: str, expected_without_punctuation_text: str) -> None:
    result = delete_punctuation(text)
    assert result == expected_without_punctuation_text


@pytest.mark.parametrize('text,expected_normalized_text', [
    ('before\xa0after', 'before after'),
    ('multiple    spaces', 'multiple spaces')
])
def test_normalize_text(text: str, expected_normalized_text: str) -> None:
    result = normalize_text(text)
    assert result == expected_normalized_text


@pytest.mark.parametrize('text,expected_normalized_text', [
    ('single-dash', 'single dash'),
    ('here-are-multiple-dashes', 'here are multiple dashes'),
    ('multiple    spaces', 'multiple spaces'),
    ('UPPERCASE', 'uppercase')
])
def test_normalize(text: str, expected_normalized_text: str) -> None:
    result = normalize(text)
    assert result == expected_normalized_text


@pytest.mark.parametrize('text,expected_normalized_text', [
    ('this is a long long text', 'this i')
])
def test_normalize_for_count(text: str, expected_normalized_text: str) -> None:
    result = normalize_for_count(text)
    assert result == expected_normalized_text

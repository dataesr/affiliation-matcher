import pytest

from matcher.server.main.strings import delete_punctuation, normalize_text, strip_accents


class TestStrings:
    @pytest.mark.parametrize('text,text_without_punctuation', [
        ('with.dot', 'with dot'),
        ('no,comma', 'no comma'),
        ('UPPERCASE', 'uppercase')
    ])
    def test_delete_punctuation(self, text: str, text_without_punctuation: str) -> None:
        result = delete_punctuation(text)
        assert result == text_without_punctuation

    @pytest.mark.parametrize('text,normalized_text', [
        ('before\xa0after', 'before after'),
        ('multiple      spaces', 'multiple spaces'),
        ('multiple\n\nlines', 'multiple lines'),
        ('multi-dashed-text', 'multi dashed text'),
    ])
    def test_normalize_text(self, text: str, normalized_text: str) -> None:
        result = normalize_text(text, remove_separator=False)
        assert result == normalized_text

    @pytest.mark.parametrize('text,stripped_text', [
        ('guivarc’h', 'guivarc h'),
        ('énervant', 'enervant'),
        ('agaçant', 'agacant')
    ])
    def test_strip_accents(self, text: str, stripped_text: str) -> None:
        result = strip_accents(text)
        assert result == stripped_text

import pytest

from project.server.main.utils import delete_punctuation, get_common_words, has_a_digit, \
    normalize_text, remove_ref_index, strip_accents


class TestUtils:
    @pytest.mark.parametrize('text,stripped_text', [
        ('guivarc’h', 'guivarc h'),
        ('énervant', 'enervant'),
        ('agaçant', 'agacant')
    ])
    def test_strip_accents(self, text: str, stripped_text: str) -> None:
        result = strip_accents(text)
        assert result == stripped_text

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

    @pytest.mark.parametrize('text,test_has_a_digit_text', [
        ('no_digit_at_all', False),
        ('0test', True)
    ])
    def test_has_a_digit(self, text: str, test_has_a_digit_text: bool) -> None:
        result = has_a_digit(text=text)
        assert result is test_has_a_digit_text

    @pytest.mark.parametrize('objects,field,split,threshold,common_words', [
        ([{'field': ['word_01', 'word_02']}], 'field', True, 2, ['word']),
        # If occurrences < threshold, nothing is returned
        ([{'field': ['word_01', 'word_02']}], 'field', True, 3, []),
        # If field does not exist, nothing is returned
        ([{'field': ['word_01', 'word_02']}], 'another_field', True, 2, []),
        # If split is False, text will remain as it is
        ([{'field': ['word_01', 'word_02', 'word_02']}], 'field', False, 2, ['word 02'])
    ])
    def test_get_common_words(self, objects: list, field: str, split: bool, threshold: int, common_words: list) -> None:
        result = get_common_words(objects=objects, field=field, split=split, threshold=threshold)
        assert result == common_words

    @pytest.mark.parametrize('text,clean_text', [
        ('example', 'example'),
        ('1example and another text so on', 'example and another text so on'),
        ('12example and another text so on', 'example and another text so on'),
        ('123example and another text so on', '123example and another text so on'),
        ('exam58ple and another text so on', 'exam58ple and another text so on'),
        ('12 example and another text so on', '12 example and another text so on')
    ])
    def test_remove_ref_index(self, text, clean_text) -> None:
        result = remove_ref_index(query=text)
        assert result == clean_text

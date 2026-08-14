from chinese_learning.domain.learner.word_status import WordStatus


def test_word_status_contains_expected_values():
    assert WordStatus.NEW.value == "new"
    assert WordStatus.LEARNING.value == "learning"
    assert WordStatus.KNOWN.value == "known"

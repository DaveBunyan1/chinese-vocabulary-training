from pytest import raises

from chinese_learning.domain.learner.vocabulary_knowledge import VocabularyKnowledge
from chinese_learning.domain.learner.word_status import WordStatus
from chinese_learning.domain.vocabulary.vocabulary_item import (
    VocabularyId,
    VocabularyItem,
)


def create_vocabulary_item() -> VocabularyItem:
    return VocabularyItem(
        id=VocabularyId("1"),
        text="今天",
        pinyin="jīn tiān",
        meaning="today",
    )


def test_vocabulary_knowledge_stores_vocabulary_item():
    vocabulary = create_vocabulary_item()

    knowledge = VocabularyKnowledge(
        vocabulary=vocabulary,
        status=WordStatus.NEW,
    )

    assert knowledge.vocabulary == vocabulary


def test_vocabulary_knowledge_stores_status():
    knowledge = VocabularyKnowledge(
        vocabulary=create_vocabulary_item(),
        status=WordStatus.KNOWN,
    )

    assert knowledge.status == WordStatus.KNOWN


def test_vocabulary_knowledge_is_immutable():
    knowledge = VocabularyKnowledge(
        vocabulary=create_vocabulary_item(),
        status=WordStatus.NEW,
    )

    with raises(AttributeError):
        knowledge.status = WordStatus.KNOWN  # type: ignore

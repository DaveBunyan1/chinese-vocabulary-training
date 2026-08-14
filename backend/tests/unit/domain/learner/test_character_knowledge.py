from pytest import raises

from chinese_learning.domain.learner.character_knowledge import CharacterKnowledge
from chinese_learning.domain.learner.word_status import WordStatus
from chinese_learning.domain.text_analysis.character import Character


def test_character_knowledge_stores_character():
    character = Character("天")

    knowledge = CharacterKnowledge(
        character=character,
        status=WordStatus.NEW,
    )

    assert knowledge.character == character


def test_character_knowledge_stores_status():
    knowledge = CharacterKnowledge(
        character=Character("天"),
        status=WordStatus.KNOWN,
    )

    assert knowledge.status == WordStatus.KNOWN


def test_character_knowledge_is_immutable():
    knowledge = CharacterKnowledge(
        character=Character("天"),
        status=WordStatus.NEW,
    )

    with raises(AttributeError):
        knowledge.status = WordStatus.KNOWN  # type: ignore

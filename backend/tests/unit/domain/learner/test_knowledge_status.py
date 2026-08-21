from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus


def test_knowledge_status_contains_expected_values():
    assert KnowledgeStatus.NEW.value == "new"
    assert KnowledgeStatus.LEARNING.value == "learning"
    assert KnowledgeStatus.KNOWN.value == "known"

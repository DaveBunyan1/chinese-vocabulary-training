from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.character_knowledge import CharacterKnowledge
from chinese_learning.domain.learner.vocabulary_knowledge import VocabularyKnowledge
from chinese_learning.domain.text_analysis.character import Character
from chinese_learning.domain.vocabulary.vocabulary_item import VocabularyId
from chinese_learning.infrastructure.persistence.mappers.mappers_utils import ensure_utc
from chinese_learning.infrastructure.persistence.models import (
    CharacterKnowledgeModel,
    VocabularyKnowledgeModel,
)


def character_knowledge_to_domain(model: CharacterKnowledgeModel) -> CharacterKnowledge:
    return CharacterKnowledge(
        learner_id=LearnerId(model.learner_id),
        character=Character(model.character_literal),
        status=model.status,
        successful_recognitions=model.successful_recognitions,
        failed_recognitions=model.failed_recognitions,
        correct_pinyin_count=model.correct_pinyin_count,
        times_seen=model.times_seen,
        first_seen_at=ensure_utc(model.first_seen_at),
        last_practised_at=ensure_utc(model.last_practised_at),
        last_seen_at=ensure_utc(model.last_seen_at),
        next_review_at=ensure_utc(model.next_review_at),
    )


def character_knowledge_to_model(domain: CharacterKnowledge) -> CharacterKnowledgeModel:
    return CharacterKnowledgeModel(
        learner_id=str(domain.learner_id),
        character_literal=str(domain.character),
        status=domain.status,
        successful_recognitions=domain.successful_recognitions,
        failed_recognitions=domain.failed_recognitions,
        correct_pinyin_count=domain.correct_pinyin_count,
        times_seen=domain.times_seen,
        first_seen_at=domain.first_seen_at,
        last_practised_at=domain.last_practised_at,
        last_seen_at=domain.last_seen_at,
        next_review_at=domain.next_review_at,
    )


def vocabulary_knowledge_to_domain(
    model: VocabularyKnowledgeModel,
) -> VocabularyKnowledge:
    return VocabularyKnowledge(
        learner_id=LearnerId(model.learner_id),
        vocabulary_id=VocabularyId(model.vocabulary_id),
        status=model.status,
        successful_recalls=model.successful_recalls,
        failed_recalls=model.failed_recalls,
        times_seen=model.times_seen,
        times_produced=model.times_produced,
        first_seen_at=ensure_utc(model.first_seen_at),
        last_practised_at=ensure_utc(model.last_practised_at),
        last_seen_at=ensure_utc(model.last_seen_at),
        next_review_at=ensure_utc(model.next_review_at),
        ease_factor=model.ease_factor,
        interval_days=model.interval_days,
    )


def vocabulary_knowledge_to_model(
    domain: VocabularyKnowledge,
) -> VocabularyKnowledgeModel:
    return VocabularyKnowledgeModel(
        learner_id=str(domain.learner_id),
        vocabulary_id=str(domain.vocabulary_id),
        status=domain.status,
        successful_recalls=domain.successful_recalls,
        failed_recalls=domain.failed_recalls,
        times_seen=domain.times_seen,
        times_produced=domain.times_produced,
        first_seen_at=domain.first_seen_at,
        last_practised_at=domain.last_practised_at,
        last_seen_at=domain.last_seen_at,
        next_review_at=domain.next_review_at,
        ease_factor=domain.ease_factor,
        interval_days=domain.interval_days,
    )

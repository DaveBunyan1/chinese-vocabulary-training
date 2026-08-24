import json
from uuid import uuid4

from chinese_learning.domain.text_analysis.character import Character
from chinese_learning.domain.text_analysis.sentence import Sentence
from chinese_learning.domain.text_analysis.token import Token
from chinese_learning.infrastructure.persistence.models import (
    CharacterModel,
    SentenceModel,
    TokenModel,
)

# ---------- Character ----------


def character_to_domain(model: CharacterModel) -> Character:
    return Character(symbol=model.symbol)


def character_to_model(domain: Character) -> CharacterModel:
    return CharacterModel(symbol=domain.symbol)


# ---------- Token ----------


def token_to_domain(model: TokenModel) -> Token:
    return Token(text=model.text)


def token_to_model(domain: Token) -> TokenModel:
    return TokenModel(text=domain.text)


# ---------- Sentence ----------


def sentence_to_domain(model: SentenceModel) -> Sentence:
    token_texts: list[str] = json.loads(model.tokens_json)
    tokens = [Token(text=t) for t in token_texts]
    return Sentence(tokens=tokens, raw_text=model.raw_text)


def sentence_to_model(
    domain: Sentence,
    *,
    sentence_id: str | None = None,
) -> SentenceModel:
    return SentenceModel(
        id=sentence_id or str(uuid4()),
        raw_text=domain.raw_text,
        tokens_json=json.dumps(
            [t.text for t in domain.tokens],
            ensure_ascii=False,
        ),
    )

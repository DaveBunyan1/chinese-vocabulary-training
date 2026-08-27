"""Unit tests for CC-CEDICT definition sanitization."""

from chinese_learning.infrastructure.nlp.definition_sanitize import sanitize_definition


def test_strips_parenthetical_glosses_and_bound_form():
    raw = (
        "(third-person singular) (since the early 20th century, usu. male) "
        "he; him; his/(bound form) other; another; some other "
        "(as in 他日[ta1 ri4] and 他人[ta1 ren2])"
    )
    assert sanitize_definition(raw) == "he; him; his"


def test_keeps_simple_gloss():
    assert sanitize_definition("hello; how do you do") == "hello; how do you do"


def test_strips_classifier_notes():
    # raw = "book; CL:本[ben3],冊|册[ce4]"
    # CL notes may appear outside parens in some entries; paren form is common
    raw_paren = "book (CL:本[ben3],冊|册[ce4])"
    assert sanitize_definition(raw_paren) == "book"


def test_drops_variant_of_sense():
    raw = "variant of 台|台[tai2]/platform; stage"
    assert "variant" not in sanitize_definition(raw).lower()
    assert "platform" in sanitize_definition(raw).lower()


def test_empty_and_whitespace():
    assert sanitize_definition("") == ""
    assert sanitize_definition("   ") == "   "


def test_surname_sense_kept_if_only_sense():
    # Sanitizer does not drop surname senses; ranking is CedictDictionary's job
    raw = "surname Wang"
    assert sanitize_definition(raw) == "surname Wang"


def test_multiple_useful_senses_joined():
    raw = "to study; to learn/school"
    assert sanitize_definition(raw) == "to study; to learn; school"

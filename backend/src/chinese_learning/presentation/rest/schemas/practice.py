"""Request/response schemas for practice endpoints."""

from pydantic import BaseModel, Field


class AnswerOptionSchema(BaseModel):
    text: str
    is_correct: bool


class QuestionSchema(BaseModel):
    id: str
    type: str
    order: int
    prompt: str
    correct_answers: list[str]
    vocabulary_id: str | None = None
    character: str | None = None
    options: list[AnswerOptionSchema] = Field(default_factory=list)
    is_multiple_choice: bool = False


class ExerciseSchema(BaseModel):
    id: str
    learner_id: str
    type: str
    status: str
    questions: list[QuestionSchema]
    category_id: str | None = None
    knowledge_status_filter: str | None = None
    question_count: int
    candidate_count: int
    created_at: str


class GenerateVocabularyRecallRequest(BaseModel):
    count: int = Field(default=10, ge=1, le=50)
    category_id: str | None = None
    knowledge_status: str | None = Field(
        default=None,
        description="new | learning | known",
    )
    direction: str = Field(default="meaning_to_hanzi")


class GenerateCharacterRecognitionRequest(BaseModel):
    count: int = Field(default=10, ge=1, le=50)
    knowledge_status: str | None = None
    direction: str = Field(default="character_to_meaning")


class SubmitAnswerRequest(BaseModel):
    exercise_id: str
    question_id: str
    question_type: str
    raw_answer: str = Field(..., min_length=0, max_length=500)
    correct_answers: list[str] = Field(..., min_length=1)
    vocabulary_id: str | None = None
    character: str | None = None
    response_time_ms: int | None = Field(default=None, ge=0)


class SubmitAnswerResponse(BaseModel):
    attempt_id: str
    is_correct: bool
    previous_status: str | None
    new_status: str | None
    raw_answer: str
    response_time_ms: int | None = None

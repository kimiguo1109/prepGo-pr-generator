"""Practice generation request and response models."""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class DifficultyLevel(str, Enum):
    """Difficulty level for practice questions."""
    EASIER = "easier"      # Easier than AP exam
    AP_LEVEL = "ap_level"  # AP Exam level
    HARDER = "harder"      # Harder than AP exam


class PracticeRequest(BaseModel):
    """Practice generation request."""
    course_id: str = Field(..., description="Course identifier (e.g., 'biology', 'us-history')")
    unit_numbers: list[int] = Field(..., min_length=1, description="List of unit numbers to include")
    mcq_count: int = Field(default=15, ge=1, le=50, description="Number of MCQ questions")
    frq_count: int = Field(default=2, ge=0, le=10, description="Number of FRQ questions")
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.AP_LEVEL, description="Difficulty level")


class PracticeResponse(BaseModel):
    """Practice generation response."""
    course_name: str
    unit_titles: list[str]
    practice_content: str
    mcq_count: int
    frq_count: int
    difficulty: str
    generated_at: datetime = Field(default_factory=datetime.now)


class PracticeStreamChunk(BaseModel):
    """Streaming chunk for practice generation."""
    content: str
    is_complete: bool = False


class QuestionMetadata(BaseModel):
    """Metadata for a generated question (stored internally, not shown to user)."""
    question_number: int
    question_type: str  # "mcq" or "frq"
    skills: list[str] = []
    topics: list[str] = []
    difficulty: str


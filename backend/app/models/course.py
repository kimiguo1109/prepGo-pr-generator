"""Course data models."""
from typing import Optional
from pydantic import BaseModel


class LearningObjective(BaseModel):
    """Learning objective model."""
    id: str
    summary: str


class EssentialKnowledge(BaseModel):
    """Essential knowledge model."""
    id: str
    summary: str


class SkillDetails(BaseModel):
    """Skill details model."""
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    skill_name: Optional[str] = None


class Topic(BaseModel):
    """Topic model."""
    topic_number: str
    topic_title: str
    suggested_skill: Optional[str] = None
    skill_details: Optional[SkillDetails] = None
    reasoning_process: Optional[str] = None
    learning_objectives: list[LearningObjective] = []
    essential_knowledge: list[EssentialKnowledge] = []
    study_guide: Optional[dict] = None


class UnitOverview(BaseModel):
    """Unit overview model."""
    summary: Optional[str] = None
    study_guide: Optional[str] = None


class ProgressCheck(BaseModel):
    """Progress check info model."""
    mcq_count: int = 0
    frq_count: int = 0
    saq_count: int = 0
    mcq_description: Optional[str] = None
    frq_description: Optional[str] = None
    saq_description: Optional[str] = None


class Unit(BaseModel):
    """Unit model."""
    unit_number: int
    unit_title: str
    exam_weight: Optional[str] = None
    ced_class_periods: Optional[str] = None
    unit_overview: Optional[UnitOverview] = None
    topics: list[Topic] = []
    progress_check: Optional[ProgressCheck] = None


class Course(BaseModel):
    """Course model."""
    course_name: str
    units: list[Unit] = []
    skills: Optional[dict] = None


class CourseListItem(BaseModel):
    """Course list item for API responses."""
    id: str
    name: str
    units_count: int


class UnitListItem(BaseModel):
    """Unit list item for API responses."""
    unit_number: int
    unit_title: str
    exam_weight: Optional[str] = None
    ced_class_periods: Optional[str] = None
    topics_count: int
    progress_check: Optional[ProgressCheck] = None


"""Practice generation service."""
from datetime import datetime
from typing import AsyncGenerator

from app.models.practice import PracticeRequest, PracticeResponse, DifficultyLevel
from app.services.course_service import CourseService
from app.services.gemini_client import GeminiClient
from app.prompts.practice_prompt import build_practice_prompt


class PracticeService:
    """Service for generating practice question sets."""
    
    @classmethod
    async def generate_practice_stream(
        cls, 
        request: PracticeRequest
    ) -> AsyncGenerator[str, None]:
        """Generate practice questions with streaming response."""
        # Get course data
        course = CourseService.get_course(request.course_id)
        if not course:
            raise ValueError(f"Course not found: {request.course_id}")
        
        # Get requested units
        units = CourseService.get_units(request.course_id, request.unit_numbers)
        if not units:
            raise ValueError(f"No valid units found for: {request.unit_numbers}")
        
        # Verify all requested units exist
        found_unit_numbers = {u.unit_number for u in units}
        missing = set(request.unit_numbers) - found_unit_numbers
        if missing:
            raise ValueError(f"Units not found: {missing}")
        
        # Get skills dictionary (used internally for prompt building)
        skills_dict = CourseService.get_skills_dict(request.course_id)
        
        # Build prompt
        prompt = build_practice_prompt(
            units=units,
            course_name=course.course_name,
            mcq_count=request.mcq_count,
            frq_count=request.frq_count,
            difficulty=request.difficulty,
            skills_dict=skills_dict
        )
        
        # Generate with streaming
        async for chunk in GeminiClient.generate_content_stream(prompt):
            yield chunk
    
    @classmethod
    async def generate_practice(cls, request: PracticeRequest) -> PracticeResponse:
        """Generate practice questions (non-streaming)."""
        # Get course data
        course = CourseService.get_course(request.course_id)
        if not course:
            raise ValueError(f"Course not found: {request.course_id}")
        
        # Get requested units
        units = CourseService.get_units(request.course_id, request.unit_numbers)
        if not units:
            raise ValueError(f"No valid units found for: {request.unit_numbers}")
        
        # Get skills dictionary
        skills_dict = CourseService.get_skills_dict(request.course_id)
        
        # Build prompt
        prompt = build_practice_prompt(
            units=units,
            course_name=course.course_name,
            mcq_count=request.mcq_count,
            frq_count=request.frq_count,
            difficulty=request.difficulty,
            skills_dict=skills_dict
        )
        
        # Generate content
        content = await GeminiClient.generate_content(prompt)
        
        return PracticeResponse(
            course_name=course.course_name,
            unit_titles=[u.unit_title for u in units],
            practice_content=content,
            mcq_count=request.mcq_count,
            frq_count=request.frq_count,
            difficulty=request.difficulty.value,
            generated_at=datetime.now()
        )


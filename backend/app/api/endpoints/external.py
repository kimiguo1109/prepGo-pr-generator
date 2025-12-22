"""External API endpoints for third-party integration - JSON output."""
import json
import logging
import re
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Any

from app.models.practice import PracticeRequest, DifficultyLevel
from app.services.course_service import CourseService
from app.services.gemini_client import GeminiClient
from app.services.queue_manager import QueueManager
from app.prompts.practice_json_prompt import build_practice_json_prompt

router = APIRouter(prefix="/external", tags=["external"])
logger = logging.getLogger(__name__)


class ExternalGenerateRequest(BaseModel):
    """External generate request model."""
    course_id: str = Field(..., description="Course identifier (e.g., 'biology', 'us-history')")
    unit_numbers: list[int] = Field(..., min_length=1, description="List of unit numbers to include")
    mcq_count: int = Field(default=15, ge=1, le=50, description="Number of MCQ questions")
    frq_count: int = Field(default=2, ge=0, le=10, description="Number of FRQ questions")
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.AP_LEVEL, description="Difficulty level")


class ExternalGenerateResponse(BaseModel):
    """External generate response model."""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


def extract_json_from_response(text: str) -> dict:
    """Extract and parse JSON from AI response."""
    # Clean the text
    cleaned = text.strip()
    
    # Try direct parse first
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    # Remove markdown code block markers if present
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]  # Remove ```json
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]  # Remove ```
    
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]  # Remove trailing ```
    
    cleaned = cleaned.strip()
    
    # Try parsing the cleaned text
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON in code blocks (more thorough)
    code_block_pattern = r'```(?:json)?\s*\n?([\s\S]*?)\n?```'
    matches = re.findall(code_block_pattern, text)
    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue
    
    # Try to find a complete JSON object by bracket matching
    start_idx = text.find('{')
    if start_idx != -1:
        bracket_count = 0
        for i in range(start_idx, len(text)):
            if text[i] == '{':
                bracket_count += 1
            elif text[i] == '}':
                bracket_count -= 1
                if bracket_count == 0:
                    json_str = text[start_idx:i+1]
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        break
    
    raise ValueError("Could not extract valid JSON from response")


@router.post("/generate", response_model=ExternalGenerateResponse)
async def external_generate(request: ExternalGenerateRequest):
    """
    Generate practice questions and return as structured JSON.
    
    Returns structured data with:
    - header: Course info, units, difficulty, question counts
    - mcq_questions: Array of MCQ with options, answers, explanations
    - frq_questions: Array of FRQ with parts, model answers, scoring
    - answer_key: Quick reference for MCQ answers
    
    **Note:** This is a synchronous endpoint that may take 30-90 seconds.
    """
    logger.info(f"External JSON generate request: {request.course_id} units {request.unit_numbers}")
    
    # Validate course exists
    course = CourseService.get_course(request.course_id)
    if not course:
        return ExternalGenerateResponse(
            success=False,
            error=f"Course not found: {request.course_id}"
        )
    
    # Validate units exist
    units = CourseService.get_units(request.course_id, request.unit_numbers)
    if not units:
        return ExternalGenerateResponse(
            success=False,
            error=f"No valid units found for: {request.unit_numbers}"
        )
    
    found_unit_numbers = {u.unit_number for u in units}
    missing = set(request.unit_numbers) - found_unit_numbers
    if missing:
        return ExternalGenerateResponse(
            success=False,
            error=f"Units not found: {list(missing)}"
        )
    
    # Create queue request for tracking
    request_id = await QueueManager.create_request(request.course_id, request.unit_numbers)
    
    try:
        # Acquire processing slot
        acquired = await QueueManager.acquire(request_id, timeout=300)
        
        if not acquired:
            return ExternalGenerateResponse(
                success=False,
                error="Request timed out waiting in queue. Please try again later."
            )
        
        # Get course type for subject-specific formatting
        course_type = CourseService.get_course_type(request.course_id)
        
        # Build JSON prompt with course type
        prompt = build_practice_json_prompt(
            units=units,
            course_name=course.course_name,
            mcq_count=request.mcq_count,
            frq_count=request.frq_count,
            difficulty=request.difficulty,
            course_type=course_type
        )
        
        # Generate content
        raw_response = await GeminiClient.generate_content(prompt, request_id=request_id)
        
        # Parse JSON from response
        try:
            content_json = extract_json_from_response(raw_response)
        except ValueError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"Raw response preview: {raw_response[:500]}")
            return ExternalGenerateResponse(
                success=False,
                error="Failed to parse generated content as JSON. Please try again."
            )
        
        logger.info(f"External JSON generate completed for {request_id}")
        
        # Return structured response
        return ExternalGenerateResponse(
            success=True,
            data={
                "course_id": request.course_id,
                "course_name": course.course_name,
                "unit_numbers": request.unit_numbers,
                "unit_titles": [u.unit_title for u in units],
                "mcq_count": request.mcq_count,
                "frq_count": request.frq_count,
                "difficulty": request.difficulty.value,
                "content": content_json,
                "generated_at": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"External generate error: {e}")
        return ExternalGenerateResponse(
            success=False,
            error=f"Generation failed: {str(e)}"
        )
    finally:
        # Always release the slot
        await QueueManager.release(request_id)


@router.get("/courses")
async def list_courses():
    """List all available courses for practice generation, organized by category."""
    categories = CourseService.get_courses_by_category()
    courses = CourseService.get_available_courses()
    
    return {
        "success": True,
        "data": {
            "categories": categories,
            "all_courses": [
                {
                    "id": c.id,
                    "name": c.name,
                    "units_count": c.units_count,
                    "type": CourseService.get_course_type(c.id)
                }
                for c in courses
            ]
        }
    }


@router.get("/courses/{course_id}/units")
async def get_course_units(course_id: str):
    """Get available units for a specific course."""
    course_name, units = CourseService.get_course_units(course_id)
    
    if not units:
        return {
            "success": False,
            "error": f"Course not found: {course_id}"
        }
    
    return {
        "success": True,
        "data": {
            "course_id": course_id,
            "course_name": course_name,
            "units": [
                {
                    "unit_number": u.unit_number,
                    "unit_title": u.unit_title,
                    "exam_weight": u.exam_weight,
                    "topics_count": u.topics_count
                }
                for u in units
            ]
        }
    }


@router.get("/queue-status")
async def get_queue_status():
    """Get current queue status for monitoring."""
    status = await QueueManager.get_queue_status()
    return {
        "success": True,
        "data": status
    }

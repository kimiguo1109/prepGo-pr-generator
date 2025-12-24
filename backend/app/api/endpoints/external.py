"""External API endpoints for third-party integration - JSON output."""
import asyncio
import json
import logging
import re
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict

from app.models.practice import PracticeRequest, DifficultyLevel
from app.services.course_service import CourseService
from app.services.gemini_client import GeminiClient
from app.services.queue_manager import QueueManager
from app.prompts.practice_json_prompt import build_practice_json_prompt

router = APIRouter(prefix="/external", tags=["external"])
logger = logging.getLogger(__name__)


# In-memory task storage (for async task management)
_task_store: Dict[str, dict] = {}


class TaskStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


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
    """Extract and parse JSON from AI response, with truncation repair."""
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
        in_string = False
        escape_next = False
        last_complete_pos = -1
        
        for i in range(start_idx, len(text)):
            char = text[i]
            
            if escape_next:
                escape_next = False
                continue
            
            if char == '\\':
                escape_next = True
                continue
            
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            
            if in_string:
                continue
                
            if char == '{':
                bracket_count += 1
            elif char == '}':
                bracket_count -= 1
                if bracket_count == 0:
                    json_str = text[start_idx:i+1]
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        break
    
    # If we get here, the JSON might be truncated - try to repair it
    repaired_json = _try_repair_truncated_json(cleaned)
    if repaired_json:
        return repaired_json
    
    raise ValueError("Could not extract valid JSON from response")


def _try_repair_truncated_json(text: str) -> Optional[dict]:
    """Attempt to repair truncated JSON by closing open structures."""
    # Find the start of JSON
    start_idx = text.find('{')
    if start_idx == -1:
        return None
    
    json_text = text[start_idx:]
    
    # Count unclosed brackets and braces (simplified, doesn't handle strings perfectly)
    # We'll try progressively more aggressive repairs
    
    repairs = [
        # Try just closing with minimal repair
        lambda t: t.rstrip(',\n\t ') + '}' * (t.count('{') - t.count('}')),
        # Try closing arrays too
        lambda t: _close_json_structures(t),
        # Try truncating to last complete structure
        lambda t: _truncate_to_complete(t),
    ]
    
    for repair_fn in repairs:
        try:
            repaired = repair_fn(json_text)
            result = json.loads(repaired)
            logger.warning(f"Successfully repaired truncated JSON using {repair_fn.__name__ if hasattr(repair_fn, '__name__') else 'repair'}")
            return result
        except (json.JSONDecodeError, Exception):
            continue
    
    return None


def _close_json_structures(text: str) -> str:
    """Close all open JSON structures (braces and brackets)."""
    # Count open structures (simplified - doesn't handle strings)
    open_braces = 0
    open_brackets = 0
    in_string = False
    escape_next = False
    
    for char in text:
        if escape_next:
            escape_next = False
            continue
        if char == '\\':
            escape_next = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == '{':
            open_braces += 1
        elif char == '}':
            open_braces -= 1
        elif char == '[':
            open_brackets += 1
        elif char == ']':
            open_brackets -= 1
    
    # Remove trailing incomplete content (after last comma or colon)
    result = text.rstrip()
    
    # Remove trailing incomplete value
    if result.endswith(','):
        result = result[:-1]
    elif result.endswith(':'):
        result = result[:-1].rstrip().rstrip(',')
    
    # Check if we're in the middle of a string
    if result.count('"') % 2 == 1:
        # Find last complete string
        last_quote = result.rfind('"')
        if last_quote > 0:
            # Look for the opening quote
            prev_quote = result.rfind('"', 0, last_quote)
            if prev_quote >= 0:
                result = result[:last_quote]
                result = result.rstrip().rstrip(',').rstrip(':')
    
    # Close structures
    result = result.rstrip().rstrip(',')
    result += ']' * max(0, open_brackets) + '}' * max(0, open_braces)
    
    return result


def _truncate_to_complete(text: str) -> str:
    """Truncate to the last complete object/array element."""
    # Find positions of complete structures by looking for },  or ],
    # Work backwards to find a good truncation point
    
    # Start from the end and look for a point where we can close cleanly
    for end_pos in range(len(text) - 1, len(text) // 2, -1):
        char = text[end_pos]
        if char in '},]':
            test_text = text[:end_pos + 1]
            # Count structures
            open_braces = test_text.count('{') - test_text.count('}')
            open_brackets = test_text.count('[') - test_text.count(']')
            
            if open_braces >= 0 and open_brackets >= 0:
                # Try to close and parse
                closed = test_text + ']' * open_brackets + '}' * open_braces
                try:
                    json.loads(closed)
                    return closed
                except json.JSONDecodeError:
                    continue
    
    return text


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


# ============== Async Task API ==============

class AsyncGenerateResponse(BaseModel):
    """Response for async generate request."""
    success: bool
    task_id: Optional[str] = None
    error: Optional[str] = None


class TaskStatusResponse(BaseModel):
    """Response for task status query."""
    success: bool
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: Optional[str] = None
    data: Optional[dict] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


async def _process_generate_task(task_id: str, request: ExternalGenerateRequest):
    """Background task to process generation request."""
    logger.info(f"[Task {task_id}] Starting background generation...")
    
    _task_store[task_id]["status"] = TaskStatus.PROCESSING
    _task_store[task_id]["progress"] = "Validating request..."
    
    try:
        # Validate course exists
        course = CourseService.get_course(request.course_id)
        if not course:
            _task_store[task_id]["status"] = TaskStatus.FAILED
            _task_store[task_id]["error"] = f"Course not found: {request.course_id}"
            return
        
        # Validate units exist
        units = CourseService.get_units(request.course_id, request.unit_numbers)
        if not units:
            _task_store[task_id]["status"] = TaskStatus.FAILED
            _task_store[task_id]["error"] = f"No valid units found for: {request.unit_numbers}"
            return
        
        found_unit_numbers = {u.unit_number for u in units}
        missing = set(request.unit_numbers) - found_unit_numbers
        if missing:
            _task_store[task_id]["status"] = TaskStatus.FAILED
            _task_store[task_id]["error"] = f"Units not found: {list(missing)}"
            return
        
        _task_store[task_id]["progress"] = "Waiting in queue..."
        
        # Create queue request for tracking
        queue_request_id = await QueueManager.create_request(request.course_id, request.unit_numbers)
        
        try:
            # Acquire processing slot
            acquired = await QueueManager.acquire(queue_request_id, timeout=300)
            
            if not acquired:
                _task_store[task_id]["status"] = TaskStatus.FAILED
                _task_store[task_id]["error"] = "Request timed out waiting in queue."
                return
            
            _task_store[task_id]["progress"] = "Generating with AI..."
            
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
            raw_response = await GeminiClient.generate_content(prompt, request_id=queue_request_id)
            
            _task_store[task_id]["progress"] = "Parsing response..."
            
            # Parse JSON from response
            try:
                content_json = extract_json_from_response(raw_response)
            except ValueError as e:
                logger.error(f"[Task {task_id}] Failed to parse JSON: {e}")
                logger.error(f"[Task {task_id}] Raw response first 1000 chars: {raw_response[:1000]}")
                logger.error(f"[Task {task_id}] Raw response last 500 chars: {raw_response[-500:]}")
                _task_store[task_id]["status"] = TaskStatus.FAILED
                _task_store[task_id]["error"] = "Failed to parse generated content as JSON."
                return
            
            # Success!
            _task_store[task_id]["status"] = TaskStatus.COMPLETED
            _task_store[task_id]["progress"] = "Complete"
            _task_store[task_id]["completed_at"] = datetime.now().isoformat()
            _task_store[task_id]["data"] = {
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
            
            logger.info(f"[Task {task_id}] Generation completed successfully")
            
        finally:
            await QueueManager.release(queue_request_id)
            
    except Exception as e:
        logger.error(f"[Task {task_id}] Generation failed: {e}")
        _task_store[task_id]["status"] = TaskStatus.FAILED
        _task_store[task_id]["error"] = f"Generation failed: {str(e)}"


@router.post("/async", response_model=AsyncGenerateResponse)
async def async_generate(request: ExternalGenerateRequest, background_tasks: BackgroundTasks):
    """
    Start an async practice generation task.
    
    Returns immediately with a task_id. Use /task/{task_id} to poll for results.
    
    This endpoint is designed for long-running requests that may exceed HTTP timeout limits.
    """
    task_id = str(uuid.uuid4())
    
    logger.info(f"[Task {task_id}] Async generate request: {request.course_id} units {request.unit_numbers}")
    
    # Initialize task in store
    _task_store[task_id] = {
        "status": TaskStatus.PENDING,
        "progress": "Task created",
        "data": None,
        "error": None,
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "request": {
            "course_id": request.course_id,
            "unit_numbers": request.unit_numbers,
            "mcq_count": request.mcq_count,
            "frq_count": request.frq_count,
            "difficulty": request.difficulty.value
        }
    }
    
    # Start background task
    background_tasks.add_task(_process_generate_task, task_id, request)
    
    return AsyncGenerateResponse(
        success=True,
        task_id=task_id
    )


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get the status of an async generation task.
    
    Poll this endpoint to check if your task is complete.
    
    Status values:
    - pending: Task is waiting to start
    - processing: Task is being processed
    - completed: Task finished successfully (data available)
    - failed: Task failed (error available)
    """
    if task_id not in _task_store:
        return TaskStatusResponse(
            success=False,
            task_id=task_id,
            status="not_found",
            error="Task not found. It may have expired or never existed."
        )
    
    task = _task_store[task_id]
    
    return TaskStatusResponse(
        success=True,
        task_id=task_id,
        status=task["status"],
        progress=task.get("progress"),
        data=task.get("data"),
        error=task.get("error"),
        created_at=task.get("created_at"),
        completed_at=task.get("completed_at")
    )


@router.delete("/task/{task_id}")
async def delete_task(task_id: str):
    """Delete a completed or failed task from memory."""
    if task_id in _task_store:
        del _task_store[task_id]
        return {"success": True, "message": "Task deleted"}
    return {"success": False, "error": "Task not found"}

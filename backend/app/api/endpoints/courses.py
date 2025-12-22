"""Course API endpoints."""
from fastapi import APIRouter, HTTPException

from app.services.course_service import CourseService

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("")
async def get_courses():
    """Get list of available courses."""
    courses = CourseService.get_available_courses()
    return {"courses": courses}


@router.get("/categories")
async def get_courses_by_category():
    """Get courses organized by category."""
    categories = CourseService.get_courses_by_category()
    return {"categories": categories}


@router.get("/{course_id}/units")
async def get_course_units(course_id: str):
    """Get units for a specific course."""
    course_name, units = CourseService.get_course_units(course_id)
    
    if not units:
        raise HTTPException(
            status_code=404,
            detail=f"Course not found: {course_id}"
        )
    
    return {
        "course_name": course_name,
        "units": units
    }


@router.get("/{course_id}/type")
async def get_course_type(course_id: str):
    """Get the course type for a specific course."""
    course_type = CourseService.get_course_type(course_id)
    return {
        "course_id": course_id,
        "course_type": course_type
    }


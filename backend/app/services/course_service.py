"""Course data service with thread-safe caching for multi-user support."""
import json
import glob
import threading
import logging
import httpx
from pathlib import Path
from typing import Optional

from app.config import settings
from app.models.course import Course, Unit, CourseListItem, UnitListItem, ProgressCheck

logger = logging.getLogger(__name__)

# HTTP client for fetching from S3
_http_client = httpx.Client(timeout=30.0)


class CourseService:
    """Service for loading and managing course data with thread-safe caching."""
    
    # Thread-safe cache with lock
    _cache: dict[str, Course] = {}
    _skills_cache: dict[str, dict] = {}
    _lock = threading.RLock()
    _initialized = False
    
    @classmethod
    def _get_course_url(cls, course_id: str) -> Optional[str]:
        """Get the S3 URL for a course file."""
        if course_id in settings.course_file_mapping:
            file_path = settings.course_file_mapping[course_id]
            return f"{settings.s3_course_data_url}/{file_path}"
        return None
    
    @classmethod
    def _get_course_file_path(cls, course_id: str) -> Optional[Path]:
        """Get the local file path for a course using glob pattern (fallback)."""
        base_path = Path(settings.course_data_path)
        
        # Check if we have a mapping for this course
        if course_id in settings.course_file_mapping:
            pattern = settings.course_file_mapping[course_id]
            # For S3, the mapping is exact filename, so try direct path first
            direct_path = base_path / pattern
            if direct_path.exists():
                return direct_path
            # Fallback to glob pattern
            matches = glob.glob(str(base_path / pattern))
            if matches:
                return Path(sorted(matches)[-1])
        
        return None
    
    @classmethod
    def _load_course(cls, course_id: str) -> Optional[Course]:
        """Load course data from S3 URL or local file with thread-safe caching."""
        # Fast path: check cache without lock
        if course_id in cls._cache:
            return cls._cache[course_id]
        
        # Slow path: acquire lock and load
        with cls._lock:
            # Double-check after acquiring lock
            if course_id in cls._cache:
                return cls._cache[course_id]
            
            data = None
            
            # Try S3 first (preferred)
            s3_url = cls._get_course_url(course_id)
            if s3_url:
                try:
                    logger.info(f"Loading course data: {course_id} from S3: {s3_url}")
                    response = _http_client.get(s3_url)
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"✅ Loaded {course_id} from S3")
                    else:
                        logger.warning(f"S3 returned {response.status_code} for {course_id}")
                except Exception as e:
                    logger.warning(f"Failed to load from S3 for {course_id}: {e}")
            
            # Fallback to local file
            if data is None:
                file_path = cls._get_course_file_path(course_id)
                if file_path and file_path.exists():
                    try:
                        logger.info(f"Loading course data: {course_id} from local: {file_path.name}")
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                    except Exception as e:
                        logger.error(f"Error loading local file for {course_id}: {e}")
            
            if data is None:
                logger.warning(f"Course file not found for: {course_id}")
                return None
            
            try:
                course = Course(**data)
                cls._cache[course_id] = course
                
                # Also cache skills if available
                if "skills" in data:
                    cls._skills_cache[course_id] = data["skills"]
                
                return course
                
            except Exception as e:
                logger.error(f"Error parsing course {course_id}: {e}")
                return None
    
    @classmethod
    def preload_courses(cls):
        """Preload all available courses into cache (call on startup)."""
        all_course_ids = list(settings.course_file_mapping.keys())
        
        loaded = 0
        for course_id in all_course_ids:
            if cls._load_course(course_id):
                loaded += 1
        
        logger.info(f"Preloaded {loaded}/{len(all_course_ids)} courses")
        cls._initialized = True
    
    @classmethod
    def get_available_courses(cls) -> list[CourseListItem]:
        """Get list of available courses organized by category."""
        courses = []
        
        # Iterate through all categories
        for category, category_courses in settings.course_categories.items():
            for course_info in category_courses:
                course_id = course_info["id"]
                course = cls._load_course(course_id)
                if course:
                    courses.append(CourseListItem(
                        id=course_id,
                        name=course.course_name,
                        units_count=len(course.units)
                    ))
        
        return courses
    
    @classmethod
    def get_courses_by_category(cls) -> dict:
        """Get courses organized by category."""
        result = {}
        
        for category, category_courses in settings.course_categories.items():
            result[category] = []
            for course_info in category_courses:
                course_id = course_info["id"]
                course = cls._load_course(course_id)
                if course:
                    result[category].append({
                        "id": course_id,
                        "name": course.course_name,
                        "units_count": len(course.units)
                    })
        
        return result
    
    @classmethod
    def get_course(cls, course_id: str) -> Optional[Course]:
        """Get full course data."""
        return cls._load_course(course_id)
    
    @classmethod
    def get_course_type(cls, course_id: str) -> str:
        """Get the course type for special formatting."""
        return settings.course_type_mapping.get(course_id, "general")
    
    @classmethod
    def get_course_units(cls, course_id: str) -> tuple[str, list[UnitListItem]]:
        """Get units for a course."""
        course = cls._load_course(course_id)
        if not course:
            return "", []
        
        units = [
            UnitListItem(
                unit_number=unit.unit_number,
                unit_title=unit.unit_title,
                exam_weight=unit.exam_weight,
                ced_class_periods=unit.ced_class_periods,
                topics_count=len(unit.topics),
                progress_check=unit.progress_check
            )
            for unit in course.units
        ]
        
        return course.course_name, units
    
    @classmethod
    def get_unit(cls, course_id: str, unit_number: int) -> Optional[Unit]:
        """Get a specific unit from a course."""
        course = cls._load_course(course_id)
        if not course:
            return None
        
        for unit in course.units:
            if unit.unit_number == unit_number:
                return unit
        
        return None
    
    @classmethod
    def get_units(cls, course_id: str, unit_numbers: list[int]) -> list[Unit]:
        """Get multiple units from a course."""
        course = cls._load_course(course_id)
        if not course:
            return []
        
        units = []
        for unit in course.units:
            if unit.unit_number in unit_numbers:
                units.append(unit)
        
        # Sort by unit number
        units.sort(key=lambda u: u.unit_number)
        return units
    
    @classmethod
    def get_skills_dict(cls, course_id: str) -> dict:
        """Get the skills dictionary for a course with caching."""
        # Fast path: check cache
        if course_id in cls._skills_cache:
            return cls._skills_cache[course_id]
        
        with cls._lock:
            # Double-check after lock
            if course_id in cls._skills_cache:
                return cls._skills_cache[course_id]
            
            # Try loading the course which will also cache skills
            course = cls._load_course(course_id)
            if course and course_id in cls._skills_cache:
                return cls._skills_cache[course_id]
            
            return {}
    
    @classmethod
    def clear_cache(cls):
        """Clear all cached data."""
        with cls._lock:
            cls._cache.clear()
            cls._skills_cache.clear()
            logger.info("Course cache cleared")
    
    @classmethod
    def get_cache_stats(cls) -> dict:
        """Get cache statistics for monitoring."""
        with cls._lock:
            return {
                "courses_cached": len(cls._cache),
                "skills_cached": len(cls._skills_cache),
                "cached_courses": list(cls._cache.keys())
            }

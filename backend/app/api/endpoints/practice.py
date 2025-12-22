"""Practice generation API endpoints with multi-user support."""
import json
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from sse_starlette.sse import EventSourceResponse

from app.models.practice import PracticeRequest, PracticeResponse
from app.services.practice_service import PracticeService
from app.services.course_service import CourseService
from app.services.queue_manager import QueueManager

router = APIRouter(prefix="/practice", tags=["practice"])
logger = logging.getLogger(__name__)


async def practice_event_generator(request: PracticeRequest, request_id: str):
    """Generate SSE events for practice streaming with queue management."""
    logger.info(f"Starting practice generation for request {request_id}: {request.course_id} units {request.unit_numbers}")
    
    try:
        # Send initial queue status
        queue_status = await QueueManager.get_queue_status()
        position = await QueueManager.get_queue_position(request_id)
        estimated_wait = await QueueManager.get_estimated_wait_time(request_id)
        
        yield {
            "event": "queue",
            "data": json.dumps({
                "position": position,
                "queue_length": queue_status["queue_length"],
                "active_count": queue_status["active_count"],
                "max_concurrent": queue_status["max_concurrent"],
                "estimated_wait_seconds": estimated_wait
            })
        }
        
        # Show waiting message if in queue
        if position > 1:
            yield {
                "event": "message",
                "data": json.dumps({
                    "content": f"⏳ You are #{position} in queue. Estimated wait: ~{estimated_wait or 60}s\n",
                    "is_complete": False,
                    "is_queue_message": True
                })
            }
        
        # Acquire processing slot (this will wait if queue is full)
        acquired = await QueueManager.acquire(request_id)
        
        if not acquired:
            yield {
                "event": "error",
                "data": json.dumps({"error": "Request timed out waiting in queue"})
            }
            return
        
        yield {
            "event": "message",
            "data": json.dumps({
                "content": "🚀 Starting practice generation...\n",
                "is_complete": False,
                "is_queue_message": True
            })
        }
        
        # Generate the practice set
        async for chunk in PracticeService.generate_practice_stream(request):
            yield {
                "event": "message",
                "data": json.dumps({"content": chunk, "is_complete": False})
            }
        
        logger.info(f"Completed practice generation for request {request_id}")
        yield {
            "event": "message", 
            "data": json.dumps({"content": "", "is_complete": True})
        }
        
    except ValueError as e:
        logger.error(f"ValueError for request {request_id}: {e}")
        yield {
            "event": "error",
            "data": json.dumps({"error": str(e)})
        }
    except Exception as e:
        import traceback
        logger.error(f"Exception for request {request_id}: {e}")
        logger.error(traceback.format_exc())
        yield {
            "event": "error",
            "data": json.dumps({"error": f"Generation failed: {str(e)}"})
        }
    finally:
        # Always release the slot
        await QueueManager.release(request_id)


@router.get("/queue-status")
async def get_queue_status():
    """Get current queue status."""
    status = await QueueManager.get_queue_status()
    return status


@router.get("/queue-status/detailed")
async def get_detailed_queue_status():
    """Get detailed queue status for monitoring."""
    status = await QueueManager.get_detailed_status()
    return status


@router.post("/generate")
async def generate_practice(request: PracticeRequest):
    """Generate practice questions with streaming response and queue management."""
    # Validate course exists
    course = CourseService.get_course(request.course_id)
    if not course:
        raise HTTPException(
            status_code=404,
            detail=f"Course not found: {request.course_id}"
        )
    
    # Validate units exist
    units = CourseService.get_units(request.course_id, request.unit_numbers)
    if not units:
        raise HTTPException(
            status_code=404,
            detail=f"No valid units found for: {request.unit_numbers}"
        )
    
    found_unit_numbers = {u.unit_number for u in units}
    missing = set(request.unit_numbers) - found_unit_numbers
    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"Units not found: {missing}"
        )
    
    # Create queue request
    request_id = await QueueManager.create_request(request.course_id, request.unit_numbers)
    
    return EventSourceResponse(practice_event_generator(request, request_id))


@router.post("/generate-sync", response_model=PracticeResponse)
async def generate_practice_sync(request: PracticeRequest):
    """Generate practice questions (non-streaming, for testing)."""
    try:
        response = await PracticeService.generate_practice(request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.delete("/queue/{request_id}")
async def cancel_request(request_id: str):
    """Cancel a queued request."""
    cancelled = await QueueManager.cancel_request(request_id)
    if cancelled:
        return {"status": "cancelled", "request_id": request_id}
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Request not found or already processing: {request_id}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for load balancers."""
    queue_status = await QueueManager.get_queue_status()
    cache_stats = CourseService.get_cache_stats()
    
    return {
        "status": "healthy",
        "queue": queue_status,
        "cache": cache_stats
    }

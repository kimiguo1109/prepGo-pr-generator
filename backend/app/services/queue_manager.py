"""Queue manager for rate limiting concurrent generations with multi-user support."""
import asyncio
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class RequestStatus(str, Enum):
    """Request status enum."""
    WAITING = "waiting"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class QueueRequest:
    """Queue request data."""
    request_id: str
    course_id: str
    unit_numbers: list[int]
    created_at: datetime
    status: RequestStatus = RequestStatus.WAITING
    started_at: Optional[datetime] = None
    user_id: Optional[str] = None  # For future user tracking


class QueueManager:
    """
    Manages the generation queue to limit concurrent API calls.
    Supports multiple concurrent users with fair queuing.
    """
    
    # Class-level state (shared across all instances)
    _queue: Dict[str, QueueRequest] = {}
    _active: Set[str] = set()
    _lock: asyncio.Lock = None
    _condition: asyncio.Condition = None
    _initialized: bool = False
    
    # Configuration
    _max_concurrent: int = 5  # Increased for multi-user support
    _request_timeout: int = 300  # 5 minutes timeout for processing
    _queue_timeout: int = 600  # 10 minutes timeout for waiting in queue
    _cleanup_interval: int = 60  # Cleanup stale requests every 60 seconds
    _cleanup_task: Optional[asyncio.Task] = None
    
    @classmethod
    async def _ensure_initialized(cls):
        """Ensure async primitives are initialized."""
        if not cls._initialized:
            cls._lock = asyncio.Lock()
            cls._condition = asyncio.Condition(cls._lock)
            cls._initialized = True
            # Start cleanup task
            if cls._cleanup_task is None or cls._cleanup_task.done():
                cls._cleanup_task = asyncio.create_task(cls._cleanup_loop())
    
    @classmethod
    async def _cleanup_loop(cls):
        """Background task to clean up stale requests."""
        while True:
            try:
                await asyncio.sleep(cls._cleanup_interval)
                await cls._cleanup_stale_requests()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
    
    @classmethod
    async def _cleanup_stale_requests(cls):
        """Remove timed-out and stale requests."""
        await cls._ensure_initialized()
        now = datetime.now()
        
        async with cls._lock:
            stale_ids = []
            
            for request_id, request in cls._queue.items():
                # Check for queue timeout (waiting too long)
                if request.status == RequestStatus.WAITING:
                    if now - request.created_at > timedelta(seconds=cls._queue_timeout):
                        stale_ids.append(request_id)
                        logger.warning(f"Request {request_id} timed out in queue")
                
                # Check for processing timeout
                elif request.status == RequestStatus.PROCESSING:
                    if request.started_at and now - request.started_at > timedelta(seconds=cls._request_timeout):
                        stale_ids.append(request_id)
                        cls._active.discard(request_id)
                        logger.warning(f"Request {request_id} timed out during processing")
            
            # Remove stale requests
            for request_id in stale_ids:
                if request_id in cls._queue:
                    cls._queue[request_id].status = RequestStatus.TIMEOUT
                    del cls._queue[request_id]
            
            if stale_ids:
                cls._condition.notify_all()
    
    @classmethod
    async def create_request(
        cls, 
        course_id: str, 
        unit_numbers: list[int],
        user_id: Optional[str] = None
    ) -> str:
        """Create a new queue request and return request ID."""
        await cls._ensure_initialized()
        
        request_id = str(uuid.uuid4())
        request = QueueRequest(
            request_id=request_id,
            course_id=course_id,
            unit_numbers=unit_numbers,
            created_at=datetime.now(),
            user_id=user_id
        )
        
        async with cls._lock:
            cls._queue[request_id] = request
            logger.info(f"Created request {request_id} for {course_id} units {unit_numbers}")
        
        return request_id
    
    @classmethod
    async def get_queue_position(cls, request_id: str) -> int:
        """
        Get position in queue.
        Returns:
            0 = being processed
            >0 = position in queue
            -1 = not found
        """
        await cls._ensure_initialized()
        
        async with cls._lock:
            if request_id in cls._active:
                return 0
            
            if request_id not in cls._queue:
                return -1
            
            request = cls._queue[request_id]
            if request.status == RequestStatus.PROCESSING:
                return 0
            
            # Count requests ahead in queue (by creation time)
            request_time = request.created_at
            position = 0
            
            for rid, req in cls._queue.items():
                if rid != request_id and req.status == RequestStatus.WAITING:
                    if req.created_at < request_time:
                        position += 1
            
            # Add 1 to convert from 0-indexed to 1-indexed position
            return position + 1
    
    @classmethod
    async def get_estimated_wait_time(cls, request_id: str) -> Optional[int]:
        """Estimate wait time in seconds based on queue position."""
        await cls._ensure_initialized()
        
        position = await cls.get_queue_position(request_id)
        if position <= 0:
            return 0
        
        # Estimate ~60 seconds per request (this is a rough estimate)
        avg_processing_time = 60
        estimated_wait = (position // cls._max_concurrent) * avg_processing_time
        
        return estimated_wait
    
    @classmethod
    async def acquire(cls, request_id: str, timeout: Optional[float] = None) -> bool:
        """
        Wait for and acquire a processing slot.
        
        Args:
            request_id: The request ID to acquire
            timeout: Optional timeout in seconds
            
        Returns:
            True if slot acquired, False if timeout or cancelled
        """
        await cls._ensure_initialized()
        
        timeout = timeout or cls._queue_timeout
        start_time = datetime.now()
        
        async with cls._condition:
            while True:
                # Check if request still exists
                if request_id not in cls._queue:
                    logger.warning(f"Request {request_id} no longer in queue")
                    return False
                
                request = cls._queue[request_id]
                
                # Check if already processing
                if request_id in cls._active:
                    return True
                
                # Check for timeout
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed >= timeout:
                    logger.warning(f"Request {request_id} timed out waiting for slot")
                    request.status = RequestStatus.TIMEOUT
                    del cls._queue[request_id]
                    return False
                
                # Try to acquire slot
                if len(cls._active) < cls._max_concurrent:
                    cls._active.add(request_id)
                    request.status = RequestStatus.PROCESSING
                    request.started_at = datetime.now()
                    logger.info(f"Request {request_id} acquired slot ({len(cls._active)}/{cls._max_concurrent} active)")
                    return True
                
                # Wait for a slot to become available (with timeout)
                remaining_timeout = timeout - elapsed
                try:
                    await asyncio.wait_for(
                        cls._condition.wait(),
                        timeout=min(remaining_timeout, 5.0)  # Check every 5 seconds
                    )
                except asyncio.TimeoutError:
                    # Continue loop to check conditions again
                    pass
    
    @classmethod
    async def release(cls, request_id: str):
        """Release a processing slot."""
        await cls._ensure_initialized()
        
        async with cls._condition:
            cls._active.discard(request_id)
            
            if request_id in cls._queue:
                cls._queue[request_id].status = RequestStatus.COMPLETED
                del cls._queue[request_id]
            
            logger.info(f"Request {request_id} released slot ({len(cls._active)}/{cls._max_concurrent} active)")
            
            # Notify waiting requests that a slot is available
            cls._condition.notify_all()
    
    @classmethod
    async def cancel_request(cls, request_id: str) -> bool:
        """Cancel a queued request."""
        await cls._ensure_initialized()
        
        async with cls._condition:
            if request_id in cls._queue:
                request = cls._queue[request_id]
                
                # Can only cancel waiting requests
                if request.status == RequestStatus.WAITING:
                    request.status = RequestStatus.CANCELLED
                    del cls._queue[request_id]
                    logger.info(f"Request {request_id} cancelled")
                    cls._condition.notify_all()
                    return True
            
            return False
    
    @classmethod
    async def get_queue_status(cls) -> dict:
        """Get current queue status."""
        await cls._ensure_initialized()
        
        async with cls._lock:
            waiting_count = sum(
                1 for r in cls._queue.values() 
                if r.status == RequestStatus.WAITING
            )
            
            return {
                "queue_length": waiting_count,
                "active_count": len(cls._active),
                "max_concurrent": cls._max_concurrent,
                "total_requests": len(cls._queue)
            }
    
    @classmethod
    async def get_detailed_status(cls) -> dict:
        """Get detailed queue status for monitoring."""
        await cls._ensure_initialized()
        
        async with cls._lock:
            now = datetime.now()
            
            waiting_requests = []
            active_requests = []
            
            for request_id, request in cls._queue.items():
                req_info = {
                    "request_id": request_id[:8] + "...",  # Truncated for privacy
                    "course_id": request.course_id,
                    "units": request.unit_numbers,
                    "waiting_seconds": (now - request.created_at).total_seconds()
                }
                
                if request.status == RequestStatus.WAITING:
                    waiting_requests.append(req_info)
                elif request.status == RequestStatus.PROCESSING:
                    req_info["processing_seconds"] = (
                        (now - request.started_at).total_seconds() 
                        if request.started_at else 0
                    )
                    active_requests.append(req_info)
            
            return {
                "queue_length": len(waiting_requests),
                "active_count": len(active_requests),
                "max_concurrent": cls._max_concurrent,
                "waiting_requests": waiting_requests,
                "active_requests": active_requests
            }
    
    @classmethod
    def set_max_concurrent(cls, max_concurrent: int):
        """Update maximum concurrent requests (for runtime configuration)."""
        if max_concurrent >= 1:
            cls._max_concurrent = max_concurrent
            logger.info(f"Max concurrent requests set to {max_concurrent}")

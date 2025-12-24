// API client for communicating with the backend

import type { CoursesResponse, UnitsResponse, PracticeRequest, StreamChunk } from '../types';

const API_BASE = '/api/v1';

// Console styling for better visibility
const logStyles = {
  info: 'color: #2196F3; font-weight: bold',
  success: 'color: #4CAF50; font-weight: bold',
  error: 'color: #f44336; font-weight: bold',
  warn: 'color: #FF9800; font-weight: bold',
  data: 'color: #9C27B0',
};

export async function fetchCourses(): Promise<CoursesResponse> {
  console.log('%c[API] Fetching courses...', logStyles.info);
  const startTime = performance.now();
  
  const response = await fetch(`${API_BASE}/courses`);
  if (!response.ok) {
    console.error('%c[API] Failed to fetch courses', logStyles.error, { status: response.status });
    throw new Error('Failed to fetch courses');
  }
  
  const data = await response.json();
  const duration = (performance.now() - startTime).toFixed(0);
  console.log(`%c[API] ✓ Courses loaded (${duration}ms)`, logStyles.success, { 
    categoriesCount: Object.keys(data.categories || {}).length,
    coursesCount: data.courses?.length || 0
  });
  
  return data;
}

export async function fetchUnits(courseId: string): Promise<UnitsResponse> {
  console.log('%c[API] Fetching units...', logStyles.info, { courseId });
  const startTime = performance.now();
  
  const response = await fetch(`${API_BASE}/courses/${courseId}/units`);
  if (!response.ok) {
    console.error('%c[API] Failed to fetch units', logStyles.error, { courseId, status: response.status });
    throw new Error(`Failed to fetch units for ${courseId}`);
  }
  
  const data = await response.json();
  const duration = (performance.now() - startTime).toFixed(0);
  console.log(`%c[API] ✓ Units loaded (${duration}ms)`, logStyles.success, { 
    courseId,
    unitsCount: data.units?.length || 0
  });
  
  return data;
}

export async function* generatePracticeStream(
  request: PracticeRequest
): AsyncGenerator<StreamChunk, void, unknown> {
  console.log('%c[Generator] Starting practice generation...', logStyles.info);
  console.log('%c[Generator] Request:', logStyles.data, {
    course: request.course_id,
    units: request.unit_numbers,
    mcq: request.mcq_count,
    frq: request.frq_count,
    difficulty: request.difficulty
  });
  
  const startTime = performance.now();
  
  const response = await fetch(`${API_BASE}/practice/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    console.error('%c[Generator] Failed to start generation', logStyles.error, { status: response.status });
    throw new Error('Failed to start practice generation');
  }

  console.log('%c[Generator] Stream connected, receiving chunks...', logStyles.success);
  
  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('No response body');
  }

  const decoder = new TextDecoder();
  let buffer = '';
  let chunkCount = 0;
  let totalChars = 0;

  while (true) {
    const { done, value } = await reader.read();
    
    if (done) {
      const duration = ((performance.now() - startTime) / 1000).toFixed(1);
      console.log(`%c[Generator] ✓ Stream complete (${duration}s)`, logStyles.success, {
        totalChunks: chunkCount,
        totalChars
      });
      break;
    }
    
    buffer += decoder.decode(value, { stream: true });
    
    // Parse SSE events
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6));
          chunkCount++;
          if (data.content) {
            totalChars += data.content.length;
          }
          
          // Log queue messages
          if (data.is_queue_message) {
            console.log('%c[Generator] Queue status:', logStyles.warn, data.content);
          }
          
          yield data as StreamChunk;
        } catch {
          // Skip invalid JSON
        }
      }
    }
  }
}


// API client for communicating with the backend

import type { CoursesResponse, UnitsResponse, PracticeRequest, StreamChunk } from '../types';

const API_BASE = '/api/v1';

export async function fetchCourses(): Promise<CoursesResponse> {
  const response = await fetch(`${API_BASE}/courses`);
  if (!response.ok) {
    throw new Error('Failed to fetch courses');
  }
  return response.json();
}

export async function fetchUnits(courseId: string): Promise<UnitsResponse> {
  const response = await fetch(`${API_BASE}/courses/${courseId}/units`);
  if (!response.ok) {
    throw new Error(`Failed to fetch units for ${courseId}`);
  }
  return response.json();
}

export async function* generatePracticeStream(
  request: PracticeRequest
): AsyncGenerator<StreamChunk, void, unknown> {
  const response = await fetch(`${API_BASE}/practice/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error('Failed to start practice generation');
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('No response body');
  }

  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    
    if (done) break;
    
    buffer += decoder.decode(value, { stream: true });
    
    // Parse SSE events
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6));
          yield data as StreamChunk;
        } catch {
          // Skip invalid JSON
        }
      }
    }
  }
}


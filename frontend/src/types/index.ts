// TypeScript types for Practice Generator

export interface Course {
  id: string;
  name: string;
  units_count: number;
}

export interface ProgressCheck {
  mcq_count: number;
  frq_count: number;
  saq_count: number;
  mcq_description: string | null;
  frq_description: string | null;
  saq_description: string | null;
}

export interface Unit {
  unit_number: number;
  unit_title: string;
  exam_weight: string | null;
  ced_class_periods: string | null;
  topics_count: number;
  progress_check: ProgressCheck | null;
}

export interface CoursesResponse {
  courses: Course[];
}

export interface UnitsResponse {
  course_name: string;
  units: Unit[];
}

export type DifficultyLevel = 'easier' | 'ap_level' | 'harder';

export interface PracticeRequest {
  course_id: string;
  unit_numbers: number[];
  mcq_count: number;
  frq_count: number;
  difficulty: DifficultyLevel;
}

export interface PracticeResponse {
  course_name: string;
  unit_titles: string[];
  practice_content: string;
  mcq_count: number;
  frq_count: number;
  difficulty: string;
  generated_at: string;
}

export interface StreamChunk {
  content: string;
  is_complete: boolean;
  is_queue_message?: boolean;
}

export interface QueueStatus {
  position: number;
  queue_length: number;
  active_count: number;
  max_concurrent?: number;
  estimated_wait_seconds?: number;
}

export interface GenerationState {
  status: 'idle' | 'loading' | 'streaming' | 'complete' | 'error';
  content: string;
  error?: string;
}

export const DIFFICULTY_OPTIONS: { value: DifficultyLevel; label: string; description: string }[] = [
  { value: 'easier', label: 'Easier than AP', description: 'Foundational concepts, simpler questions' },
  { value: 'ap_level', label: 'AP Exam level', description: 'Match official AP exam difficulty' },
  { value: 'harder', label: 'Harder than AP', description: 'Advanced analysis, complex reasoning' },
];


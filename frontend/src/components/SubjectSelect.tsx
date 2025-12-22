// Subject selection dropdown component

import type { Course } from '../types';

interface SubjectSelectProps {
  courses: Course[];
  selectedId: string | null;
  onSelect: (courseId: string | null) => void;
  loading?: boolean;
  disabled?: boolean;
}

export function SubjectSelect({
  courses,
  selectedId,
  onSelect,
  loading = false,
  disabled = false,
}: SubjectSelectProps) {
  return (
    <div className="select-container">
      <label className="select-label">
        <span className="step-number">1</span>
        SELECT SUBJECT
      </label>
      <select
        className="select-input"
        value={selectedId || ''}
        onChange={(e) => onSelect(e.target.value || null)}
        disabled={disabled || loading}
      >
        <option value="">Select a subject</option>
        {courses.map((course) => (
          <option key={course.id} value={course.id}>
            {course.name} ({course.units_count} units)
          </option>
        ))}
      </select>
      {loading && <span className="select-loading">Loading...</span>}
    </div>
  );
}


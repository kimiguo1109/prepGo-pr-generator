// Custom hooks for course data

import { useState, useEffect } from 'react';
import { fetchCourses, fetchUnits } from '../api/client';
import type { Course, Unit } from '../types';

export function useCourses() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const response = await fetchCourses();
        setCourses(response.courses);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load courses');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return { courses, loading, error };
}

export function useUnits(courseId: string | null) {
  const [units, setUnits] = useState<Unit[]>([]);
  const [courseName, setCourseName] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!courseId) {
      setUnits([]);
      setCourseName('');
      return;
    }

    async function load(id: string) {
      try {
        setLoading(true);
        const response = await fetchUnits(id);
        setUnits(response.units);
        setCourseName(response.course_name);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load units');
        setUnits([]);
      } finally {
        setLoading(false);
      }
    }
    load(courseId);
  }, [courseId]);

  return { units, courseName, loading, error };
}


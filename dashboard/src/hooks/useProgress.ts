/**
 * Lesson progress tracking via localStorage.
 * Key: 'apexgold_progress' → JSON object { "1-1": true, "1-2": true, ... }
 */

import { useState, useCallback } from 'react';

const STORAGE_KEY = 'apexgold_progress';

function loadProgress(): Record<string, boolean> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    return JSON.parse(raw) as Record<string, boolean>;
  } catch {
    return {};
  }
}

function saveProgress(p: Record<string, boolean>) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(p));
  } catch { /* silent */ }
}

/** Check if a specific lesson is complete. */
export function useLessonComplete(moduleNum: number, lessonNum: number): boolean {
  const key = `${moduleNum}-${lessonNum}`;
  const p = loadProgress();
  return p[key] === true;
}

/** For use inside a lesson — returns state + markComplete action. */
export function useProgress(moduleNum: number, lessonNum: number) {
  const key = `${moduleNum}-${lessonNum}`;
  const [isComplete, setIsComplete] = useState(() => {
    const p = loadProgress();
    return p[key] === true;
  });

  const markComplete = useCallback(() => {
    const p = loadProgress();
    p[key] = true;
    saveProgress(p);
    setIsComplete(true);
  }, [key]);

  return { isComplete, markComplete };
}

/** Returns the full progress map — used on the Academy overview page. */
export function useAllProgress(): Record<string, boolean> {
  return loadProgress();
}

// Difficulty selection component

import type { DifficultyLevel } from '../types';
import { DIFFICULTY_OPTIONS } from '../types';

interface DifficultySelectProps {
  selected: DifficultyLevel;
  onSelect: (difficulty: DifficultyLevel) => void;
  disabled?: boolean;
}

export function DifficultySelect({
  selected,
  onSelect,
  disabled = false,
}: DifficultySelectProps) {
  return (
    <div className="difficulty-select">
      <label className="select-label">
        <span className="step-number">3</span>
        DIFFICULTY
        <span className="label-hint">Relative to the AP Exam</span>
      </label>
      
      <div className="difficulty-options">
        {DIFFICULTY_OPTIONS.map((option, index) => (
          <div
            key={option.value}
            className={`difficulty-option ${selected === option.value ? 'selected' : ''} ${disabled ? 'disabled' : ''}`}
            onClick={() => !disabled && onSelect(option.value)}
          >
            <div className="difficulty-icon">
              {index === 0 && <span className="icon-bar">▪</span>}
              {index === 1 && <span className="icon-bar">▪▪</span>}
              {index === 2 && <span className="icon-bar">▪▪▪</span>}
            </div>
            <div className="difficulty-label">{option.label}</div>
            <div className="difficulty-radio">
              {selected === option.value && <span className="radio-check">✓</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}


// Multi-select unit component

import type { Unit } from '../types';

interface UnitMultiSelectProps {
  units: Unit[];
  selectedUnits: number[];
  onSelect: (unitNumbers: number[]) => void;
  loading?: boolean;
  disabled?: boolean;
}

export function UnitMultiSelect({
  units,
  selectedUnits,
  onSelect,
  loading = false,
  disabled = false,
}: UnitMultiSelectProps) {
  const handleUnitToggle = (unitNumber: number) => {
    if (selectedUnits.includes(unitNumber)) {
      onSelect(selectedUnits.filter(u => u !== unitNumber));
    } else {
      onSelect([...selectedUnits, unitNumber].sort((a, b) => a - b));
    }
  };

  const handleSelectAll = () => {
    if (selectedUnits.length === units.length) {
      onSelect([]);
    } else {
      onSelect(units.map(u => u.unit_number));
    }
  };

  const allSelected = units.length > 0 && selectedUnits.length === units.length;

  return (
    <div className="unit-multi-select">
      <div className="unit-select-header">
        <label className="select-label">
          <span className="step-number">1</span>
          SELECT UNITS
        </label>
        <div className="unit-select-info">
          <span className="selected-count">Selected: {selectedUnits.length} units</span>
          <button 
            className="select-all-btn"
            onClick={handleSelectAll}
            disabled={disabled || loading || units.length === 0}
          >
            {allSelected ? 'Deselect All' : 'Select All'}
          </button>
        </div>
      </div>
      
      {loading && <div className="unit-loading">Loading units...</div>}
      
      {!loading && units.length === 0 && (
        <div className="unit-empty">Select a subject first</div>
      )}
      
      {!loading && units.length > 0 && (
        <div className="unit-grid">
          {units.map((unit) => {
            const isSelected = selectedUnits.includes(unit.unit_number);
            return (
              <div 
                key={unit.unit_number}
                className={`unit-card ${isSelected ? 'selected' : ''} ${disabled ? 'disabled' : ''}`}
                onClick={() => !disabled && handleUnitToggle(unit.unit_number)}
              >
                <div className="unit-checkbox">
                  {isSelected && <span className="checkmark">✓</span>}
                </div>
                <div className="unit-info">
                  <div className="unit-title">Unit {unit.unit_number}: {unit.unit_title}</div>
                  {unit.exam_weight && (
                    <div className="unit-weight">{unit.exam_weight}</div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}


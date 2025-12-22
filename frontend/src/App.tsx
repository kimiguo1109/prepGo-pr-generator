// Main App component for Practice Generator

import { useState, useEffect } from 'react';
import { SubjectSelect } from './components/SubjectSelect';
import { UnitMultiSelect } from './components/UnitMultiSelect';
import { QuestionCountControl } from './components/QuestionCountControl';
import { DifficultySelect } from './components/DifficultySelect';
import { GenerateButton } from './components/GenerateButton';
import { PracticeDisplay } from './components/PracticeDisplay';
import { useCourses, useUnits } from './hooks/useCourses';
import { usePracticeGenerator } from './hooks/usePracticeGenerator';
import type { DifficultyLevel } from './types';
import './App.css';

function App() {
  const [selectedCourse, setSelectedCourse] = useState<string | null>(null);
  const [selectedUnits, setSelectedUnits] = useState<number[]>([]);
  const [mcqCount, setMcqCount] = useState(15);
  const [frqCount, setFrqCount] = useState(2);
  const [difficulty, setDifficulty] = useState<DifficultyLevel>('ap_level');
  const [editedContent, setEditedContent] = useState<string>('');

  const { courses, loading: coursesLoading } = useCourses();
  const { units, loading: unitsLoading } = useUnits(selectedCourse);
  const { state: practiceState, generate, reset } = usePracticeGenerator();

  // Sync edited content with generated content
  useEffect(() => {
    if (practiceState.status === 'complete') {
      setEditedContent(practiceState.content);
    }
  }, [practiceState.status, practiceState.content]);

  const handleCourseChange = (courseId: string | null) => {
    setSelectedCourse(courseId);
    setSelectedUnits([]);
    reset();
  };

  const handleUnitsChange = (unitNumbers: number[]) => {
    setSelectedUnits(unitNumbers);
    reset();
  };

  const handleGenerate = () => {
    if (selectedCourse && selectedUnits.length > 0) {
      generate({
        course_id: selectedCourse,
        unit_numbers: selectedUnits,
        mcq_count: mcqCount,
        frq_count: frqCount,
        difficulty: difficulty,
      });
    }
  };

  const isGenerating = practiceState.status === 'loading' || practiceState.status === 'streaming';
  const canGenerate = selectedCourse && selectedUnits.length > 0 && !isGenerating;

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <div className="header-left">
            <h1>📝 Practice Generator</h1>
            <p>Create customized AP practice question sets</p>
          </div>
          <div className="preview-badge">
            <span className="preview-icon">👁️</span>
            Question Preview
            <span className="preview-mode">PREVIEW MODE</span>
          </div>
        </div>
      </header>

      <main className="main">
        <div className="layout">
          {/* Left Panel - Controls */}
          <aside className="controls-panel">
            <div className="controls-section">
              <SubjectSelect
                courses={courses}
                selectedId={selectedCourse}
                onSelect={handleCourseChange}
                loading={coursesLoading}
                disabled={isGenerating}
              />
            </div>

            <div className="controls-section">
              <UnitMultiSelect
                units={units}
                selectedUnits={selectedUnits}
                onSelect={handleUnitsChange}
                loading={unitsLoading}
                disabled={isGenerating}
              />
            </div>

            <div className="controls-section">
              <QuestionCountControl
                mcqCount={mcqCount}
                frqCount={frqCount}
                onMcqChange={setMcqCount}
                onFrqChange={setFrqCount}
                disabled={isGenerating}
              />
            </div>

            <div className="controls-section">
              <DifficultySelect
                selected={difficulty}
                onSelect={setDifficulty}
                disabled={isGenerating}
              />
            </div>

            <div className="controls-section">
              <GenerateButton
                onClick={handleGenerate}
                disabled={!canGenerate}
                loading={isGenerating}
              />
            </div>
          </aside>

          {/* Right Panel - Preview */}
          <section className="preview-panel">
            <PracticeDisplay
              state={{
                ...practiceState,
                content: practiceState.status === 'complete'
                  ? (editedContent || practiceState.content)
                  : practiceState.content
              }}
              onContentChange={setEditedContent}
              onSave={(content) => {
                setEditedContent(content);
                console.log('Content saved:', content.length, 'chars');
              }}
            />
          </section>
        </div>
      </main>

      <footer className="footer">
        <p>PrepGo Practice Generator © 2025 | Powered by Gemini AI</p>
      </footer>
    </div>
  );
}

export default App;


// Question count control component

interface QuestionCountControlProps {
  mcqCount: number;
  frqCount: number;
  onMcqChange: (count: number) => void;
  onFrqChange: (count: number) => void;
  disabled?: boolean;
}

export function QuestionCountControl({
  mcqCount,
  frqCount,
  onMcqChange,
  onFrqChange,
  disabled = false,
}: QuestionCountControlProps) {
  const totalQuestions = mcqCount + frqCount;

  const handleIncrement = (type: 'mcq' | 'frq') => {
    if (type === 'mcq' && mcqCount < 50) {
      onMcqChange(mcqCount + 1);
    } else if (type === 'frq' && frqCount < 10) {
      onFrqChange(frqCount + 1);
    }
  };

  const handleDecrement = (type: 'mcq' | 'frq') => {
    if (type === 'mcq' && mcqCount > 1) {
      onMcqChange(mcqCount - 1);
    } else if (type === 'frq' && frqCount > 0) {
      onFrqChange(frqCount - 1);
    }
  };

  return (
    <div className="question-count-control">
      <div className="count-header">
        <label className="select-label">
          <span className="step-number">2</span>
          QUESTION COUNT
        </label>
        <div className="total-badge">
          Total: {totalQuestions} questions
        </div>
      </div>

      <div className="count-controls">
        <div className="count-item">
          <span className="count-label">MCQ Questions</span>
          <div className="count-input-group">
            <button 
              className="count-btn"
              onClick={() => handleDecrement('mcq')}
              disabled={disabled || mcqCount <= 1}
            >
              −
            </button>
            <input
              type="number"
              className="count-input"
              value={mcqCount}
              onChange={(e) => {
                const val = parseInt(e.target.value) || 1;
                onMcqChange(Math.min(50, Math.max(1, val)));
              }}
              min={1}
              max={50}
              disabled={disabled}
            />
            <button 
              className="count-btn"
              onClick={() => handleIncrement('mcq')}
              disabled={disabled || mcqCount >= 50}
            >
              +
            </button>
          </div>
        </div>

        <div className="count-item">
          <span className="count-label">FRQ Questions</span>
          <div className="count-input-group">
            <button 
              className="count-btn"
              onClick={() => handleDecrement('frq')}
              disabled={disabled || frqCount <= 0}
            >
              −
            </button>
            <input
              type="number"
              className="count-input"
              value={frqCount}
              onChange={(e) => {
                const val = parseInt(e.target.value) || 0;
                onFrqChange(Math.min(10, Math.max(0, val)));
              }}
              min={0}
              max={10}
              disabled={disabled}
            />
            <button 
              className="count-btn"
              onClick={() => handleIncrement('frq')}
              disabled={disabled || frqCount >= 10}
            >
              +
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}


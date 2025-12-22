// Generate button component

interface GenerateButtonProps {
  onClick: () => void;
  disabled?: boolean;
  loading?: boolean;
}

export function GenerateButton({
  onClick,
  disabled = false,
  loading = false,
}: GenerateButtonProps) {
  return (
    <div className="generate-buttons">
      <button
        className="reset-button"
        onClick={() => window.location.reload()}
        disabled={loading}
      >
        Reset
      </button>
      <button
        className="generate-button"
        onClick={onClick}
        disabled={disabled || loading}
      >
        {loading && <span className="spinner" />}
        {loading ? 'Generating...' : 'Generate Practice Set'}
      </button>
    </div>
  );
}


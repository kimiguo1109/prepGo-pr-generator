// Practice display component with markdown rendering

import { useState, useEffect, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import type { GenerationState } from '../types';

interface PracticeDisplayProps {
  state: GenerationState;
  onContentChange?: (content: string) => void;
  onSave?: (content: string) => void;
}

// Fun loading messages
const LOADING_MESSAGES = [
  { emoji: '🧠', text: 'Analyzing curriculum standards...' },
  { emoji: '📚', text: 'Reading through course materials...' },
  { emoji: '✍️', text: 'Crafting challenging questions...' },
  { emoji: '🔬', text: 'Designing stimulus materials...' },
  { emoji: '🎯', text: 'Calibrating difficulty levels...' },
  { emoji: '📝', text: 'Writing answer explanations...' },
  { emoji: '✨', text: 'Polishing your practice set...' },
];

// Queue waiting messages
const QUEUE_MESSAGES = [
  { emoji: '⏳', text: 'Waiting in queue...' },
  { emoji: '🔄', text: 'Processing other requests...' },
  { emoji: '⌛', text: 'Your turn is coming up...' },
  { emoji: '🎟️', text: 'Reserved your spot...' },
];

export function PracticeDisplay({
  state,
  onContentChange,
  onSave,
}: PracticeDisplayProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState('');
  const [loadingMessageIndex, setLoadingMessageIndex] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [startTime, setStartTime] = useState<number | null>(null);

  // Track elapsed time during generation
  useEffect(() => {
    if (state.status === 'loading' || state.status === 'streaming') {
      if (!startTime) {
        setStartTime(Date.now());
      }
      const timer = setInterval(() => {
        setElapsedTime(Math.floor((Date.now() - (startTime || Date.now())) / 1000));
      }, 1000);
      return () => clearInterval(timer);
    } else {
      setStartTime(null);
    }
  }, [state.status, startTime]);

  // Rotate loading messages
  useEffect(() => {
    if (state.status === 'loading') {
      const timer = setInterval(() => {
        setLoadingMessageIndex((prev) => (prev + 1) % LOADING_MESSAGES.length);
      }, 3000);
      return () => clearInterval(timer);
    }
  }, [state.status]);

  // Sync edit content
  useEffect(() => {
    if (state.status === 'complete' && !isEditing) {
      setEditContent(state.content);
    }
  }, [state.content, state.status, isEditing]);

  const handleSave = () => {
    setIsEditing(false);
    onContentChange?.(editContent);
    onSave?.(editContent);
  };

  const handleCopy = async () => {
    const textToCopy = editContent || state.content;
    
    // Try modern clipboard API first
    if (navigator.clipboard && window.isSecureContext) {
      try {
        await navigator.clipboard.writeText(textToCopy);
        alert('Content copied to clipboard!');
        return;
      } catch {
        // Fall through to fallback
      }
    }
    
    // Fallback for HTTP or older browsers
    try {
      const textArea = document.createElement('textarea');
      textArea.value = textToCopy;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      textArea.style.top = '-999999px';
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      
      const successful = document.execCommand('copy');
      document.body.removeChild(textArea);
      
      if (successful) {
        alert('Content copied to clipboard!');
      } else {
        alert('Failed to copy. Please select and copy manually.');
      }
    } catch {
      alert('Failed to copy. Please select and copy manually.');
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Calculate estimated progress
  const estimatedProgress = useMemo(() => {
    if (state.status === 'streaming') {
      // Rough estimate based on content length
      const expectedLength = 15000; // Typical practice set length
      return Math.min(95, Math.round((state.content.length / expectedLength) * 100));
    }
    return 0;
  }, [state.status, state.content.length]);

  // Idle state
  if (state.status === 'idle') {
    return (
      <div className="practice-display">
        <div className="practice-placeholder">
          <div className="placeholder-icon">📝</div>
          <h3>Question Preview</h3>
          <p>Configure your practice set on the left, then click "Generate Practice Set" to begin.</p>
        </div>
      </div>
    );
  }

  // Loading state (including queue waiting)
  if (state.status === 'loading') {
    // Check if content contains queue message
    const isInQueue = state.content.includes('in queue') || state.content.includes('#');
    const queueMatch = state.content.match(/#(\d+)/);
    const queuePosition = queueMatch ? parseInt(queueMatch[1]) : 0;
    
    const currentMessage = isInQueue 
      ? QUEUE_MESSAGES[loadingMessageIndex % QUEUE_MESSAGES.length]
      : LOADING_MESSAGES[loadingMessageIndex];
    
    return (
      <div className="practice-display">
        <div className="practice-loading">
          <div className="loading-message-container">
            {isInQueue && queuePosition > 0 && (
              <div className="queue-position-badge">
                <span className="queue-number">#{queuePosition}</span>
                <span className="queue-label">in queue</span>
              </div>
            )}
            <div className="loading-message">
              <span className="loading-emoji">{currentMessage.emoji}</span>
              {currentMessage.text}
            </div>
            <div className="loading-hint">
              {isInQueue 
                ? 'Multiple users online. Thanks for waiting!' 
                : 'This usually takes 30-60 seconds'}
            </div>
            <div className="loading-timer-bar">
              <span className="loading-timer">{formatTime(elapsedTime)}</span>
              <div className="thinking-dots">
                <span>.</span><span>.</span><span>.</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (state.status === 'error') {
    return (
      <div className="practice-display">
        <div className="practice-error">
          <span className="error-icon">⚠️</span>
          <h3>Generation Failed</h3>
          <p>{state.error}</p>
        </div>
      </div>
    );
  }

  // Streaming or Complete state
  const displayContent = isEditing ? editContent : (state.content || '');

  return (
    <div className="practice-display">
      {/* Streaming indicator */}
      {state.status === 'streaming' && (
        <div className="streaming-indicator">
          <div className="streaming-header">
            <span className="pulse" />
            Generating Practice Set...
            <span className="elapsed-time">{formatTime(elapsedTime)}</span>
          </div>
          <div className="progress-bar-wrapper">
            <div className="progress-bar-container">
              <div 
                className="progress-bar-fill" 
                style={{ width: `${estimatedProgress}%` }}
              />
            </div>
            <span className="progress-percentage">{estimatedProgress}%</span>
          </div>
        </div>
      )}

      {/* Complete banner */}
      {state.status === 'complete' && (
        <div className="practice-complete-banner">
          ✅ Practice Set Generated Successfully!
        </div>
      )}

      {/* Toolbar */}
      {state.status === 'complete' && (
        <div className="editor-toolbar">
          {isEditing ? (
            <>
              <button className="save-button" onClick={handleSave}>
                💾 Save
              </button>
              <button className="cancel-button" onClick={() => setIsEditing(false)}>
                Cancel
              </button>
            </>
          ) : (
            <>
              <button className="edit-button" onClick={() => setIsEditing(true)}>
                ✏️ Edit
              </button>
              <button className="copy-button" onClick={handleCopy}>
                📋 Copy
              </button>
              <button className="print-button" onClick={handlePrint}>
                🖨️ Print
              </button>
            </>
          )}
        </div>
      )}

      {/* Content */}
      <div className="practice-content">
        {isEditing ? (
          <div className="editor-container">
            <textarea
              className="markdown-textarea"
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
            />
            <div className="preview-container">
              <div className="preview-label">Preview</div>
              <div className="markdown-preview">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm, remarkMath]}
                  rehypePlugins={[rehypeKatex]}
                >
                  {editContent}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        ) : (
          <div className="markdown-content">
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkMath]}
              rehypePlugins={[rehypeKatex]}
            >
              {displayContent}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}


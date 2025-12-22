// Custom hook for practice generation

import { useState, useCallback } from 'react';
import { generatePracticeStream } from '../api/client';
import type { PracticeRequest, GenerationState } from '../types';

export function usePracticeGenerator() {
  const [state, setState] = useState<GenerationState>({
    status: 'idle',
    content: '',
  });

  const generate = useCallback(async (request: PracticeRequest) => {
    setState({ status: 'loading', content: '' });

    try {
      let content = '';
      
      for await (const chunk of generatePracticeStream(request)) {
        if (chunk.is_complete) {
          setState({ status: 'complete', content });
          return;
        }
        
        // Skip queue messages and chunks without content
        if (!chunk.is_queue_message && chunk.content) {
          content += chunk.content;
        }
        
        setState({ 
          status: chunk.is_queue_message ? 'loading' : 'streaming', 
          content 
        });
      }
      
      // If we exit the loop without is_complete, still mark as complete
      setState({ status: 'complete', content });
      
    } catch (error) {
      setState({
        status: 'error',
        content: '',
        error: error instanceof Error ? error.message : 'Generation failed',
      });
    }
  }, []);

  const reset = useCallback(() => {
    setState({ status: 'idle', content: '' });
  }, []);

  return { state, generate, reset };
}


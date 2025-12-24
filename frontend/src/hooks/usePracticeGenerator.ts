// Custom hook for practice generation

import { useState, useCallback } from 'react';
import { generatePracticeStream } from '../api/client';
import type { PracticeRequest, GenerationState } from '../types';

// Console styling
const logStyles = {
  info: 'color: #2196F3; font-weight: bold',
  success: 'color: #4CAF50; font-weight: bold',
  error: 'color: #f44336; font-weight: bold',
  state: 'color: #673AB7',
};

export function usePracticeGenerator() {
  const [state, setState] = useState<GenerationState>({
    status: 'idle',
    content: '',
  });

  const generate = useCallback(async (request: PracticeRequest) => {
    console.log('%c[Hook] Generate called', logStyles.info, { request });
    console.log('%c[Hook] State → loading', logStyles.state);
    setState({ status: 'loading', content: '' });

    const startTime = performance.now();

    try {
      let content = '';
      let chunkCount = 0;
      
      for await (const chunk of generatePracticeStream(request)) {
        if (chunk.is_complete) {
          const duration = ((performance.now() - startTime) / 1000).toFixed(1);
          console.log(`%c[Hook] ✓ Generation complete (${duration}s)`, logStyles.success, {
            contentLength: content.length,
            totalChunks: chunkCount
          });
          console.log('%c[Hook] State → complete', logStyles.state);
          setState({ status: 'complete', content });
          return;
        }
        
        // Skip queue messages and chunks without content
        if (!chunk.is_queue_message && chunk.content) {
          content += chunk.content;
          chunkCount++;
        }
        
        const newStatus = chunk.is_queue_message ? 'loading' : 'streaming';
        setState({ 
          status: newStatus, 
          content 
        });
      }
      
      // If we exit the loop without is_complete, still mark as complete
      const duration = ((performance.now() - startTime) / 1000).toFixed(1);
      console.log(`%c[Hook] ✓ Stream ended (${duration}s)`, logStyles.success, {
        contentLength: content.length
      });
      console.log('%c[Hook] State → complete', logStyles.state);
      setState({ status: 'complete', content });
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Generation failed';
      console.error('%c[Hook] ✗ Generation failed', logStyles.error, { error: errorMessage });
      console.log('%c[Hook] State → error', logStyles.state);
      setState({
        status: 'error',
        content: '',
        error: errorMessage,
      });
    }
  }, []);

  const reset = useCallback(() => {
    console.log('%c[Hook] Reset called', logStyles.info);
    console.log('%c[Hook] State → idle', logStyles.state);
    setState({ status: 'idle', content: '' });
  }, []);

  return { state, generate, reset };
}


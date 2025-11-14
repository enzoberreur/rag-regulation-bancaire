import { useEffect, useState } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Hook to check if backend is available
 */
export function useBackendHealth() {
  const [isBackendReady, setIsBackendReady] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/health/`, {
          method: 'GET',
          signal: AbortSignal.timeout(3000), // 3 second timeout
        });
        
        if (response.ok) {
          setIsBackendReady(true);
          setIsChecking(false);
        } else {
          setIsBackendReady(false);
          setIsChecking(false);
        }
      } catch (error) {
        setIsBackendReady(false);
        setIsChecking(false);
      }
    };

    // Check immediately
    checkBackend();

    // Then check every 2 seconds until backend is ready
    const interval = setInterval(() => {
      if (!isBackendReady) {
        checkBackend();
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [isBackendReady]);

  return { isBackendReady, isChecking };
}


import { useState, useEffect } from 'react';
import { api } from '../api/client';
import { HealthResponse } from '../types/api';

export function useHealth() {
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    let mounted = true;
    const check = async () => {
      try {
        const res = await api.checkHealth();
        if (mounted) setHealth(res);
      } catch (e) {
        if (mounted) setHealth({ status: 'UNHEALTHY', version: '', uptime: 0 });
      }
    };
    
    check();
    const interval = setInterval(check, 30000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return health;
}

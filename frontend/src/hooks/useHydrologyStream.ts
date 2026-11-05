import { useEffect, useState } from 'react';
import {
  connectHydrologySocket,
  type GaugeObs,
} from '../layers/GaugeDeckLayer';

export function useHydrologyStream(wsBase = 'ws://127.0.0.1:8000') {
  const [observations, setObservations] = useState<GaugeObs[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const ws = connectHydrologySocket(wsBase, setObservations);
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    return () => ws.close();
  }, [wsBase]);

  return { observations, connected };
}

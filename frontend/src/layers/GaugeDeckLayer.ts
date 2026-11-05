/**
 * Deck.gl ScatterplotLayer for live NAVD88 gauge points.
 * Expects WebSocket messages of type "gauge_fabric".
 */
import { ScatterplotLayer } from '@deck.gl/layers';

export type GaugeObs = {
  station_id: string;
  station_name: string;
  agency: string;
  gage_height_ft: number | null;
  gage_zero_navd88_ft: number;
  derived_wse_navd88_ft: number | null;
  observation_time_utc: string;
  status: string;
  /** lon/lat for map — set by client geocode or station registry */
  longitude?: number;
  latitude?: number;
};

/** Approximate station positions (WGS84) near confluence */
export const STATION_LONLAT: Record<string, [number, number]> = {
  '03381700': [-87.945, 38.13], // New Harmony
  '03322000': [-87.95, 37.79], // J.T. Myers
  '03322130': [-88.13, 37.70], // Old Shawneetown
};

export function buildGaugeLayer(
  observations: GaugeObs[],
  id = 'ptdt-gauges'
): ScatterplotLayer {
  const data = observations.map((o) => {
    const ll = STATION_LONLAT[o.station_id] ?? [-87.9, 37.95];
    return {
      ...o,
      position: [ll[0], ll[1]] as [number, number],
      wse: o.derived_wse_navd88_ft ?? 0,
      live: o.status === 'LIVE OBSERVATION',
    };
  });

  return new ScatterplotLayer({
    id,
    data,
    getPosition: (d: { position: [number, number] }) => d.position,
    getRadius: 800,
    radiusUnits: 'meters',
    getFillColor: (d: { live: boolean }) =>
      d.live ? [0, 180, 255, 200] : [128, 128, 128, 160],
    pickable: true,
    updateTriggers: {
      getFillColor: data.map((d) => d.live),
    },
  });
}

export function connectHydrologySocket(
  baseUrl = 'ws://127.0.0.1:8000',
  onFabric: (obs: GaugeObs[]) => void
): WebSocket {
  const ws = new WebSocket(`${baseUrl}/ws/hydrology`);
  ws.onmessage = (ev) => {
    try {
      const msg = JSON.parse(ev.data as string);
      if (msg.type === 'gauge_fabric' && Array.isArray(msg.observations)) {
        onFabric(msg.observations as GaugeObs[]);
      }
    } catch {
      /* ignore */
    }
  };
  const ping = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) ws.send('ping');
  }, 25000);
  ws.onclose = () => clearInterval(ping);
  return ws;
}

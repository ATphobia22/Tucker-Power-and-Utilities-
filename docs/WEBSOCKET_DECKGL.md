# WebSocket streaming + Deck.gl

## Backend

- Endpoint: `WS /ws/hydrology`
- Polls `TriStateDataFabric` every 30s
- Payload: `{ type: "gauge_fabric", observations: [...] }`

Register in `backend/main.py`:

```python
from backend.streaming.ws_hydrology import router as ws_hydro_router
app.include_router(ws_hydro_router)
```

## Frontend (Deck.gl)

```ts
import { buildGaugeLayer } from './layers/GaugeDeckLayer';
import { useHydrologyStream } from './hooks/useHydrologyStream';

const { observations } = useHydrologyStream();
const layers = [buildGaugeLayer(observations)];
// pass layers into <DeckGL layers={layers} ... />
```

Install: `npm i @deck.gl/core @deck.gl/layers maplibre-gl`

## Explore further

| Layer | Use |
|-------|-----|
| `ScatterplotLayer` | Live gauges (done) |
| `GeoJsonLayer` | FEMA SFHA from `/geofabric` |
| `TerrainLayer` / quantized mesh | `engine/tiles_generator.py` output |
| `Tile3DLayer` | 3D Tiles / b3dm |

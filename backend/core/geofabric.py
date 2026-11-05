"""Geospatial GeoFabric — OpenFEMA NFHL SFHA polygons in EPSG:2966."""
from __future__ import annotations

from typing import Any, Dict

import httpx

FEMA_NFHL_ARCGIS_URL = (
    "https://hazards.fema.gov/gis/nfhl/rest/services/public/NFHL/MapServer/28/query"
)


class GeoFabricIngestor:
    @staticmethod
    async def fetch_fema_firm_panel_geometry(bbox_epsg2966: str) -> Dict[str, Any]:
        """Query OpenFEMA ArcGIS REST for SFHA flood-zone polygons."""
        params = {
            "where": "1=1",
            "geometry": bbox_epsg2966,
            "geometryType": "esriGeometryEnvelope",
            "inSR": "2966",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "FLD_ZONE,ZONE_SUBTY,STATIC_BFE",
            "returnGeometry": "true",
            "f": "geojson",
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    FEMA_NFHL_ARCGIS_URL, params=params, timeout=15.0
                )
                if response.status_code == 200:
                    return response.json()
            except Exception as err:
                print(f"Error querying OpenFEMA GeoFabric: {err}")
        return {"type": "FeatureCollection", "features": []}


if __name__ == "__main__":
    import asyncio

    # Point Township / Wabash confluence approx bbox (EPSG:2966 Indiana East)
    bbox = "2900000,1200000,2950000,1250000"
    geojson_data = asyncio.run(
        GeoFabricIngestor.fetch_fema_firm_panel_geometry(bbox)
    )
    print(f"Retrieved {len(geojson_data.get('features', []))} SFHA features.")

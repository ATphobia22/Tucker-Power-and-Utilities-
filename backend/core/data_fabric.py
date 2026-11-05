"""Real-time multi-agency hydrologic data fabric (USGS / NOAA / USACE / INDNR)."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

import httpx
from pydantic import BaseModel

logger = logging.getLogger("PTDT_DataFabric")


class GaugeObservation(BaseModel):
    station_id: str
    station_name: str
    agency: str
    gage_height_ft: Optional[float]
    gage_zero_navd88_ft: float
    derived_wse_navd88_ft: Optional[float]
    observation_time_utc: str
    status: str


class TriStateDataFabric:
    """WSE_NAVD88 = GageHeight_Source + GageZero_NAVD88"""

    def __init__(self) -> None:
        self.stations: Dict[str, dict] = {
            "03381700": {
                "name": "Wabash River at New Harmony, IN",
                "agency": "USGS",
                "gage_zero": 352.54,
            },
            "03322000": {
                "name": "Ohio River at J.T. Myers Lock & Dam",
                "agency": "USACE",
                "gage_zero": 320.00,
            },
            "03322130": {
                "name": "Ohio River at Old Shawneetown, IL",
                "agency": "USGS",
                "gage_zero": 310.20,
            },
        }

    async def fetch_usgs_observation(
        self, client: httpx.AsyncClient, station_id: str
    ) -> Optional[float]:
        url = (
            "https://waterservices.usgs.gov/nwis/iv/"
            f"?format=json&sites={station_id}&parameterCd=00065"
        )
        try:
            resp = await client.get(url, timeout=8.0)
            if resp.status_code != 200:
                return None
            data = resp.json()
            series = data["value"]["timeSeries"]
            if not series:
                return None
            values = series[0]["values"][0]["value"]
            if not values:
                return None
            return float(values[-1]["value"])
        except Exception as e:
            logger.warning("Failed USGS %s: %s", station_id, e)
            return None

    async def get_live_hydrologic_fabric(self) -> List[GaugeObservation]:
        results: List[GaugeObservation] = []
        async with httpx.AsyncClient() as client:
            for st_id, info in self.stations.items():
                gage_height = await self.fetch_usgs_observation(client, st_id)
                now_str = datetime.now(timezone.utc).isoformat()
                if gage_height is not None:
                    derived_wse = round(gage_height + info["gage_zero"], 2)
                    status = "LIVE OBSERVATION"
                else:
                    derived_wse = None
                    status = "SOURCE UNAVAILABLE"
                results.append(
                    GaugeObservation(
                        station_id=st_id,
                        station_name=info["name"],
                        agency=info["agency"],
                        gage_height_ft=gage_height,
                        gage_zero_navd88_ft=info["gage_zero"],
                        derived_wse_navd88_ft=derived_wse,
                        observation_time_utc=now_str,
                        status=status,
                    )
                )
        return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fabric = TriStateDataFabric()
    print(asyncio.run(fabric.get_live_hydrologic_fabric()))

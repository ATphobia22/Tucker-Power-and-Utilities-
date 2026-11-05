"""
PTDT v33 — Sovereign FastAPI Backend
Telemetry → QEC → Hydrodynamics → HEC-RAS → Governance → Regulatory Package
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PTDT.v33.Main")

app = FastAPI(
    title="PTDT v33 Tri-State Sovereign Core",
    version="33.0.0",
    description="13101 Bonebank Road — Archimedes Line Phase I",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    from fastapi.staticfiles import StaticFiles
    app.mount("/tilesets", StaticFiles(directory="data/tilesets"), name="tilesets")
    app.mount("/splats", StaticFiles(directory="data/splats"), name="splats")
    app.mount("/geo", StaticFiles(directory="data/geo"), name="geo")
except Exception:
    pass

try:
    from backend.routers.sovereign_api import router as sovereign_router
    app.include_router(sovereign_router)
except Exception as exc:
    logger.warning("sovereign_router unavailable: %s", exc)
    sovereign_router = None

try:
    from backend.streaming.ws_hydrology import router as ws_hydro_router
    app.include_router(ws_hydro_router)
except Exception as exc:
    logger.warning("ws_hydrology unavailable: %s", exc)

try:
    from backend.routers.grants import router as grants_router
    app.include_router(grants_router)
except Exception as exc:
    logger.warning("grants router unavailable: %s", exc)

_engine = None
_gov = None
_bridge = None
_gis = None
_daubert = None
_hecras = None

try:
    from backend.physics.hydrodynamics import ArchimedesEngine, HydraulicState
    from backend.physics.hecras_coupler import HECRASCoupler
    from backend.physics.qec_filter import decode_sensor_noise
    from backend.cognitive.governance_tristate import TriStateLegalComplianceGovernor
    from backend.services.gis_data_aggregator import GISDataAggregator
    from backend.services.daubert_engine import ArchimedesDaubertEngine

    _engine = ArchimedesEngine()
    _gov = TriStateLegalComplianceGovernor()
    _gis = GISDataAggregator()
    _daubert = ArchimedesDaubertEngine()
    _hecras = HECRASCoupler()
except Exception as exc:
    logger.warning("partial engine init: %s", exc)

    def decode_sensor_noise():
        return {"status": "ORDER_LOCKED", "mode": "mock"}

try:
    from core.telemetry.usgs_telemetry_bridge import StateDataHarvestBridge
    _bridge = StateDataHarvestBridge()
except Exception as exc:
    logger.warning("telemetry bridge unavailable: %s", exc)


class SimulationPayload(BaseModel):
    usgs_stage_ft: float = Field(381.2, ge=300, le=450)
    discharge_cfs: float = Field(142000, gt=0)


class PackagePayload(BaseModel):
    berm_length_ft: float = 850.0
    berm_width_ft: float = 12.0
    berm_height_ft: float = 4.5
    output_dir: str = "render_output/v33_portal"


@app.get("/api/v1/health")
def health() -> Dict[str, Any]:
    return {
        "status": "OK",
        "version": "PTDT-v33",
        "anchor": "13101 Bonebank Road, Point Township, Posey County, IN",
        "datum": "NAVD 88",
        "bfe_ft": 375.0,
        "lag_ft": 377.2,
        "ffe_ft": 382.5,
        "berm_crest_ft": 379.8,
        "max_rise_ft": 0.14,
        "v_net_cy": -21500,
        "bcr": 1.41,
        "engines": {
            "hydro": _engine is not None,
            "governance": _gov is not None,
            "hecras": _hecras is not None,
            "telemetry": _bridge is not None,
            "sovereign_router": sovereign_router is not None,
        },
    }


@app.get("/api/v1/freeboard")
def freeboard() -> Dict[str, Any]:
    if _engine is None:
        raise HTTPException(status_code=503, detail="Hydro engine unavailable")
    return _engine.freeboard_vector()


@app.get("/api/v1/telemetry/myers")
def telemetry_myers() -> Dict[str, Any]:
    if _bridge is None:
        raise HTTPException(status_code=503, detail="Telemetry bridge unavailable")
    payload = _bridge.fetch_john_t_myers()
    data = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    data["qec"] = decode_sensor_noise()
    return data


@app.get("/api/v1/telemetry/wabash")
def telemetry_wabash() -> Dict[str, Any]:
    if _bridge is None:
        raise HTTPException(status_code=503, detail="Telemetry bridge unavailable")
    stage = _bridge.fetch_usgs_river_stage("03378500")
    return {
        "station": "03378500",
        "name": "Wabash River at New Harmony",
        "stage_ft": stage,
        "qec": decode_sensor_noise(),
    }


@app.post("/api/v1/twin/simulation")
def twin_simulation(body: SimulationPayload) -> Dict[str, Any]:
    if _engine is None or _hecras is None or _gov is None:
        raise HTTPException(status_code=503, detail="Simulation engines unavailable")
    stage = body.usgs_stage_ft
    flow = body.discharge_cfs
    qec = decode_sensor_noise()
    if qec.get("status") == "UNSTABLE":
        raise HTTPException(status_code=422, detail="QEC channel unstable — abort simulation")
    sim = _engine.run_simulation(stage, flow)
    hs = sim["hydraulic_state"]
    hec = _hecras.compute_2d_flood_extent(
        upstream_stage_ft=stage,
        downstream_stage_ft=stage - 0.5,
        discharge_cfs=flow,
    )
    gov_state = _gov.evaluate_tri_state_compliance(hs, stage)
    receipt = None
    if _daubert is not None:
        try:
            receipt = _daubert.issue_receipt(sim, gov_state)
        except Exception as exc:
            logger.warning("daubert receipt failed: %s", exc)
    return {
        "simulation": sim if isinstance(sim, dict) else {"status": "ok"},
        "hecras": hec,
        "governance": _gov.to_api_dict(gov_state),
        "daubert": receipt,
        "qec": qec,
    }


@app.post("/api/v1/package/generate")
def package_generate(body: Optional[PackagePayload] = None) -> Dict[str, Any]:
    try:
        from backend.services.regulatory_package import generate_unified_regulatory_package
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Regulatory package unavailable: {exc}") from exc
    params = body.model_dump() if body else {}
    out_dir = params.pop("output_dir", "render_output/v33_portal")
    out_path = str(ROOT / out_dir)
    return generate_unified_regulatory_package(out_path, custom_params=params)


@app.post("/api/v1/governance/evaluate")
def governance_evaluate(body: SimulationPayload) -> Dict[str, Any]:
    if _engine is None or _gov is None:
        raise HTTPException(status_code=503, detail="Governance engine unavailable")
    sim = _engine.run_simulation(body.usgs_stage_ft, body.discharge_cfs)
    hs = sim["hydraulic_state"]
    state = _gov.evaluate_tri_state_compliance(hs, body.usgs_stage_ft)
    return _gov.to_api_dict(state)


@app.get("/api/v1/viz/instant-ngp")
def instant_ngp_status() -> Dict[str, Any]:
    try:
        from backend.services.instant_ngp_bridge import status_payload
        return status_payload()
    except Exception as exc:
        return {"available": False, "error": str(exc)}


@app.get("/api/v1/viz/instant-ngp/checklist")
def instant_ngp_checklist(photos_dir: str = "data/nerf/bonebank/images") -> Dict[str, Any]:
    try:
        from backend.services.instant_ngp_bridge import dataset_checklist
        return dataset_checklist(photos_dir)
    except Exception as exc:
        return {"available": False, "error": str(exc)}


@app.get("/api/v1/viz/geospatial-stack")
def geospatial_stack() -> Dict[str, Any]:
    try:
        from backend.services.geospatial_viz_stack import stack_status
        return stack_status()
    except Exception as exc:
        return {"available": False, "error": str(exc)}

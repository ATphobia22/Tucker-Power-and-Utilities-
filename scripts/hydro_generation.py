#!/usr/bin/env python3
"""Auditable, non-operational hydro interval screening; Python standard library only.

No observed data is bundled. Results are deterministic scenario arithmetic, not a forecast.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

NUMERIC_FIELDS = (
    "duration_hours", "gross_head_m", "hydraulic_loss_m", "available_flow_m3s",
    "environmental_reserved_flow_m3s", "turbine_max_flow_m3s", "nameplate_kw",
    "efficiency", "availability_fraction", "flow_relative_uncertainty",
    "head_absolute_uncertainty_m", "efficiency_absolute_uncertainty",
)
REQUIRED_FIELDS = ("site_id", "timestamp_start_utc", *NUMERIC_FIELDS, "record_class", "source_id")
RESULT_FIELDS = ("site_id", "timestamp_start_utc", "duration_hours", "record_class",
                 "source_id", "net_head_m", "turbine_flow_m3s", "power_kw",
                 "energy_kwh", "low_energy_kwh", "high_energy_kwh")


def number(row: dict, field: str, line: int) -> float:
    try:
        result = float(row[field])
    except (ValueError, TypeError, KeyError) as exc:
        raise ValueError(f"line {line}: invalid {field}") from exc
    if not math.isfinite(result):
        raise ValueError(f"line {line}: non-finite {field}")
    return result


def utc_time(raw: str, line: int) -> datetime:
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"line {line}: invalid timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError(f"line {line}: timestamp must be UTC with explicit Z/+00:00")
    return parsed.astimezone(timezone.utc)


def validate(row: dict, line: int) -> dict:
    for field in REQUIRED_FIELDS:
        if not str(row.get(field, "")).strip():
            raise ValueError(f"line {line}: missing {field}")
    values = {field: number(row, field, line) for field in NUMERIC_FIELDS}
    for field in ("gross_head_m", "hydraulic_loss_m", "available_flow_m3s",
                  "environmental_reserved_flow_m3s", "turbine_max_flow_m3s",
                  "nameplate_kw", "flow_relative_uncertainty",
                  "head_absolute_uncertainty_m", "efficiency_absolute_uncertainty"):
        if values[field] < 0:
            raise ValueError(f"line {line}: negative {field}")
    if values["duration_hours"] <= 0 or values["nameplate_kw"] <= 0 or values["turbine_max_flow_m3s"] <= 0:
        raise ValueError(f"line {line}: duration, nameplate and max turbine flow must be positive")
    for field in ("efficiency", "availability_fraction", "flow_relative_uncertainty",
                  "efficiency_absolute_uncertainty"):
        if not 0 <= values[field] <= 1:
            raise ValueError(f"line {line}: {field} outside [0,1]")
    return {**row, **values, "_start": utc_time(row["timestamp_start_utc"], line)}


def hydraulic_power(row: dict, gross_head: float, flow: float, eta: float) -> tuple[float, float, float]:
    net_head = max(0.0, gross_head - row["hydraulic_loss_m"])
    turbine_flow = min(max(0.0, flow - row["environmental_reserved_flow_m3s"]),
                       row["turbine_max_flow_m3s"])
    # 9.81 = rho*g/1000 in kW/(m3/s*m) for rho=1000 kg/m3.
    power = min(row["nameplate_kw"], 9.81 * turbine_flow * net_head * eta)
    power *= row["availability_fraction"]
    return net_head, turbine_flow, power


def evaluate(row: dict) -> dict:
    head, flow, power = hydraulic_power(
        row, row["gross_head_m"], row["available_flow_m3s"], row["efficiency"]
    )
    df = row["flow_relative_uncertainty"]
    dh = row["head_absolute_uncertainty_m"]
    de = row["efficiency_absolute_uncertainty"]
    low = hydraulic_power(row, max(0.0, row["gross_head_m"] - dh),
                          max(0.0, row["available_flow_m3s"] * (1 - df)),
                          max(0.0, row["efficiency"] - de))[2]
    high = hydraulic_power(row, row["gross_head_m"] + dh,
                           row["available_flow_m3s"] * (1 + df),
                           min(1.0, row["efficiency"] + de))[2]
    duration = row["duration_hours"]
    return {"site_id": row["site_id"], "timestamp_start_utc": row["timestamp_start_utc"],
            "duration_hours": duration, "record_class": row["record_class"],
            "source_id": row["source_id"], "net_head_m": head, "turbine_flow_m3s": flow,
            "power_kw": power, "energy_kwh": power * duration,
            "low_energy_kwh": low * duration, "high_energy_kwh": high * duration}


def run(input_path: Path, output_dir: Path) -> dict:
    with input_path.open("r", newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or set(REQUIRED_FIELDS) - set(reader.fieldnames):
            raise ValueError(f"missing required columns: {sorted(set(REQUIRED_FIELDS) - set(reader.fieldnames or []))}")
        rows = [validate(row, i) for i, row in enumerate(reader, 2)]
    if not rows:
        raise ValueError("input contains no intervals")
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["site_id"]].append(row)
    output_rows = []
    summaries = []
    for site_id, series in sorted(grouped.items()):
        series.sort(key=lambda item: item["_start"])
        for prior, current in zip(series, series[1:]):
            expected = prior["_start"] + timedelta(hours=prior["duration_hours"])
            if current["_start"] != expected:
                raise ValueError(f"{site_id}: overlapping or missing intervals between {prior['timestamp_start_utc']} and {current['timestamp_start_utc']}")
            if current["nameplate_kw"] != series[0]["nameplate_kw"]:
                raise ValueError(f"{site_id}: inconsistent nameplate_kw")
        results = [evaluate(row) for row in series]
        output_rows.extend(results)
        total_h = sum(r["duration_hours"] for r in results)
        energy = sum(r["energy_kwh"] for r in results)
        low = sum(r["low_energy_kwh"] for r in results)
        high = sum(r["high_energy_kwh"] for r in results)
        summaries.append({
            "site_id": site_id, "intervals": len(results),
            "window_start_utc": series[0]["_start"].isoformat().replace("+00:00", "Z"),
            "window_end_utc": (series[-1]["_start"] + timedelta(hours=series[-1]["duration_hours"])).isoformat().replace("+00:00", "Z"),
            "window_hours": total_h, "nameplate_kw": series[0]["nameplate_kw"],
            "energy_kwh": energy, "low_energy_kwh": low, "high_energy_kwh": high,
            "window_capacity_factor": energy / (series[0]["nameplate_kw"] * total_h),
            "record_classes": sorted({r["record_class"] for r in results}),
            "source_ids": sorted({r["source_id"] for r in results}),
        })
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "interval_results.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=RESULT_FIELDS)
        writer.writeheader()
        writer.writerows(output_rows)
    summary = {"model": "hydro_interval_v0.1", "model_status": "screening_only",
               "uncertainty_kind": "deterministic_input_sensitivity_not_statistical_confidence",
               "water_density_kg_m3": 1000, "gravity_m_s2": 9.81,
               "site_summaries": summaries}
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="UTC interval CSV with explicit SI units")
    parser.add_argument("--output-dir", required=True, type=Path, help="output folder")
    args = parser.parse_args()
    try:
        summary = run(args.input, args.output_dir)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

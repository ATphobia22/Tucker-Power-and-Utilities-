"""Deterministic hydro-screening arithmetic and fail-closed data checks."""
import csv
import tempfile
import unittest
from pathlib import Path

from scripts.hydro_generation import evaluate, run, validate

BASE = {
    "site_id": "test", "timestamp_start_utc": "2026-01-01T00:00:00Z",
    "duration_hours": "1", "gross_head_m": "3", "hydraulic_loss_m": "0",
    "available_flow_m3s": "0.055", "environmental_reserved_flow_m3s": "0",
    "turbine_max_flow_m3s": "0.055", "nameplate_kw": "1.6",
    "efficiency": "0.65", "availability_fraction": "1",
    "flow_relative_uncertainty": "0.2", "head_absolute_uncertainty_m": "0.3",
    "efficiency_absolute_uncertainty": "0.08", "record_class": "illustrative_assumption",
    "source_id": "TEST",
}


class HydroGenerationTests(unittest.TestCase):
    def test_known_water_to_wire_equation(self):
        result = evaluate(validate(BASE.copy(), 2))
        self.assertAlmostEqual(result["power_kw"], 9.81 * 0.055 * 3 * 0.65)
        self.assertLessEqual(result["low_energy_kwh"], result["energy_kwh"])
        self.assertGreaterEqual(result["high_energy_kwh"], result["energy_kwh"])

    def test_nameplate_and_availability_caps(self):
        row = {**BASE, "nameplate_kw": "0.5", "availability_fraction": "0.5"}
        self.assertAlmostEqual(evaluate(validate(row, 2))["power_kw"], 0.25)

    def test_reserved_flow_and_zero_net_head(self):
        row = {**BASE, "environmental_reserved_flow_m3s": "0.06"}
        self.assertEqual(evaluate(validate(row, 2))["energy_kwh"], 0)
        row = {**BASE, "hydraulic_loss_m": "4"}
        self.assertEqual(evaluate(validate(row, 2))["energy_kwh"], 0)

    def test_bad_units_values_and_timestamps_rejected(self):
        for change in ({"efficiency": "1.1"}, {"duration_hours": "0"},
                       {"available_flow_m3s": "nan"}, {"gross_head_m": "-1"},
                       {"timestamp_start_utc": "2026-01-01T00:00:00"}):
            with self.subTest(change=change):
                with self.assertRaises(ValueError):
                    validate({**BASE, **change}, 2)

    def test_gaps_rejected_and_output_summaries(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            csv_path = folder / "input.csv"
            rows = [BASE.copy(), {**BASE, "timestamp_start_utc": "2026-01-01T01:00:00Z"}]
            with csv_path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(BASE))
                writer.writeheader()
                writer.writerows(rows)
            summary = run(csv_path, folder / "out")
            self.assertEqual(summary["site_summaries"][0]["window_hours"], 2)
            self.assertTrue((folder / "out" / "interval_results.csv").exists())
            self.assertTrue((folder / "out" / "summary.json").exists())
            rows[1]["timestamp_start_utc"] = "2026-01-01T03:00:00Z"
            with csv_path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(BASE))
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaisesRegex(ValueError, "missing intervals"):
                run(csv_path, folder / "out2")


if __name__ == "__main__":
    unittest.main()

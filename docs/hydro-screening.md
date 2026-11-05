# Hydro screening evidence package (v0.1; 2026-11-05)

**Status: research demonstration, NOT a resource assessment, plant design, investment estimate, permitted project, or verified generation forecast.** No observed head/discharge series or OEM performance curves have been imported.

## Contents and evidence taxonomy

- `data/hydro/sites.csv`: three candidate *categories* with known site identity separated from unselected sites; `verified_location_only` does not mean verified hydro resource.
- `data/hydro/source_register.csv`: dated source registry, URLs, provenance class and limitations.
- `data/hydro/manufacturer_claims.csv`: labeled manufacturer claims; never silently convert claims to performance observations.
- `data/hydro/illustrative_intervals.csv`: four **fabricated example hours** for each scale, solely to exercise code. These are NOT observations at John T. Myers, and do not represent 2026-01-01 operations.
- `scripts/hydro_generation.py`: deterministic, standard-library interval energy model with low/base/high sensitivity envelopes and strict data validation.
- `tests/test_hydro_generation.py`: regression and failure-path tests.

## Calculation

For each UTC interval of duration `dt_h`:

```text
H_net_m = max(0, H_gross_m - H_loss_m)
Q_turbine_m3s = min(max(0, Q_available_m3s - Q_reserved_m3s), Q_turbine_max_m3s)
P_kW = min(P_nameplate_kW, 9.81 * Q_turbine_m3s * H_net_m * eta) * availability_fraction
E_kWh = P_kW * dt_h
```

The factor 9.81 has units kN/m³ (water density approximated 1000 kg/m³ and g=9.81 m/s²). `eta` is **combined water-to-wire efficiency**; availability is a fractional derate for the interval. This is a **head-driven** model, NOT a free-stream hydrokinetic velocity model. No turbine minimum-flow cutoff or OEM efficiency curve is implemented; those are required before feasibility use. No seasonal extrapolation or dispatch guarantee is permitted.

**Sensitivity envelope (not a statistical confidence interval):** for each interval vary available flow by `± flow_relative_uncertainty`, gross head by `± head_absolute_uncertainty_m`, and efficiency by `± efficiency_absolute_uncertainty`, clipping efficiency to [0,1] and respecting turbine/nameplate caps. These parameters are illustrative judgments, not calibrated uncertainty distributions. The bounds omit datum error, correlated flow/head, water rights, outages uncertainty, flooding, sediment, ecology, grid losses, finance, and permitting. Results cannot be called P10/P90 or confidence limits.

## Run and reproduce

```bash
python scripts/hydro_generation.py --input data/hydro/illustrative_intervals.csv --output-dir /tmp/tucker-hydro
python -m unittest discover -s tests -p 'test_hydro_generation.py' -v
```

Output: `interval_results.csv` (each input interval plus `net_head_m`, `turbine_flow_m3s`, `power_kw`, `energy_kwh`, `low_energy_kwh`, `high_energy_kwh`) and `summary.json` (site totals, hours, theoretical nameplate MWh-equivalent denominator, observed-window capacity factor, source classes). Only compare the **same four-hour illustrative window**; no annual generation claim follows. Inputs are required, and outputs are never silently interpolated.

## Required measurement campaign before ranking projects

1. **Micro demonstration:** choose a legally accessible site; log synchronized upstream/downstream levels (common vertical datum), flow duration, diversion/bypass requirements, debris and ecological constraints. Validate a turbine-specific head/flow curve and actual electrical output.
2. **Community-scale:** identify a real site and hydraulic rights, measure net head and allocable flow across seasons, verify civil footprint, flood effects, interconnection, safety and manufacturer quotation.
3. **John T. Myers:** confirm USACE ownership/permissions, FERC jurisdiction and current project docket, and obtain *concurrent* USACE headwater, tailwater and discharge records. Navigation discharge is not automatically turbine-available. The USACE project page locates the dam at Ohio River mile 846.0; nominal upper/lower pool elevations (342/324 ft) imply 18 ft = 5.4864 m **nominal difference**, not a continuous net head. The datum and conditions must be reconciled. The project's 700 MW proposal is **unverified**; do not use as installed capacity.

For observational ingestion: record sensor/station ID, parameter, measurement method, timestamps and timezone, datum, QA flags, original unit, conversion, download time, license, and SHA-256 of unmodified source. Missing/flagged observations must remain missing or be explicitly excluded. Check same-time hydraulic measurements before subtraction; do not mix gage-stage feet with elevations.

## Cost, manufacturer, and regulatory evidence

ORNL's *Updated Baseline Cost Model for Hydropower (2025)* was published **2026-01-28**. It is a screening model with project-category applicability and cost confidence intervals; do not substitute older coefficient sets, a different base-dollar year, or blanket modular savings as if they were updated 2025 coefficients. A defensible LCOE comparison requires a documented model version, construction scope, price base year, capital recovery, O&M, replacements, downtime, annual measured energy, and interconnection. **No LCOE is computed by this package.**

The PowerSpout LH advertised static-head/flow and output values and Turbulent nominal product ratings are **manufacturer claims**, not independent field measurements, installed quotations, or performance guarantees. Obtain dated OEM efficiency curves, minimum flow, environmental limits, warranties, and binding site-specific quotations. The `illustrative_intervals.csv` values are not claimed manufacturer settings.

Federal navigation infrastructure has additional USACE and FERC review; neither an expedited timeline nor an exemption is guaranteed. Verify state and federal water quality, fish passage, property access, safety, interconnection, and environmental obligations before construction. Hashes support traceability, not legal admissibility or professional certification.

## Source register and change control

Source links, publisher and dates are in `data/hydro/source_register.csv`. Key primary sources:
- [USACE John T. Myers (published 2024-01-09)](https://www.lrd.usace.army.mil/Missions/Projects/Article/3638728/john-t-myers-locks-and-dam/)
- [ORNL Updated BCM 2025 (published 2026-01-28)](https://hydrosource.ornl.gov/data/datasets/updated-baseline-cost-model-for-hydropower-2025/)
- [USGS Water Data APIs](https://api.waterdata.usgs.gov/)
- [FERC hydropower authorizations](https://www.ferc.gov/licensing/smalllow-impact-hydropower-projects/smalllow-impact-hydropower-projects-types-projects)

No empirical data is bundled. For a measured dataset, commit a separate manifest with retrieval timestamp, raw SHA-256, QA exclusions, source terms and revision ID. Require review by qualified hydraulic, environmental and electrical engineers before external engineering use.

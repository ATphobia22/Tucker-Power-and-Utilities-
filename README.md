# Tucker Power and Utilities

**Public-interest utility planning and engineering software for the Tri-State River Valley of Indiana, Illinois, and Kentucky.**

Tucker Power and Utilities is an initiative to explore affordable, reliable electricity and resilient infrastructure for every member of our community. Our work combines open-source software, hydropower feasibility research, distributed energy resources, and transparent engineering evidence.

Our motivation is service to our neighbors, grounded in faith, care for families, and public accountability. **Technology informs people; it does not silently govern them. Human authority remains final.**

## Project status

This repository contains a development foundation inherited from the Point Township Digital Twin (PTDT): a Python/FastAPI backend, a React/TypeScript frontend, geospatial components, data, schemas, tests, and engineering documentation. Existing PTDT names and site-specific examples remain in the codebase.

The utility architecture and hydro portfolio described below are **development goals and feasibility work**, not a declaration of an operating utility, commissioned generating plant, approved interconnection, or completed utility-control platform. This README update does not certify runtime behavior or passing CI.

| Workstream | Scope and evidence boundary |
|---|---|
| Community utility planning | Evaluate public-interest ownership, affordability, service reliability, and accountable governance. Formation, service territory, and rate authority require separate legal review. |
| Hydropower | Screen micro-hydro sites, community-scale installations, and potential existing-dam retrofits using measured head and available flow. |
| Distribution and DER modeling | Plan feeder studies, solar/storage integration, and scenario analysis; OpenDSS and PyPSA are candidate tools, not asserted completed integrations. |
| Grid operations architecture | Research ADMS, SCADA, DERMS, interoperability, and cybersecurity. Planning documents do not establish deployment or authority to operate equipment. |
| Evidence and visualization | Preserve source data, units, timestamps, datum metadata, assumptions, and uncertainty. Rendered scenes must not alter underlying engineering evidence. |

## Low-head hydropower research

Low-head generation uses a water-level difference and flow through a turbine. Free-stream hydrokinetic generation uses water velocity and requires a different resource model.

Preliminary electrical output is:

```text
P_kW = 9.81 × Q_m3_per_s × H_net_m × efficiency
H_net = available gross hydraulic head − hydraulic losses
```

Efficiency represents the combined turbine, generator, and relevant electrical conversion efficiencies. Use turbine flow after required bypasses and other water allocations, not total river discharge. Annual energy must be integrated over changing flow, head, efficiency, and downtime.

For illustration only, 3 m net head, 55 L/s flow, and 65% combined efficiency yield approximately **1.05 kW**. This is a calculation, not a measured site yield.

### Technology screening

| Candidate | Published information | Qualification |
|---|---|---|
| PowerSpout LH propeller | Manufacturer product page: 1–5 m static head, 25–55 L/s per unit, up to 1.6 kW | General information gives a different minimum flow of 14 L/s. Resolve through a site-specific manufacturer calculation. Maximum output does not apply throughout the operating range. |
| Turbulent vortex | Manufacturer advertises 15–90 kW units; approximately 1.5 m head and 1.5 m³/s for the smallest unit | Manufacturer claims are not independent proof of site output, availability, or ecological performance. |
| Kaplan/propeller | Reaction turbines suited to lower-head, higher-flow applications | Select using verified performance curves and site conditions; do not impose a universal 1–6 m range. |
| Archimedes screw | Candidate for low-head sites | Fish passage, debris, sediment, civil footprint, and maintenance require site-specific evaluation. No blanket fish-safety claim. |

A draft tube enables appropriate reaction turbines to use available head; it does not create energy. For the PowerSpout LH, the water-filled draft tube and submerged outlet are essential, and rising tailwater reduces operating head.

Sources reviewed November 5, 2026:

- [DOE: Types of Hydropower Turbines](https://www.energy.gov/cmei/water/types-hydropower-turbines)
- [PowerSpout LH product specifications](https://www.powerspout.com/products/powerspout-lh-1)
- [PowerSpout LH general information](https://www.powerspout.com/pages/low-head-lh-info)
- [Turbulent manufacturer information](https://www.turbulent.be/)
- [NCAT: Micro-Hydro Design and Installation](https://www.ncat.org/publication/micro-hydro-power-a-beginners-guide-to-design-and-installation/)
- [Experimental study of fish passage through an Archimedean screw turbine](https://pubmed.ncbi.nlm.nih.gov/29537067/)

### John T. Myers: candidate site, unverified capacity

John T. Myers Locks and Dam is a potential research focus, not a secured generation asset. USACE lists upper and lower pool elevations of 342 and 324 ft, a nominal difference of 18 ft (5.4864 m). These values do not establish continuous net generating head; confirm the elevation datum and use concurrent operational records.

The **700 MW proposal in project planning material remains unverified**. At an illustrative 5.4864 m net head and 90% efficiency, 700 MW would require approximately **14,450 m³/s (510,000 cfs)** through turbines. This arithmetic does not demonstrate usable flow, constructability, navigation compatibility, environmental acceptability, or economic feasibility.

- [USACE: John T. Myers project information](https://www.lrd.usace.army.mil/Missions/Projects/Article/3638728/john-t-myers-locks-and-dam/)
- [USACE water-management data](https://water.usace.army.mil/)

## Economics and permitting

Calculate project economics from site-specific energy yield, civil works, equipment, interconnection, financing, maintenance, replacements, and decommissioning. Separate generation LCOE from the delivered customer tariff, which also depends on distribution and utility-service costs.

The often-quoted **$0.02–$0.27/kWh** small-hydro range comes from IRENA's 2012 report in **2010 dollars**, assuming a **10% cost of capital**. It is historical context, not a current Tucker Power price, quote, or payback commitment.

Use [ORNL's Updated Baseline Cost Model for Hydropower (2025)](https://hydrosource.ornl.gov/data/datasets/updated-baseline-cost-model-for-hydropower-2025/) for preliminary U.S. screening with model applicability, dollar year, and uncertainty recorded. Investment decisions require site-specific estimates.

Small capacity does not automatically remove permitting obligations. FERC's 10 MW exemption route excludes federal dams; an existing-dam proposal requires its own authorization assessment. Determine applicable federal, Indiana, Illinois, or Kentucky requirements for each site, including water quality, environmental review, navigation, land rights, and electrical interconnection.

- [IRENA historical hydropower cost report](https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2012/RE_Technologies_Cost_Analysis-HYDROPOWER.pdf)
- [FERC: Hydropower project types and authorization pathways](https://www.ferc.gov/licensing/smalllow-impact-hydropower-projects/smalllow-impact-hydropower-projects-types-projects)

## Data and evidence requirements

| Input | Preferred source | Required context |
|---|---|---|
| Headwater, tailwater, and project flows | USACE operational records | Concurrent timestamps, units, datum, operating conditions, and quality flags |
| Historical streamflow | [USGS Water Data APIs](https://api.waterdata.usgs.gov/) | Station identity, measurement period, parameter codes, revisions, and missing-data handling |
| Turbine performance | Manufacturer curves and independent testing where available | Model, head/flow envelope, efficiency, minimum flow, and electrical configuration |
| Costs | ORNL screening models and dated supplier/contractor quotations | Currency, base year, scope, exclusions, contingency, and uncertainty |
| Regulatory status | Responsible federal and state agencies | Project identifiers, dated determinations, conditions, and unresolved requirements |

Store observations, manufacturer claims, assumptions, and derived results separately. Use consistent units and compatible vertical datums before subtracting elevations. Property flood elevations and gage-stage triggers inherited from PTDT are site-specific examples, not universal utility-design constants.

Cryptographic hashes support integrity and reproducibility; they do not establish scientific correctness, professional licensure, regulatory approval, or court admissibility. Engineering outputs do not replace formal regulatory determinations.

## Development

The existing application foundation uses Python/FastAPI and React/TypeScript/Vite. The following commands are development entry points retained from the repository's prior setup, not a verified production deployment.

### Backend — POSIX shell

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

### Frontend — separate terminal

```bash
cd frontend
npm install
npm run dev
```

The frontend package also defines `npm run typecheck` and `npm run build`. Consult [tests](tests/), [scripts](scripts/), and [workflow definitions](.github/workflows/) for the applicable checks. Do not infer passing tests from the presence of these commands.

### Repository navigation

| Location | Contents |
|---|---|
| [backend](backend/) | Backend application code |
| [frontend](frontend/) | React/TypeScript frontend |
| [core](core/) | Core components inherited from PTDT |
| [data](data/) and [schemas](schemas/) | Data and schema definitions |
| [adapters](adapters/) and [integrations](integrations/) | Adapter and integration code |
| [docs](docs/) | Engineering and project documentation |
| [tests](tests/) and [scripts](scripts/) | Tests and development utilities |

## Next milestones

1. Build a source-indexed site-screening dataset with measured head, flow, uncertainty, and access constraints.
2. Implement a reproducible time-series hydro energy model and compare it with manufacturer curves.
3. Evaluate lifecycle costs and sensitivity to drought, flood tailwater, downtime, and financing.
4. Complete site-specific environmental, navigation, ownership, and interconnection assessments.
5. Develop distribution and DER scenarios with explicit validation before any operational use.
6. Reconcile inherited PTDT naming and documentation with utility-specific implementation.

## Participation and licensing

Contributions should include reproducible calculations, source links, explicit units, documented assumptions, and tests appropriate to the change. Public access, accessibility, non-discrimination, and accountable human decisions are project goals.

Open-source development is the intended direction. Confirm the applicable license for each file and dependency before redistribution; this README does not grant a new license or assert that every component shares one.

**Project maintainer:** [ATphobia22](https://github.com/ATphobia22)

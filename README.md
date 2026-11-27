# RiskRoute — Global Disruption to Supply Chain Impact

An AI-assisted early-warning system that connects real-world disruptions — conflicts, extreme weather, port congestion and trade restrictions — to a company's suppliers, shipments and inventory. It scores risks and simulates delays to recommend actions before shortages happen.

> **Status:** 🚧 In development (Phase 2 — Database)
>
> **Data notice:** All company data (suppliers, materials, inventory, orders, shipments) is **simulated** for a fictional Warsaw-based electronics manufacturer. External risk events come from public sources.

## The question it answers

> *"A global disruption is happening. Which parts of our supply chain are affected, how serious is the impact, and what should we do about it?"*

## How it works

1. **Detect** — collect global risk events (GDELT, GDACS, IMF PortWatch)
2. **Connect** — match events to suppliers, routes and chokepoints
3. **Measure** — score risks and simulate 7 / 14 / 30-day delays
4. **Advise** — AI agent explains risks and suggests mitigation actions

## Tech stack

| Layer | Tool |
|---|---|
| Data collection & analysis | Python (pandas, requests) |
| Storage | MySQL |
| Dashboard | Power BI |
| AI agent | LLM with function calling |

## Project structure

```
RiskRoute/
├── data/
│   ├── raw/          # downloaded external data (not committed)
│   ├── processed/    # cleaned data
│   └── simulated/    # generated company data
├── sql/              # database schema and queries
├── src/              # Python source code
├── notebooks/        # exploration notebooks
├── dashboard/        # Power BI files
└── docs/             # diagrams and documentation
```

## Roadmap

- [x] Phase 1 — Setup and foundations
- [ ] Phase 2 — Simulated company database
- [ ] Phase 3 — External risk event collection
- [ ] Phase 4 — Risk scoring and exposure engine
- [ ] Phase 5 — Disruption scenario simulator
- [ ] Phase 6 — Power BI dashboard
- [ ] Phase 7 — AI risk analyst agent
- [ ] Phase 8 — Red Sea 2023 back-test and documentation

## Setup

```bash
git clone https://github.com/PrasadPawar1999/RiskRoute--global-disruption-to-supply-chain-impact.git
cd RiskRoute--global-disruption-to-supply-chain-impact
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env         # then edit .env with your MySQL password
python src/test_connection.py
```

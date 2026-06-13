# ☁️ Cloud Cost Optimizer & Remediation Engine

**Andela FDE Technical Challenge — 2026**
**Architect:** Pradeep Kumar Pacha | **AI Readiness Tag:** The Architect (Navigator edge)

---

## Overview

A Python-based, API-first FinOps tool that ingests AWS/Azure billing exports (JSON/CSV), identifies orphaned cloud resources, and generates CLI remediation commands — all surfaced through a real-time dashboard.

## Features

- 📁 **File Ingestion** — Upload AWS/Azure billing exports (JSON or CSV)
- 🔍 **Orphan Detection** — Rule-based engine detects unattached disks, idle VMs, unused IPs, old snapshots, empty load balancers
- 🔧 **CLI Remediation** — Auto-generates provider-specific CLI commands (AWS CLI / Azure CLI)
- 📊 **FinOps Dashboard** — Visual breakdown by resource type, risk level, provider, region
- 💰 **Savings Projection** — Monthly and annual waste estimates
- 📤 **Export** — Download remediation shell script

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI + Uvicorn |
| Database | SQLite (via SQLAlchemy ORM) |
| Frontend | HTML5 + Chart.js |
| Engine | Python rules engine + Pandas |
| CI/CD | GitHub Actions |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Open browser
http://localhost:8000
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/resources/scan` | Upload billing file and detect orphans |
| GET | `/api/resources/orphans` | List all orphaned resources |
| GET | `/api/remediation/commands` | Get all CLI remediation commands |
| GET | `/api/remediation/export` | Export as shell script |
| GET | `/api/dashboard/summary` | Full dashboard data |
| GET | `/docs` | Swagger UI |

## Sample Input Format

```json
[
  {
    "resource_id": "vol-0abc123",
    "resource_type": "ebs",
    "resource_name": "old-data-disk",
    "cloud_provider": "AWS",
    "region": "us-east-1",
    "monthly_cost": 45.00,
    "status": "unattached",
    "last_used": "2025-11-01"
  }
]
```

## Vibe Coding Methodology

This project was built using **Vibe Coding** — the Architect directs, the AI engineers. No manual code edits were made. See `prompts.md` for the full audit log of all instructions.

## Project Structure

```
cloud-cost-optimizer/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── database.py          # SQLAlchemy models + SQLite
│   ├── finops_engine.py     # Orphan detection + CLI generation
│   └── routers/
│       ├── resources.py     # Scan + orphan endpoints
│       ├── remediation.py   # CLI command endpoints
│       └── dashboard.py     # Dashboard summary endpoint
├── templates/
│   └── index.html           # FinOps dashboard UI
├── data/                    # SQLite database (auto-created)
├── tests/                   # Test suite
├── prompts.md               # Vibe coding audit log
├── requirements.txt
└── README.md
```

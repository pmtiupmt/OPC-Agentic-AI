# OPC Agentic AI Decision Support System

A competition prototype developed for **MIS Talent 2026 – North Star**, designed to support operational and financial decision-making for a One Person Company (OPC) scaling its business across multiple provinces.

The system uses a **hierarchical multi-agent architecture** to separate financial analysis, risk control, and partner recommendation tasks, while keeping the **Founder as the final decision-maker** through a Human-in-the-Loop (HITL) governance layer.

> **Project status:** Competition prototype / proof of concept.  
> External banking integrations are currently simulated or conceptual rather than connected to production banking APIs.

---

## System Overview

The architecture consists of one orchestration agent and three specialized agents:

```text
                         Founder
                            |
                    Decision Dashboard
                            |
              Chief Operating Agent (COA)
                 /          |           \
                /           |            \
     Data & Finance   Risk & Compliance   Decision & Partner
          Agent             Agent               Agent
                \           |            /
                 \          |           /
                    Business Data
                         |
                 OpenAI Reasoning
```

### Agents

| Agent | Responsibility | Main Output |
|---|---|---|
| **Chief Operating Agent (COA)** | Decomposes objectives, routes tasks, and aggregates agent results | Executive summary / decision context |
| **Data & Finance Agent** | Analyzes revenue, cost, gross margin, invoices, transactions, and cashflow | Financial report / finance indicators |
| **Risk & Compliance Agent** | Applies governance rules, detects suspicious transactions, and masks sensitive data | Risk report / masked payload |
| **Decision & Partner Agent** | Matches financing needs with available banking products | Decision Card / recommendation |

---

## Key Features

- Hierarchical multi-agent orchestration
- Financial and cashflow analysis
- Risk-rule screening
- Suspicious transaction detection
- Sensitive-data masking before external sharing
- OpenAI-powered structured recommendation
- JSON-schema constrained model output
- Human-in-the-Loop approval flow
- Streamlit executive dashboard
- Session-level audit logging
- PostgreSQL relational schema for business, risk, and decision entities

---

## Governance Logic

The prototype combines deterministic business rules with AI-generated reasoning.

Examples implemented across the prototype include:

- **RR-001** — transactions with risk score `>= 85` are held for Founder review
- **RR-002** — projected cash below the `550M VND` reserve threshold triggers a cashflow warning
- **RR-003** — low-margin orders are flagged in the dashboard
- **RR-004** — external data is masked and requires Founder confirmation before transmission
- **RR-005** — high-value financial decisions above `300M VND` require Founder approval

AI recommendations do **not** directly execute high-impact actions. They are presented to the Founder for approval or rejection.

---

## OpenAI Integration

`openai_adapter.py` connects the Decision Agent to the **OpenAI Responses API**.

The model receives:

- financial summary
- current risk alerts
- available banking products
- customer profile

The response is constrained to a structured JSON schema containing:

```json
{
  "decision": "...",
  "recommended_bank": "...",
  "recommended_product": "...",
  "confidence": 0.0,
  "reasoning": [
    "...",
    "...",
    "..."
  ],
  "requires_founder_approval": true
}
```

The application validates the response before presenting it as a Decision Card.

---

## Repository Structure

Recommended structure:

```text
opc-agentic-ai/
│
├── dashboard.py
├── data_loader.py
├── opc_multi_agent_system.py
├── openai_adapter.py
│
├── database/
│   └── opc_schema.sql
│
├── docs/
│   ├── Report_North_Star.pdf
│   └── Slide_North_Star.pdf
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

### Main Files

| File | Description |
|---|---|
| `dashboard.py` | Streamlit dashboard for data upload, financial overview, risk monitoring, AI recommendations, Founder approval, and audit log |
| `data_loader.py` | Loads and validates the MIS Talent Team Pack Excel workbook |
| `opc_multi_agent_system.py` | Core multi-agent architecture and HITL governance middleware |
| `openai_adapter.py` | OpenAI-backed Decision Agent with structured JSON output |
| `database/opc_schema.sql` | PostgreSQL schema for customer, contract, order, invoice, transactions, cashflow, risk logs, and decisions |

---

## Run the Dashboard

```bash
streamlit run dashboard.py
```

The dashboard contains six main views:

1. **Upload TeamPack.xlsx**
2. **Financial Overview**
3. **Risk Dashboard**
4. **AI Decision**
5. **Founder Approval**
6. **Audit Log**

---

## Input Data

The application expects the MIS Talent OPC Team Pack workbook and validates its worksheet structure before enabling the dashboard.

The competition dataset is **not included in this repository**. Users must provide a compatible `TeamPack.xlsx` file separately.

This keeps the repository focused on the system architecture and avoids redistributing competition data without explicit permission.

---

## Database Design

`opc_schema.sql` provides a normalized PostgreSQL schema for the main business and governance entities, including:

- Customer
- Contract
- Order
- Invoice
- Bank Transaction
- Cashflow
- Risk Log
- Decision

The schema also includes constraints, indexes, audit-oriented fields, and Founder approval state tracking.

---

## Dashboard Workflow

```text
Team Pack
   |
   v
Data Validation
   |
   v
Financial Analysis
   |
   v
Risk Screening
   |
   v
OpenAI Decision Agent
   |
   v
Decision Card
   |
   v
Founder Approve / Reject
   |
   v
Audit Log
```

The design follows an **Executive OS** concept with three operating zones:

- **Input Data**
- **Agent Workflow**
- **Decision Center**

---

## Design Principles

The system is based on four main principles:

1. **Single Responsibility**  
   Each specialized agent handles one primary business function.

2. **Data-Driven Decision Making**  
   AI reasoning is grounded in structured business data and deterministic rules.

3. **Human-in-the-Loop Governance**  
   High-impact decisions remain under Founder control.

4. **Traceability**  
   Risk triggers, recommendations, and Founder actions are recorded for review and audit.

---

## Limitations

This repository represents a competition prototype rather than a production banking system.

Current limitations include:

- static competition workbook as the primary data source
- simulated/conceptual banking API integrations
- session-based dashboard audit events
- no production authentication or role-based access control
- no real-time banking infrastructure

Future development could include real Open Banking APIs, persistent audit storage, cloud deployment, additional specialized agents, and real-time event processing.

---

## Project Documentation

Detailed architecture, BPMN workflow, ERD, governance design, dashboard wireframe, and competition analysis are available in:

- `docs/Report_North_Star.pdf`
- `docs/Slide_North_Star.pdf`

---

## Team

**North Star — MIS Talent 2026**

This repository contains the technical prototype and system design developed for the competition.

---

## Disclaimer

This project is an educational and competition prototype.  
It does not provide financial advice and must not be used to automatically execute real financial transactions without appropriate security, compliance, and human review.

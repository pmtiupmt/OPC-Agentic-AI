"""Streamlit dashboard for the OPC Agentic AI prototype."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from data_loader import TeamPackLoadError, load_team_pack
from openai_adapter import OpenAIDecisionAgent, OpenAIDecisionAgentError


st.set_page_config(
    page_title="OPC Executive AI Operating System",
    page_icon="OPC",
    layout="wide",
    initial_sidebar_state="expanded",
)


REQUIRED_APP_SHEETS = (
    "02_OPC_PROFILE",
    "03_CUSTOMERS",
    "06_ORDERS",
    "08_BANK_TXN",
    "09_CASHFLOW",
    "11_BANK_PRODUCTS",
    "13_RISK_RULES",
    "14_ALERTS",
)


def main() -> None:
    _init_state()
    _apply_theme()
    _render_sidebar()

    page = st.session_state["page"]
    sheets = st.session_state.get("sheets")

    if page == "Upload TeamPack.xlsx":
        render_upload_page()
        return

    if not sheets:
        render_empty_state()
        return

    if page == "Financial Overview":
        render_financial_overview(sheets)
    elif page == "Risk Dashboard":
        render_risk_dashboard(sheets)
    elif page == "AI Decision":
        render_ai_decision(sheets)
    elif page == "Founder Approval":
        render_founder_approval()
    elif page == "Audit Log":
        render_audit_log(sheets)


def _init_state() -> None:
    defaults = {
        "sheets": None,
        "workbook_name": None,
        "page": "Upload TeamPack.xlsx",
        "decision": None,
        "approval": None,
        "audit_events": [],
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #f6f8fb;
            --surface: #ffffff;
            --surface-soft: #f8fafc;
            --line: #d9e2ec;
            --text: #111827;
            --muted: #64748b;
            --accent: #0f766e;
            --accent-strong: #115e59;
            --warning: #b45309;
            --danger: #b91c1c;
        }
        .stApp {
            background:
                linear-gradient(180deg, #f8fafc 0%, #eef3f8 44%, #f8fafc 100%);
            color: var(--text);
        }
        .block-container {
            padding-top: 1.15rem;
            padding-bottom: 3rem;
            max-width: 1420px;
        }
        h1, h2, h3 {
            letter-spacing: 0;
        }
        h1 {
            font-size: 2rem;
            line-height: 1.15;
            margin-bottom: 0.35rem;
        }
        h2, h3 {
            margin-top: 1.3rem;
        }
        [data-testid="stSidebar"] {
            background: #0f172a;
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }
        [data-testid="stSidebar"] * {
            color: #e5e7eb;
        }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            color: #cbd5e1;
        }
        [data-testid="stSidebar"] [role="radiogroup"] {
            gap: 0.35rem;
        }
        [data-testid="stSidebar"] label {
            border-radius: 8px;
            padding: 0.15rem 0.25rem;
        }
        [data-testid="stMetric"] {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 14px 32px rgba(15, 23, 42, 0.07);
        }
        [data-testid="stMetricLabel"] p {
            color: var(--muted);
            font-size: 0.78rem;
            text-transform: uppercase;
            font-weight: 700;
        }
        [data-testid="stMetricValue"] {
            font-weight: 800;
            color: var(--text);
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--line);
            border-radius: 8px;
            overflow: hidden;
            background: var(--surface);
        }
        .executive-shell {
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 8px;
            padding: 1.15rem 1.25rem;
            background:
                linear-gradient(135deg, rgba(15, 118, 110, 0.12), rgba(14, 165, 233, 0.07)),
                #ffffff;
            box-shadow: 0 18px 42px rgba(15, 23, 42, 0.08);
            margin-bottom: 1.2rem;
        }
        .eyebrow {
            color: var(--accent-strong);
            font-size: 0.76rem;
            text-transform: uppercase;
            font-weight: 800;
            margin-bottom: 0.35rem;
        }
        .page-subtitle {
            color: #475569;
            max-width: 920px;
            margin: 0.25rem 0 0 0;
            font-size: 0.98rem;
        }
        .kpi-card {
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1rem;
            background: var(--surface);
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.06);
            min-height: 118px;
        }
        .kpi-label {
            color: var(--muted);
            font-size: 0.76rem;
            text-transform: uppercase;
            font-weight: 800;
            margin-bottom: 0.55rem;
        }
        .kpi-value {
            color: var(--text);
            font-size: 1.45rem;
            font-weight: 850;
            line-height: 1.15;
            overflow-wrap: anywhere;
        }
        .kpi-note {
            color: var(--muted);
            font-size: 0.82rem;
            margin-top: 0.5rem;
        }
        .sidebar-brand {
            border: 1px solid rgba(255, 255, 255, 0.13);
            border-radius: 8px;
            padding: 1rem;
            background: rgba(255, 255, 255, 0.06);
            margin-bottom: 0.8rem;
        }
        .sidebar-brand-title {
            font-size: 1.05rem;
            font-weight: 850;
            color: #ffffff;
            margin-bottom: 0.25rem;
        }
        .sidebar-brand-copy {
            color: #cbd5e1;
            font-size: 0.84rem;
            line-height: 1.4;
        }
        .section-title {
            font-size: 0.82rem;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }
        .status-panel {
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1rem;
            background: var(--surface);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-brand-title">Executive AI OS</div>
                <div class="sidebar-brand-copy">OPC finance, risk, decision, approval, and audit cockpit.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        page_options = [
            "Upload TeamPack.xlsx",
            "Financial Overview",
            "Risk Dashboard",
            "AI Decision",
            "Founder Approval",
            "Audit Log",
        ]
        st.session_state["page"] = st.radio(
            "Pages",
            page_options,
            index=page_options.index(st.session_state.get("page", page_options[0])),
            label_visibility="collapsed",
        )

        st.divider()
        workbook_name = st.session_state.get("workbook_name")
        if workbook_name:
            st.success(f"Workbook loaded: {workbook_name}")
        else:
            st.info("Upload the Team Pack to begin.")

        st.divider()
        st.caption("Phase 1 interface refresh")
        st.caption("Backend logic unchanged")


def render_empty_state() -> None:
    render_page_header(
        "Upload TeamPack.xlsx First",
        "Load the validated Team Pack before opening executive operating views.",
        "Workspace status",
    )
    st.info("Use the upload page to load and validate the competition workbook before opening this page.")


def render_upload_page() -> None:
    render_page_header(
        "Upload TeamPack.xlsx",
        "Load the competition workbook, validate sheets and columns, then unlock the dashboard pages.",
        "Data intake",
    )

    uploaded_file = st.file_uploader(
        "Upload TeamPack.xlsx",
        type=("xlsx",),
        accept_multiple_files=False,
    )

    if uploaded_file is None:
        st.info("Waiting for a valid `.xlsx` workbook.")
        return

    if st.button("Validate and Load Workbook", type="primary", use_container_width=True):
        with st.status("Reading workbook...", expanded=True) as status:
            try:
                sheets = _load_uploaded_workbook(uploaded_file)
            except TeamPackLoadError as exc:
                status.update(label="Validation failed", state="error")
                st.error(str(exc))
                return

            missing_app_sheets = [sheet for sheet in REQUIRED_APP_SHEETS if sheet not in sheets]
            if missing_app_sheets:
                status.update(label="Dashboard requirements missing", state="error")
                st.error(f"Missing dashboard worksheet(s): {', '.join(missing_app_sheets)}")
                return

            st.session_state["sheets"] = sheets
            st.session_state["workbook_name"] = uploaded_file.name
            st.session_state["decision"] = None
            st.session_state["approval"] = None
            _audit("workbook_uploaded", f"Loaded and validated {uploaded_file.name}")
            status.update(label="Workbook loaded", state="complete")

    sheets = st.session_state.get("sheets")
    if sheets:
        render_kpi_row(
            [
                ("Worksheets", len(sheets), "Validated workbook tabs"),
                ("Business Sheets", len(REQUIRED_APP_SHEETS), "Used by dashboard views"),
                ("Rows Loaded", sum(len(frame) for frame in sheets.values()), "Available operating records"),
            ]
        )
        with st.expander("Workbook sheets", expanded=False):
            st.dataframe(_sheet_summary(sheets), use_container_width=True, hide_index=True)


def render_financial_overview(sheets: dict[str, pd.DataFrame]) -> None:
    render_page_header(
        "Financial Overview",
        "Executive view of revenue, cost, margin, and projected cash position.",
        "Finance command",
    )
    summary = build_finance_summary(sheets)

    render_kpi_row(
        [
            ("Revenue", format_vnd(summary["revenue"]), "Total order revenue"),
            ("Cost", format_vnd(summary["cost"]), "Estimated delivery cost"),
            ("Margin", format_percent(summary["margin"]), "Aggregate gross margin"),
            ("Closing Cash", format_vnd(summary["latest_projected_closing_cash"]), "Latest projection"),
        ]
    )

    cashflow = sheets["09_CASHFLOW"].copy()
    cashflow_numeric = cashflow.assign(
        expected_cash_in=to_number(cashflow["expected_cash_in"]),
        expected_cash_out=to_number(cashflow["expected_cash_out"]),
        projected_closing_cash=to_number(cashflow["projected_closing_cash"]),
    )

    st.subheader("Cashflow")
    st.line_chart(
        cashflow_numeric.set_index("month")[
            ["expected_cash_in", "expected_cash_out", "projected_closing_cash"]
        ],
        height=320,
    )

    left, right = st.columns([1.15, 0.85])
    with left:
        st.subheader("Orders")
        orders = sheets["06_ORDERS"].copy()
        orders["order_revenue"] = to_number(orders["order_revenue"])
        orders["estimated_cost"] = to_number(orders["estimated_cost"])
        orders["gross_margin"] = (orders["order_revenue"] - orders["estimated_cost"]) / orders[
            "order_revenue"
        ].replace(0, pd.NA)
        st.dataframe(orders, use_container_width=True, hide_index=True)
    with right:
        st.subheader("Cashflow Detail")
        st.dataframe(cashflow, use_container_width=True, hide_index=True)


def render_risk_dashboard(sheets: dict[str, pd.DataFrame]) -> None:
    render_page_header(
        "Risk Dashboard",
        "Live control room for alerts, high-risk transactions, and rule-trigger status.",
        "Risk command",
    )
    risk = build_risk_summary(sheets)

    render_kpi_row(
        [
            ("Risk Alerts", len(risk["alerts"]), "Workbook alert records"),
            ("High Risk Transactions", len(risk["high_risk_transactions"]), "Score >= 85 or suspicious"),
            ("Triggered Rules", len(risk["rule_triggers"]), "Active compliance checks"),
        ]
    )

    st.subheader("Compliance Status")
    status_rows = []
    for trigger in risk["rule_triggers"]:
        status_rows.append(
            {
                "rule_id": trigger["rule_id"],
                "status": "Triggered",
                "severity": trigger["severity"],
                "evidence": trigger["evidence"],
                "required_action": trigger["required_action"],
            }
        )
    if status_rows:
        st.dataframe(pd.DataFrame(status_rows), use_container_width=True, hide_index=True)
    else:
        st.success("No active compliance triggers detected.")

    left, right = st.columns(2)
    with left:
        st.subheader("Risk Alerts")
        st.dataframe(risk["alerts"], use_container_width=True, hide_index=True)
    with right:
        st.subheader("High Risk Transactions")
        st.dataframe(risk["high_risk_transactions"], use_container_width=True, hide_index=True)


def render_ai_decision(sheets: dict[str, pd.DataFrame]) -> None:
    render_page_header(
        "AI Decision",
        "Generate a structured GPT recommendation from finance, risk, banking product, and customer data.",
        "Decision intelligence",
    )

    customers = sheets["03_CUSTOMERS"]
    customer_ids = customers["customer_id"].astype(str).tolist()
    selected_customer_id = st.selectbox("Customer profile", customer_ids)
    customer_profile = (
        customers.loc[customers["customer_id"].astype(str) == selected_customer_id].iloc[0].to_dict()
    )

    finance_summary = build_finance_summary(sheets)
    risk_alerts = build_risk_summary(sheets)["alerts"].to_dict(orient="records")
    available_products = sheets["11_BANK_PRODUCTS"].to_dict(orient="records")

    col1, col2 = st.columns([0.35, 0.65])
    with col1:
        st.markdown('<div class="section-title">Decision Inputs</div>', unsafe_allow_html=True)
        st.json(
            {
                "finance_summary": finance_summary,
                "risk_alert_count": len(risk_alerts),
                "available_product_count": len(available_products),
                "customer_profile": customer_profile,
            }
        )
        run_gpt = st.button("Run GPT Recommendation", type="primary", use_container_width=True)
    with col2:
        if run_gpt:
            with st.status("Calling OpenAI Responses API...", expanded=True) as status:
                try:
                    agent = OpenAIDecisionAgent()
                    decision = agent.decide(
                        finance_summary=finance_summary,
                        risk_alerts=risk_alerts,
                        available_banking_products=available_products,
                        customer_profile=customer_profile,
                    )
                except OpenAIDecisionAgentError as exc:
                    status.update(label="GPT recommendation failed", state="error")
                    st.error(str(exc))
                else:
                    st.session_state["decision"] = decision
                    st.session_state["approval"] = None
                    _audit(
                        "ai_decision_generated",
                        f"Recommended {decision['recommended_bank']} - {decision['recommended_product']}",
                        {"decision": decision},
                    )
                    status.update(label="GPT recommendation ready", state="complete")

        decision = st.session_state.get("decision")
        if decision:
            render_decision_card(decision)
        else:
            st.info("No GPT recommendation has been generated in this session.")


def render_decision_card(decision: dict[str, Any]) -> None:
    st.subheader("GPT Recommendation")
    render_kpi_row(
        [
            ("Confidence", format_percent(float(decision["confidence"])), "Model-reported certainty"),
            ("Recommended Bank", decision["recommended_bank"], "Selected financial partner"),
            ("Recommended Product", decision["recommended_product"], "Selected product"),
        ]
    )

    approval_label = "Required" if decision["requires_founder_approval"] else "Not required"
    st.info(f"Founder approval: {approval_label}")
    st.markdown(f"**Decision:** {decision['decision']}")

    st.markdown("**Reasoning**")
    for item in decision["reasoning"]:
        st.write(f"- {item}")


def render_founder_approval() -> None:
    render_page_header(
        "Founder Approval",
        "Approve, reject, and annotate the AI recommendation before final action.",
        "Governance checkpoint",
    )
    decision = st.session_state.get("decision")

    if not decision:
        st.info("Generate an AI Decision before requesting founder approval.")
        return

    render_decision_card(decision)

    st.subheader("Approval Action")
    with st.form("founder_approval_form", clear_on_submit=False):
        action = st.radio("Decision", ["Approve", "Reject"], horizontal=True)
        comments = st.text_area("Comments", placeholder="Add founder rationale or conditions.")
        submitted = st.form_submit_button("Submit Founder Decision", type="primary")

    if submitted:
        approval = {
            "action": action,
            "comments": comments,
            "submitted_at": utc_now(),
            "decision": decision,
        }
        st.session_state["approval"] = approval
        _audit(
            "founder_approval_submitted",
            f"Founder selected: {action}",
            {"comments": comments, "decision": decision},
        )
        st.success(f"Founder decision recorded: {action}")

    if st.session_state.get("approval"):
        st.subheader("Current Approval Record")
        st.json(st.session_state["approval"])


def render_audit_log(sheets: dict[str, pd.DataFrame]) -> None:
    render_page_header(
        "Audit Log",
        "Trace workbook ingestion, GPT decisions, founder actions, and triggered rules.",
        "Control evidence",
    )
    events = st.session_state.get("audit_events", [])

    st.subheader("Timeline")
    if events:
        st.dataframe(pd.DataFrame(events), use_container_width=True, hide_index=True)
    else:
        st.info("No session events recorded yet.")

    st.subheader("Decisions")
    decision = st.session_state.get("decision")
    approval = st.session_state.get("approval")
    st.json({"decision": decision, "approval": approval})

    st.subheader("Rule Triggers")
    triggers = build_risk_summary(sheets)["rule_triggers"]
    if triggers:
        st.dataframe(pd.DataFrame(triggers), use_container_width=True, hide_index=True)
    else:
        st.success("No active rule triggers.")


def _load_uploaded_workbook(uploaded_file: Any) -> dict[str, pd.DataFrame]:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temporary_file:
        temporary_file.write(uploaded_file.getbuffer())
        temporary_path = Path(temporary_file.name)

    try:
        return load_team_pack(temporary_path)
    finally:
        temporary_path.unlink(missing_ok=True)


def render_page_header(title: str, subtitle: str, eyebrow: str) -> None:
    st.markdown(
        f"""
        <div class="executive-shell">
            <div class="eyebrow">{eyebrow}</div>
            <h1>{title}</h1>
            <p class="page-subtitle">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_row(items: list[tuple[str, Any, str]]) -> None:
    columns = st.columns(len(items))
    for column, (label, value, note) in zip(columns, items):
        with column:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{value}</div>
                    <div class="kpi-note">{note}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def build_finance_summary(sheets: dict[str, pd.DataFrame]) -> dict[str, Any]:
    orders = sheets["06_ORDERS"]
    cashflow = sheets["09_CASHFLOW"]

    revenue = float(to_number(orders["order_revenue"]).sum())
    cost = float(to_number(orders["estimated_cost"]).sum())
    margin = 0.0 if revenue == 0 else (revenue - cost) / revenue

    closing_cash = to_number(cashflow["projected_closing_cash"])
    reserve_minimum = to_number(cashflow["cash_reserve_minimum"])
    latest_projected_closing_cash = float(closing_cash.iloc[-1]) if len(closing_cash) else 0.0
    lowest_projected_closing_cash = float(closing_cash.min()) if len(closing_cash) else 0.0

    return {
        "revenue": revenue,
        "cost": cost,
        "margin": margin,
        "latest_projected_closing_cash": latest_projected_closing_cash,
        "lowest_projected_closing_cash": lowest_projected_closing_cash,
        "cash_reserve_minimum": float(reserve_minimum.max()) if len(reserve_minimum) else 0.0,
    }


def build_risk_summary(sheets: dict[str, pd.DataFrame]) -> dict[str, Any]:
    alerts = sheets["14_ALERTS"].copy()
    transactions = sheets["08_BANK_TXN"].copy()
    rules = sheets["13_RISK_RULES"].copy()
    orders = sheets["06_ORDERS"].copy()
    cashflow = sheets["09_CASHFLOW"].copy()

    transactions["transaction_risk_score"] = to_number(transactions["transaction_risk_score"])
    high_risk_transactions = transactions[
        (transactions["transaction_risk_score"] >= 85)
        | (transactions["txn_status"].astype(str).str.lower() == "suspicious")
    ].copy()

    order_revenue = to_number(orders["order_revenue"])
    estimated_cost = to_number(orders["estimated_cost"])
    orders["gross_margin"] = (order_revenue - estimated_cost) / order_revenue.replace(0, pd.NA)
    low_margin_orders = orders[orders["gross_margin"] < 0.28].copy()

    closing_cash = to_number(cashflow["projected_closing_cash"])
    reserve = to_number(cashflow["cash_reserve_minimum"])
    cash_breaches = cashflow[closing_cash < reserve].copy()

    rule_triggers = []
    if not high_risk_transactions.empty:
        rule_triggers.append(rule_trigger(rules, "RR-001", f"{len(high_risk_transactions)} transaction(s)"))
    if not cash_breaches.empty:
        rule_triggers.append(rule_trigger(rules, "RR-002", f"{len(cash_breaches)} cashflow period(s)"))
    if not low_margin_orders.empty:
        rule_triggers.append(rule_trigger(rules, "RR-003", f"{len(low_margin_orders)} order(s)"))

    return {
        "alerts": alerts,
        "high_risk_transactions": high_risk_transactions,
        "rule_triggers": rule_triggers,
    }


def rule_trigger(rules: pd.DataFrame, rule_id: str, evidence: str) -> dict[str, Any]:
    match = rules.loc[rules["rule_id"].astype(str) == rule_id]
    if match.empty:
        return {
            "rule_id": rule_id,
            "severity": "Unknown",
            "required_action": "Review required",
            "evidence": evidence,
        }

    row = match.iloc[0].to_dict()
    return {
        "rule_id": rule_id,
        "severity": row.get("severity", "Unknown"),
        "required_action": row.get("required_action", "Review required"),
        "evidence": evidence,
    }


def _sheet_summary(sheets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"sheet": name, "rows": len(frame), "columns": len(frame.columns)}
            for name, frame in sheets.items()
        ]
    )


def _audit(event_type: str, message: str, payload: dict[str, Any] | None = None) -> None:
    event = {
        "timestamp": utc_now(),
        "event_type": event_type,
        "message": message,
        "payload": json.dumps(payload or {}, ensure_ascii=False, default=str),
    }
    st.session_state["audit_events"].append(event)


def to_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0)


def format_vnd(value: float | int) -> str:
    return f"{float(value):,.0f} VND"


def format_percent(value: float | int) -> str:
    return f"{float(value) * 100:.1f}%"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


if __name__ == "__main__":
    main()

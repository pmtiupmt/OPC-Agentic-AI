"""
Boilerplate multi-agent orchestration system for a One Person Company (OPC).

The classes are intentionally dependency-light so the core governance logic can
run in tests or notebooks. Replace AgentLLMAdapter.generate() with LangChain
chains or AutoGen agents when connecting real model providers.
"""

from __future__ import annotations

import dataclasses
import hashlib
import time
from decimal import Decimal
from enum import Enum
from typing import Any, Callable


VND_300M = Decimal("300000000")
VND_550M = Decimal("550000000")
RISK_HOLD_SCORE = Decimal("85")


class ApprovalState(str, Enum):
    AUTO_APPROVED = "auto_approved"
    PENDING_FOUNDER_APPROVAL = "pending_founder_approval"
    APPROVED = "approved"
    REJECTED = "rejected"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclasses.dataclass(frozen=True)
class GovernanceDecision:
    rule_code: str
    state: ApprovalState
    reason: str
    requires_founder_approval: bool
    masked_payload: dict[str, Any] | None = None


@dataclasses.dataclass
class AgentResult:
    agent: str
    summary: str
    data: dict[str, Any]
    decisions: list[GovernanceDecision] = dataclasses.field(default_factory=list)
    risk_alerts: list[dict[str, Any]] = dataclasses.field(default_factory=list)


class AgentLLMAdapter:
    """Thin placeholder for LangChain/AutoGen integration."""

    def generate(self, prompt: str, context: dict[str, Any]) -> str:
        return f"LLM adapter placeholder. Prompt={prompt!r}; context_keys={list(context)}"


def mask_value(value: Any) -> str:
    digest = hashlib.sha256(str(value).encode("utf-8")).hexdigest()
    return f"tok_{digest[:16]}"


def mask_sensitive_payload(payload: dict[str, Any]) -> dict[str, Any]:
    sensitive_keys = {
        "customer_name",
        "tax_id",
        "bank_account_ref",
        "txn_reference",
        "email",
        "phone",
    }
    masked: dict[str, Any] = {}
    for key, value in payload.items():
        masked[key] = mask_value(value) if key in sensitive_keys and value is not None else value
    return masked


def enforce_human_in_the_loop(
    *,
    risk_level: RiskLevel,
    action: str,
    amount_vnd: Decimal | int | str | None = None,
    transaction_risk_score: Decimal | int | str | None = None,
    payload_to_external_partner: dict[str, Any] | None = None,
    founder_confirmed_external_send: bool = False,
) -> GovernanceDecision:
    """
    Governance middleware for OPC rules.

    Auto-approve: Low-risk opportunities.
    RR-001: Founder approval unlocks transactions with risk score >= 85.
    RR-004: Founder confirmation before sending masked data externally.
    RR-005: Founder approval for contract/financial decisions over 300M VND.
    """

    score = Decimal(str(transaction_risk_score)) if transaction_risk_score is not None else None
    amount = Decimal(str(amount_vnd)) if amount_vnd is not None else None

    if score is not None and score >= RISK_HOLD_SCORE:
        return GovernanceDecision(
            rule_code="RR-001",
            state=ApprovalState.PENDING_FOUNDER_APPROVAL,
            reason="Transaction risk score is at or above 85; temporary hold remains until Founder approval.",
            requires_founder_approval=True,
        )

    if payload_to_external_partner is not None:
        masked = mask_sensitive_payload(payload_to_external_partner)
        if not founder_confirmed_external_send:
            return GovernanceDecision(
                rule_code="RR-004",
                state=ApprovalState.PENDING_FOUNDER_APPROVAL,
                reason="Masked data is ready, but external partner transmission needs Founder confirmation.",
                requires_founder_approval=True,
                masked_payload=masked,
            )
        return GovernanceDecision(
            rule_code="RR-004",
            state=ApprovalState.APPROVED,
            reason="Founder confirmed external partner transmission of masked data.",
            requires_founder_approval=False,
            masked_payload=masked,
        )

    if amount is not None and amount > VND_300M and action in {"contract", "financial_decision"}:
        return GovernanceDecision(
            rule_code="RR-005",
            state=ApprovalState.PENDING_FOUNDER_APPROVAL,
            reason="Contract or financial decision exceeds 300 million VND.",
            requires_founder_approval=True,
        )

    if risk_level == RiskLevel.LOW:
        return GovernanceDecision(
            rule_code="AUTO-APPROVE",
            state=ApprovalState.AUTO_APPROVED,
            reason="Low-risk opportunity is eligible for automatic approval.",
            requires_founder_approval=False,
        )

    return GovernanceDecision(
        rule_code="DEFAULT-HITL",
        state=ApprovalState.PENDING_FOUNDER_APPROVAL,
        reason="Non-low-risk action requires Founder review by default.",
        requires_founder_approval=True,
    )


class DataFinanceAgent:
    """Agent 1: integrates orders, invoices, and bank transactions."""

    name = "data_finance_agent"

    def run(self, task: dict[str, Any]) -> AgentResult:
        orders = task.get("orders", [])
        invoices = task.get("invoices", [])
        bank_transactions = task.get("bank_transactions", [])
        opening_cash = Decimal(str(task.get("opening_cash_vnd", 0)))

        confirmed_revenue = sum(Decimal(str(order.get("revenue", 0))) for order in orders)
        confirmed_cost = sum(Decimal(str(order.get("cost", 0))) for order in orders)
        expected_invoice_inflows = sum(
            Decimal(str(inv.get("amount_vnd", 0)))
            for inv in invoices
            if inv.get("status") in {"issued", "overdue"}
        )
        posted_inflows = sum(
            Decimal(str(txn.get("amount_vnd", 0)))
            for txn in bank_transactions
            if txn.get("direction") == "inflow" and txn.get("status") == "posted"
        )
        posted_outflows = sum(
            abs(Decimal(str(txn.get("amount_vnd", 0))))
            for txn in bank_transactions
            if txn.get("direction") == "outflow" and txn.get("status") == "posted"
        )

        projected_closing_cash = opening_cash + expected_invoice_inflows + posted_inflows - posted_outflows
        margin = None if confirmed_revenue == 0 else (confirmed_revenue - confirmed_cost) / confirmed_revenue

        alerts: list[dict[str, Any]] = []
        decisions: list[GovernanceDecision] = []
        if projected_closing_cash < VND_550M:
            alerts.append(
                {
                    "rule_code": "RR-002",
                    "severity": "high",
                    "message": "Projected closing cash is below 550M VND.",
                    "projected_closing_cash": str(projected_closing_cash),
                }
            )
            decisions.append(
                GovernanceDecision(
                    rule_code="RR-002",
                    state=ApprovalState.PENDING_FOUNDER_APPROVAL,
                    reason="Cashflow runway breach needs Founder review.",
                    requires_founder_approval=True,
                )
            )

        return AgentResult(
            agent=self.name,
            summary="Cashflow projection and order margin calculated.",
            data={
                "projected_closing_cash": str(projected_closing_cash),
                "aggregate_margin": None if margin is None else str(margin),
                "expected_invoice_inflows": str(expected_invoice_inflows),
                "posted_inflows": str(posted_inflows),
                "posted_outflows": str(posted_outflows),
            },
            decisions=decisions,
            risk_alerts=alerts,
        )


class RiskComplianceAgent:
    """Agent 2: applies risk rules and masks data before trust-boundary exit."""

    name = "risk_compliance_agent"

    def run(self, task: dict[str, Any]) -> AgentResult:
        bank_transactions = task.get("bank_transactions", [])
        external_payload = task.get("external_payload")
        founder_confirmed = bool(task.get("founder_confirmed_external_send", False))

        alerts: list[dict[str, Any]] = []
        decisions: list[GovernanceDecision] = []
        held_transactions: list[dict[str, Any]] = []

        for txn in bank_transactions:
            score = Decimal(str(txn.get("transaction_risk_score", 0)))
            if score >= RISK_HOLD_SCORE:
                held = {**txn, "status": "held"}
                held_transactions.append(held)
                alerts.append(
                    {
                        "rule_code": "RR-001",
                        "severity": "critical",
                        "entity_type": "bank_transaction",
                        "entity_id": txn.get("txn_id"),
                        "message": "Transaction placed on temporary hold.",
                    }
                )
                decisions.append(
                    enforce_human_in_the_loop(
                        risk_level=RiskLevel.CRITICAL,
                        action="unlock_transaction",
                        transaction_risk_score=score,
                    )
                )

        masked_payload = None
        if external_payload is not None:
            decision = enforce_human_in_the_loop(
                risk_level=RiskLevel.MEDIUM,
                action="send_external_partner_data",
                payload_to_external_partner=external_payload,
                founder_confirmed_external_send=founder_confirmed,
            )
            decisions.append(decision)
            masked_payload = decision.masked_payload

        return AgentResult(
            agent=self.name,
            summary="Risk rules applied and external payload tokenized when present.",
            data={"held_transactions": held_transactions, "masked_payload": masked_payload},
            decisions=decisions,
            risk_alerts=alerts,
        )


class DecisionPartnerAgent:
    """Agent 3: matches financial needs with partner API products."""

    name = "decision_partner_agent"

    partner_products = {
        "VietinBank": ["working_capital_line", "invoice_financing", "fx_payment"],
        "CoopBank": ["short_term_cash_buffer", "supplier_payment"],
        "PartnerX": ["dynamic_discounting", "collections_automation"],
    }

    def __init__(self, api_call: Callable[[str, str, dict[str, Any]], dict[str, Any]] | None = None):
        self.api_call = api_call or self._mock_api_call

    def run(self, task: dict[str, Any]) -> AgentResult:
        need = task.get("financial_need", "working_capital")
        amount = Decimal(str(task.get("amount_vnd", 0)))
        risk_level = RiskLevel(task.get("risk_level", "medium"))

        matches = self._match_products(need)
        partner_responses = []
        for partner, product in matches:
            response = self._call_with_retry(partner, product, {"need": need, "amount_vnd": str(amount)})
            partner_responses.append(response)

        governance = enforce_human_in_the_loop(
            risk_level=risk_level,
            action="financial_decision",
            amount_vnd=amount,
        )

        return AgentResult(
            agent=self.name,
            summary="Partner products matched and governance decision produced.",
            data={"matches": matches, "partner_responses": partner_responses},
            decisions=[governance],
        )

    def _match_products(self, need: str) -> list[tuple[str, str]]:
        normalized_need = need.lower()
        matches = []
        for partner, products in self.partner_products.items():
            for product in products:
                if any(token in product for token in normalized_need.split("_")):
                    matches.append((partner, product))
        return matches or [
            ("VietinBank", "working_capital_line"),
            ("CoopBank", "short_term_cash_buffer"),
            ("PartnerX", "dynamic_discounting"),
        ]

    def _call_with_retry(
        self,
        partner: str,
        product: str,
        payload: dict[str, Any],
        *,
        max_attempts: int = 3,
        base_sleep_seconds: float = 0.25,
    ) -> dict[str, Any]:
        last_error = None
        for attempt in range(1, max_attempts + 1):
            try:
                return self.api_call(partner, product, payload)
            except (TimeoutError, ConnectionError) as exc:
                last_error = exc
                time.sleep(base_sleep_seconds * attempt)
        return {
            "partner": partner,
            "product": product,
            "status": "retry_exhausted",
            "error": str(last_error),
        }

    @staticmethod
    def _mock_api_call(partner: str, product: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {"partner": partner, "product": product, "status": "available", "payload": payload}


class ChiefOperatingAgent:
    """Agent 0: orchestrates task decomposition, routing, and aggregation."""

    name = "chief_operating_agent"

    def __init__(self):
        self.data_finance_agent = DataFinanceAgent()
        self.risk_compliance_agent = RiskComplianceAgent()
        self.decision_partner_agent = DecisionPartnerAgent()

    def run(self, objective: str, context: dict[str, Any]) -> AgentResult:
        route_plan = self._decompose(objective, context)
        child_results: list[AgentResult] = []

        if "finance" in route_plan:
            child_results.append(self.data_finance_agent.run(context))
        if "risk" in route_plan:
            child_results.append(self.risk_compliance_agent.run(context))
        if "partners" in route_plan:
            child_results.append(self.decision_partner_agent.run(context))

        aggregate_data = {
            "objective": objective,
            "route_plan": route_plan,
            "child_results": [dataclasses.asdict(result) for result in child_results],
        }
        decisions = [decision for result in child_results for decision in result.decisions]
        alerts = [alert for result in child_results for alert in result.risk_alerts]

        return AgentResult(
            agent=self.name,
            summary="Objective decomposed, routed, and aggregated.",
            data=aggregate_data,
            decisions=decisions,
            risk_alerts=alerts,
        )

    @staticmethod
    def _decompose(objective: str, context: dict[str, Any]) -> list[str]:
        objective_text = objective.lower()
        routes = []
        if any(key in context for key in ("orders", "invoices", "opening_cash_vnd")):
            routes.append("finance")
        if "risk" in objective_text or "bank_transactions" in context or "external_payload" in context:
            routes.append("risk")
        if "partner" in objective_text or "financial_need" in context:
            routes.append("partners")
        return routes or ["finance", "risk", "partners"]


def demo() -> AgentResult:
    coa = ChiefOperatingAgent()
    return coa.run(
        "Assess cashflow risk and find partner financing options",
        {
            "opening_cash_vnd": "480000000",
            "orders": [{"order_id": "o1", "revenue": "200000000", "cost": "120000000"}],
            "invoices": [{"invoice_id": "i1", "amount_vnd": "50000000", "status": "issued"}],
            "bank_transactions": [
                {
                    "txn_id": "t1",
                    "amount_vnd": "10000000",
                    "direction": "inflow",
                    "status": "posted",
                    "transaction_risk_score": "91",
                }
            ],
            "financial_need": "working_capital",
            "amount_vnd": "350000000",
            "risk_level": "medium",
            "external_payload": {
                "customer_name": "Example Co",
                "tax_id": "0123456789",
                "bank_account_ref": "9704000012345678",
                "requested_amount_vnd": "350000000",
            },
        },
    )


if __name__ == "__main__":
    result = demo()
    print(dataclasses.asdict(result))

"""Excel loader for the MISTalent 2026 OPC Team Pack.

The loader intentionally does only three things:
1. read every worksheet from a Team Pack workbook,
2. validate the expected worksheet names,
3. validate the expected columns for each required worksheet.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pandas as pd


REQUIRED_SHEETS: Final[tuple[str, ...]] = (
    "00_GUIDE",
    "01_README",
    "02_OPC_PROFILE",
    "03_CUSTOMERS",
    "04_CONTRACTS",
    "05_PRODUCTS",
    "06_ORDERS",
    "07_INVOICES",
    "08_BANK_TXN",
    "09_CASHFLOW",
    "10_CREDIT_PROFILE",
    "11_BANK_PRODUCTS",
    "12_API_CATALOG",
    "13_RISK_RULES",
    "14_ALERTS",
    "15_AGENT_TASKS",
    "19_DATA_DICTIONARY",
    "16_PUBLIC_TESTS",
    "20_DATA_CLASS",
    "21_MASKING_EXAMPLES",
    "22_API_HANDLING_RULES",
    "23_DESIGN_LOG",
    "24_AI_USE_DISCLOSURE",
    "25_RUNTIME_LOG_SCHEMA",
    "26_API_ASSUMPTIONS",
    "17_CRISIS_CARD_TEMPLATE",
)


REQUIRED_COLUMNS: Final[dict[str, tuple[str, ...]]] = {
    "00_GUIDE": ("MISTalent 2026 - OPC Agentic AI Team Pack V3",),
    "01_README": ("key", "value"),
    "02_OPC_PROFILE": ("field", "value"),
    "03_CUSTOMERS": (
        "customer_id",
        "customer_name",
        "customer_type",
        "province",
        "industry",
        "strategic_value",
        "revenue_model",
        "payment_reliability",
        "banking_fit_hint",
    ),
    "04_CONTRACTS": (
        "contract_id",
        "customer_id",
        "start_date",
        "end_date",
        "status",
        "description",
        "contract_value",
        "gross_margin",
        "payment_terms",
    ),
    "05_PRODUCTS": (
        "service_id",
        "service_name",
        "pricing_model",
        "list_price",
        "target_margin",
        "target_segment",
    ),
    "06_ORDERS": (
        "order_id",
        "contract_id",
        "customer_id",
        "order_date",
        "due_date",
        "status",
        "service_id",
        "order_revenue",
        "estimated_cost",
        "delivery_note",
    ),
    "07_INVOICES": (
        "invoice_id",
        "order_id",
        "customer_id",
        "issue_date",
        "due_date",
        "status",
        "invoice_amount",
        "paid_date",
    ),
    "08_BANK_TXN": (
        "txn_id",
        "txn_date",
        "bank",
        "account_id",
        "direction",
        "description",
        "amount",
        "counterparty_id",
        "txn_status",
        "transaction_risk_score",
    ),
    "09_CASHFLOW": (
        "month",
        "expected_cash_in",
        "expected_cash_out",
        "direct_cost",
        "opex",
        "cash_reserve_minimum",
        "projected_closing_cash",
        "management_note",
    ),
    "10_CREDIT_PROFILE": (
        "credit_case_id",
        "company_id",
        "request_type",
        "requested_amount",
        "tenor",
        "collateral_or_basis",
        "eligibility_score",
        "precheck_note",
        "approval_status",
    ),
    "11_BANK_PRODUCTS": (
        "bank_product_id",
        "bank",
        "product_name",
        "target_segment",
        "description",
        "annual_rate_or_fee",
        "processing_fee_rate",
        "collateral_ratio",
        "minimum_amount",
        "automation_level",
        "fit_note",
    ),
    "12_API_CATALOG": (
        "api_id",
        "provider",
        "method",
        "endpoint",
        "description",
        "required_fields",
        "payload_example",
        "recommended_core_role",
        "catalog_status",
        "extension_rule",
    ),
    "13_RISK_RULES": (
        "rule_id",
        "risk_type",
        "trigger_condition",
        "severity",
        "required_action",
        "owner_agent",
    ),
    "14_ALERTS": (
        "alert_id",
        "alert_date",
        "alert_type",
        "related_record",
        "severity",
        "risk_score",
        "description",
        "recommended_action",
    ),
    "15_AGENT_TASKS": (
        "task_id",
        "core_role",
        "suggested_agent_or_skill",
        "task_description",
        "minimum_baseline_inputs",
        "allowed_extended_inputs",
        "expected_handoff_output",
        "round_usage",
    ),
    "19_DATA_DICTIONARY": ("sheet_name", "column_name", "data_type", "description"),
    "16_PUBLIC_TESTS": (
        "test_id",
        "round",
        "test_type",
        "team_visible_trigger",
        "required_observable_behavior",
        "pass_condition",
    ),
    "20_DATA_CLASS": (
        "data_pattern",
        "example_field",
        "classification",
        "external_api_rule",
        "masking_or_tokenization",
        "logging_rule",
    ),
    "21_MASKING_EXAMPLES": (
        "source_field",
        "raw_example",
        "masked_example",
        "tokenized_example",
        "allowed_for_partner_api",
        "reason",
    ),
    "22_API_HANDLING_RULES": (
        "rule_id",
        "applies_to",
        "possible_issue",
        "team_visible_meaning",
        "required_handling",
        "requires_human_approval",
        "sensitive_fields",
        "note",
    ),
    "23_DESIGN_LOG": (
        "decision_no",
        "round",
        "artifact_area",
        "architectural_decision",
        "options_considered",
        "rationale",
        "owner",
        "verification_method",
        "tool_used",
        "ai_assistance",
        "evidence_link",
    ),
    "24_AI_USE_DISCLOSURE": (
        "disclosure_type",
        "round",
        "artifact_or_function",
        "ai_tool_or_openai_service",
        "purpose",
        "input_data_classification",
        "output_used",
        "human_verification",
        "responsible_member",
    ),
    "25_RUNTIME_LOG_SCHEMA": (
        "field",
        "required",
        "description",
        "example_or_rule",
        "round_relevance",
    ),
    "26_API_ASSUMPTIONS": (
        "assumption_id",
        "external_provider_or_source",
        "business_purpose",
        "mock_endpoint_or_dataset",
        "required_fields",
        "mock_data_added_by_team",
        "agent_or_skill_using_it",
        "risk_control",
        "declared_in_report",
    ),
    "17_CRISIS_CARD_TEMPLATE": (
        "crisis_field",
        "allowed_change_type",
        "baseline_record_or_metric",
        "example_placeholder",
        "affected_agent",
        "expected_dashboard_update",
        "team_action",
        "note",
    ),
}


class TeamPackLoadError(Exception):
    """Base exception for Team Pack loading and validation failures."""


class TeamPackFileNotFoundError(TeamPackLoadError):
    """Raised when the requested Team Pack workbook does not exist."""


class TeamPackReadError(TeamPackLoadError):
    """Raised when the workbook cannot be read as an Excel file."""


class MissingRequiredSheetsError(TeamPackLoadError):
    """Raised when one or more required worksheets are absent."""


class MissingRequiredColumnsError(TeamPackLoadError):
    """Raised when one or more worksheets lack required columns."""


def load_team_pack(path: str | Path = "TeamPack.xlsx") -> dict[str, pd.DataFrame]:
    """Read and validate a Team Pack workbook.

    Args:
        path: Path to the Team Pack Excel workbook.

    Returns:
        A dictionary mapping worksheet names to pandas DataFrames.

    Raises:
        TeamPackFileNotFoundError: If the workbook path does not exist.
        TeamPackReadError: If pandas cannot read the workbook.
        MissingRequiredSheetsError: If required worksheets are missing.
        MissingRequiredColumnsError: If required columns are missing.
    """

    workbook_path = Path(path)
    if not workbook_path.exists():
        raise TeamPackFileNotFoundError(f"Team Pack workbook not found: {workbook_path}")
    if not workbook_path.is_file():
        raise TeamPackFileNotFoundError(f"Team Pack path is not a file: {workbook_path}")

    try:
        sheets = pd.read_excel(workbook_path, sheet_name=None, engine="openpyxl")
    except Exception as exc:  # noqa: BLE001 - preserve the original reader failure.
        raise TeamPackReadError(f"Failed to read Team Pack workbook '{workbook_path}': {exc}") from exc

    normalized_sheets = {str(name).strip(): _normalize_columns(frame) for name, frame in sheets.items()}
    _validate_required_sheets(normalized_sheets)
    _validate_required_columns(normalized_sheets)
    return normalized_sheets


def _normalize_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    normalized = dataframe.copy()
    normalized.columns = [str(column).strip() for column in normalized.columns]
    return normalized


def _validate_required_sheets(sheets: dict[str, pd.DataFrame]) -> None:
    missing = [sheet for sheet in REQUIRED_SHEETS if sheet not in sheets]
    if missing:
        available = ", ".join(sheets)
        required = ", ".join(missing)
        raise MissingRequiredSheetsError(
            f"Missing required worksheet(s): {required}. Available worksheets: {available}"
        )


def _validate_required_columns(sheets: dict[str, pd.DataFrame]) -> None:
    missing_by_sheet: dict[str, list[str]] = {}
    for sheet_name, required_columns in REQUIRED_COLUMNS.items():
        if sheet_name not in sheets:
            continue

        available_columns = set(sheets[sheet_name].columns)
        missing_columns = [column for column in required_columns if column not in available_columns]
        if missing_columns:
            missing_by_sheet[sheet_name] = missing_columns

    if missing_by_sheet:
        details = "; ".join(
            f"{sheet}: missing {', '.join(columns)}" for sheet, columns in missing_by_sheet.items()
        )
        raise MissingRequiredColumnsError(f"Missing required column(s): {details}")


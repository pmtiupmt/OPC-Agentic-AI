"""OpenAI-backed decision agent for OPC banking recommendations."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Final


DEFAULT_MODEL: Final[str] = "gpt-5.5"
DEFAULT_ENV_PATH: Final[str] = ".env"
MAX_ATTEMPTS: Final[int] = 3


DECISION_SCHEMA: Final[dict[str, Any]] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "decision": {"type": "string"},
        "recommended_bank": {"type": "string"},
        "recommended_product": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "reasoning": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3,
            "maxItems": 3,
        },
        "requires_founder_approval": {"type": "boolean"},
    },
    "required": [
        "decision",
        "recommended_bank",
        "recommended_product",
        "confidence",
        "reasoning",
        "requires_founder_approval",
    ],
}


class OpenAIDecisionAgentError(Exception):
    """Base exception for OpenAI decision-agent failures."""


class OpenAISDKNotInstalledError(OpenAIDecisionAgentError):
    """Raised when the official OpenAI Python SDK is unavailable."""


class OpenAIAPIKeyError(OpenAIDecisionAgentError):
    """Raised when OPENAI_API_KEY is not available from the environment or .env."""


class OpenAIDecisionAPIError(OpenAIDecisionAgentError):
    """Raised when the OpenAI API call fails after retries."""


class OpenAIDecisionResponseError(OpenAIDecisionAgentError):
    """Raised when the model response cannot be parsed or validated."""


class OpenAIDecisionAgent:
    """Decision agent that calls the OpenAI Responses API and returns structured JSON."""

    def __init__(
        self,
        *,
        model: str = DEFAULT_MODEL,
        env_path: str | Path = DEFAULT_ENV_PATH,
        max_attempts: int = MAX_ATTEMPTS,
        base_sleep_seconds: float = 0.5,
    ) -> None:
        self.model = model
        self.env_path = Path(env_path)
        self.max_attempts = max_attempts
        self.base_sleep_seconds = base_sleep_seconds

        _load_dotenv(self.env_path)
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise OpenAIAPIKeyError(
                f"OPENAI_API_KEY is not set. Add it to the environment or to {self.env_path}."
            )

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise OpenAISDKNotInstalledError(
                "The official OpenAI Python SDK is required. Install the 'openai' package."
            ) from exc

        self.client = OpenAI(api_key=api_key)

    def decide(
        self,
        *,
        finance_summary: dict[str, Any],
        risk_alerts: list[dict[str, Any]],
        available_banking_products: list[dict[str, Any]],
        customer_profile: dict[str, Any],
    ) -> dict[str, Any]:
        """Return a banking decision as a JSON-compatible dictionary."""

        payload = {
            "finance_summary": finance_summary,
            "risk_alerts": risk_alerts,
            "available_banking_products": available_banking_products,
            "customer_profile": customer_profile,
        }

        response_text = self._call_responses_api(payload)
        decision = _parse_json_response(response_text)
        _validate_decision(decision)
        return decision

    def decide_json(
        self,
        *,
        finance_summary: dict[str, Any],
        risk_alerts: list[dict[str, Any]],
        available_banking_products: list[dict[str, Any]],
        customer_profile: dict[str, Any],
    ) -> str:
        """Return the banking decision as a compact JSON string."""

        decision = self.decide(
            finance_summary=finance_summary,
            risk_alerts=risk_alerts,
            available_banking_products=available_banking_products,
            customer_profile=customer_profile,
        )
        return json.dumps(decision, ensure_ascii=False, separators=(",", ":"))

    def _call_responses_api(self, payload: dict[str, Any]) -> str:
        last_error: Exception | None = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                response = self.client.responses.create(
                    model=self.model,
                    input=[
                        {
                            "role": "system",
                            "content": (
                                "You are an OPC financial decision agent. "
                                "Return only JSON that matches the provided schema. "
                                "Recommend one banking product using the supplied finance, risk, "
                                "banking product, and customer profile data. "
                                "Set requires_founder_approval to true when the decision is high risk, "
                                "involves external partner submission, or exceeds 300 million VND."
                            ),
                        },
                        {
                            "role": "user",
                            "content": json.dumps(payload, ensure_ascii=False, default=str),
                        },
                    ],
                    text={
                        "format": {
                            "type": "json_schema",
                            "name": "opc_banking_decision",
                            "strict": True,
                            "schema": DECISION_SCHEMA,
                        }
                    },
                )

                if getattr(response, "status", None) == "incomplete":
                    reason = getattr(getattr(response, "incomplete_details", None), "reason", "unknown")
                    raise OpenAIDecisionResponseError(f"OpenAI response was incomplete: {reason}")

                output_text = getattr(response, "output_text", None)
                if not output_text:
                    raise OpenAIDecisionResponseError("OpenAI response did not include output_text.")

                return output_text
            except OpenAIDecisionResponseError:
                raise
            except Exception as exc:  # noqa: BLE001 - normalize SDK/network errors for callers.
                last_error = exc
                if attempt == self.max_attempts:
                    break
                time.sleep(self.base_sleep_seconds * attempt)

        raise OpenAIDecisionAPIError(
            f"OpenAI Responses API failed after {self.max_attempts} attempt(s): {last_error}"
        ) from last_error


def _load_dotenv(env_path: Path) -> None:
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _parse_json_response(response_text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise OpenAIDecisionResponseError(f"OpenAI response was not valid JSON: {exc}") from exc

    if not isinstance(parsed, dict):
        raise OpenAIDecisionResponseError("OpenAI response JSON must be an object.")
    return parsed


def _validate_decision(decision: dict[str, Any]) -> None:
    required_fields = DECISION_SCHEMA["required"]
    missing = [field for field in required_fields if field not in decision]
    if missing:
        raise OpenAIDecisionResponseError(f"OpenAI decision JSON is missing field(s): {', '.join(missing)}")

    expected_types = {
        "decision": str,
        "recommended_bank": str,
        "recommended_product": str,
        "confidence": (int, float),
        "reasoning": list,
        "requires_founder_approval": bool,
    }
    for field, expected_type in expected_types.items():
        if not isinstance(decision[field], expected_type):
            raise OpenAIDecisionResponseError(f"Field '{field}' has invalid type.")

    confidence = float(decision["confidence"])
    if confidence < 0.0 or confidence > 1.0:
        raise OpenAIDecisionResponseError("Field 'confidence' must be between 0.0 and 1.0.")

    reasoning = decision["reasoning"]
    if len(reasoning) != 3 or not all(isinstance(item, str) for item in reasoning):
        raise OpenAIDecisionResponseError("Field 'reasoning' must contain exactly three strings.")


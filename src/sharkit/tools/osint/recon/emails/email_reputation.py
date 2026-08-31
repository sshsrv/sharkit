from __future__ import annotations

import json

from sharkit.network.client import HttpClient
from sharkit.tools.base import (
    ExecutionContext,
    OptionDefinition,
    Result,
    Tool,
    ToolMetadata,
)


class EmailReputationTool(Tool):
    metadata = ToolMetadata(
        name="email_reputation",
        description="Check email reputation and suspicious activity via emailrep.io",
        category="osint.humint.reputation",
        author="sharkit",
        version="0.1.0",
        safety="safe",
        color="#E74C3C",
    )

    def __init__(self) -> None:
        self._options: dict[str, OptionDefinition] = {
            "email": OptionDefinition(
                name="email",
                description="Email address to check",
                required=True,
            ),
        }

    def get_options(self) -> dict[str, OptionDefinition]:
        return self._options

    def execute(self, context: ExecutionContext) -> Result:
        email = context.options.get("email") or ""
        if not email:
            return Result(success=False, error="Option 'email' is required.")

        url = f"https://emailrep.io/{email}"
        with HttpClient() as client:
            try:
                resp = client.get(url, timeout=30)
            except Exception as exc:
                return Result(success=False, error=f"Request failed: {exc}")

        try:
            data = json.loads(resp.content)
        except json.JSONDecodeError:
            return Result(success=False, error="Invalid JSON response from API.")

        score = data.get("reputation", "unknown")
        suspicious = data.get("suspicious", False)
        details = data.get("details", {})

        lines: list[str] = []
        lines.append(f"Email: {email}")
        lines.append(f"Reputation: {score}")
        lines.append(f"Suspicious: {'Yes' if suspicious else 'No'}")

        if details:
            lines.append("\n--- Details ---")
            details_fields = [
                ("blacklisted", "Blacklisted"),
                ("credentials_leaked", "Credentials Leaked"),
                ("data_breach", "Data Breach"),
                ("domain_reputation", "Domain Reputation"),
                ("deliverable", "Deliverable"),
                ("valid_mx", "Valid MX"),
                ("profiles", "Profiles"),
            ]
            for key, label in details_fields:
                value = details.get(key)
                if value is not None:
                    if isinstance(value, bool):
                        display = "Yes" if value else "No"
                    elif isinstance(value, list):
                        display = ", ".join(value) if value else "None"
                    else:
                        display = str(value)
                    lines.append(f"  {label}: {display}")

        result_text = "\n".join(lines)
        return Result(success=True, data={"result": result_text})

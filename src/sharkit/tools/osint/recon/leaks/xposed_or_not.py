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


class XposedOrNotTool(Tool):
    metadata = ToolMetadata(
        name="xposed_or_not",
        description="Check if an email has been exposed in known data breaches via XposedOrNot",
        category="osint.humint.leaks",
        author="sharkit",
        version="0.1.0",
        safety="safe",
        color="#9B59B6",
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

        url = f"https://api.xposedornot.com/v1/check-email/{email}?details=true"
        with HttpClient() as client:
            try:
                resp = client.get(url, timeout=30)
            except Exception as exc:
                return Result(success=False, error=f"Request failed: {exc}")

        try:
            data = json.loads(resp.content)
        except json.JSONDecodeError:
            return Result(success=False, error="Invalid JSON response from API.")

        status = data.get("status")
        if status == "not_found":
            result_text = f"Email: {email}\nNo breaches found for this email."
            return Result(success=True, data={"result": result_text})

        breaches = data.get("breaches_details", [])

        lines: list[str] = []
        lines.append(f"Email: {email}")
        lines.append(f"Breaches found: {len(breaches)}")

        if breaches:
            lines.append("\n--- Breaches ---")
            for breach in breaches:
                name = breach.get("breach", "Unknown")
                date = breach.get("xposed_date", "Unknown")
                records = breach.get("xposed_records", "Unknown")
                data_classes = breach.get("data_classes", [])
                date_display = date if date else "Unknown date"
                records_display = records if records else "Unknown"
                lines.append(f"  [{date_display}] {name} ({records_display} records)")
                if data_classes:
                    lines.append(f"    Data exposed: {', '.join(data_classes)}")

        result_text = "\n".join(lines)
        return Result(success=True, data={"result": result_text})

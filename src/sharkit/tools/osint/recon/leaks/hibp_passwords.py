from __future__ import annotations

import contextlib
import hashlib

from sharkit.network.client import HttpClient
from sharkit.tools.base import (
    ExecutionContext,
    OptionDefinition,
    Result,
    Tool,
    ToolMetadata,
)


class HIBPPasswordsTool(Tool):
    metadata = ToolMetadata(
        name="hibp_passwords",
        description="Check if a password has been exposed in known breaches using k-anonymity",
        category="osint.humint.leaks",
        author="sharkit",
        version="0.1.0",
        safety="safe",
        color="#F39C12",
    )

    def __init__(self) -> None:
        self._options: dict[str, OptionDefinition] = {
            "password": OptionDefinition(
                name="password",
                description="Password to check (never transmitted in full)",
                required=True,
            ),
        }

    def get_options(self) -> dict[str, OptionDefinition]:
        return self._options

    def execute(self, context: ExecutionContext) -> Result:
        password = context.options.get("password") or ""
        if not password:
            return Result(success=False, error="Option 'password' is required.")

        # k-anonymity: hash password with SHA1, send only first 5 chars
        sha1_hash = hashlib.sha1(password.encode()).hexdigest().upper()
        prefix = sha1_hash[:5]
        suffix = sha1_hash[5:]

        url = f"https://api.pwnedpasswords.com/range/{prefix}"
        with HttpClient() as client:
            try:
                resp = client.get(url, timeout=30)
            except Exception as exc:
                return Result(success=False, error=f"Request failed: {exc}")

        # Parse response: lines of "SUFFIX:COUNT"
        response_text = resp.content.decode("utf-8", errors="replace")
        count = 0
        for line in response_text.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(":")
            if len(parts) == 2 and parts[0] == suffix:
                with contextlib.suppress(ValueError):
                    count = int(parts[1])
                break

        lines: list[str] = []
        if count > 0:
            lines.append("WARNING: Password found in known breaches!")
            lines.append(f"Exposure count: {count:,}")
            lines.append(
                "This password has appeared in data breaches and should not be used."
            )
        else:
            lines.append("Password not found in known breaches.")
            lines.append(
                "Note: This does not guarantee the password is secure."
            )

        result_text = "\n".join(lines)
        return Result(success=True, data={"result": result_text})

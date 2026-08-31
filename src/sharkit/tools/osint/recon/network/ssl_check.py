from __future__ import annotations

import datetime
import socket
import ssl

from sharkit.tools.base import (
    ExecutionContext,
    OptionDefinition,
    Result,
    Tool,
    ToolMetadata,
)


class SSLCheckTool(Tool):
    metadata = ToolMetadata(
        name="ssl_check",
        description="SSL/TLS certificate information and analysis",
        category="osint.recon.network",
        author="sharkit",
        version="0.1.0",
        safety="safe",
        color="#2ECC71",
    )

    def __init__(self) -> None:
        self._options: dict[str, OptionDefinition] = {
            "host": OptionDefinition(
                name="host",
                description="Target hostname",
                required=True,
            ),
            "port": OptionDefinition(
                name="port",
                description="Port to connect to",
                required=False,
                default="443",
            ),
        }

    def get_options(self) -> dict[str, OptionDefinition]:
        return self._options

    def execute(self, context: ExecutionContext) -> Result:
        host = context.options.get("host") or ""
        if not host:
            return Result(success=False, error="Option 'host' is required.")

        port_spec = context.options.get("port") or "443"
        try:
            port = int(port_spec)
        except ValueError:
            return Result(success=False, error="Port must be a number.")

        try:
            ctx = ssl.create_default_context()
            with (
                socket.create_connection((host, port), timeout=10) as sock,
                ctx.wrap_socket(sock, server_hostname=host) as ssock,
            ):
                cert = ssock.getpeercert()
                cipher = ssock.cipher()
                version = ssock.version()
        except Exception as exc:
            return Result(success=False, error=f"SSL connection failed: {exc}")

        if cert is None:
            return Result(success=False, error=f"No certificate available for {host}:{port}.")

        def _flatten_name_entries(value: object) -> dict[str, str]:
            result: dict[str, str] = {}
            items = value if isinstance(value, (list, tuple)) else ()
            for item in items:
                if not isinstance(item, (list, tuple)):
                    continue
                for pair in item:
                    if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                        continue
                    key, val = pair
                    if isinstance(key, str) and isinstance(val, str):
                        result[key] = val
            return result

        lines: list[str] = [f"SSL Certificate for {host}:{port}:"]
        lines.append("")

        subject = _flatten_name_entries(cert.get("subject"))
        subject_str = ", ".join(f"{k}={v}" for k, v in subject.items())
        lines.append(f"  Subject:          {subject_str}")

        issuer = _flatten_name_entries(cert.get("issuer"))
        issuer_str = ", ".join(f"{k}={v}" for k, v in issuer.items())
        lines.append(f"  Issuer:           {issuer_str}")

        serial = str(cert.get("serialNumber", "?"))
        lines.append(f"  Serial Number:    {serial}")

        not_before = str(cert.get("notBefore", "?"))
        not_after = str(cert.get("notAfter", "?"))
        lines.append(f"  Valid From:       {not_before}")
        lines.append(f"  Valid Until:      {not_after}")

        try:
            expire_dt = datetime.datetime.strptime(str(not_after), "%b %d %H:%M:%S %Y %Z")
            now = datetime.datetime.now(datetime.UTC)
            if expire_dt.replace(tzinfo=datetime.UTC) < now:
                lines.append("  Status:           *** EXPIRED ***")
            else:
                days_left = (expire_dt.replace(tzinfo=datetime.UTC) - now).days
                lines.append(f"  Status:           Valid ({days_left} days remaining)")
        except ValueError:
            pass

        san_ext = cert.get("subjectAltName", ())
        if isinstance(san_ext, (list, tuple)):
            show_san = san_ext[:10]
            sans = [
                f"{tag}={value}"
                for entry in show_san
                if isinstance(entry, (list, tuple)) and len(entry) == 2
                for tag, value in [(entry[0], entry[1])]
                if isinstance(tag, str) and isinstance(value, str)
            ]
            if sans:
                lines.append(f"  SAN:              {', '.join(sans)}")
                if len(san_ext) > 10:
                    lines.append(f"                    ... and {len(san_ext) - 10} more")

        lines.append(f"  TLS Version:      {version}")
        if cipher:
            lines.append(f"  Cipher:           {cipher[0]} ({cipher[1]} bits)")

        return Result(success=True, data={"result": "\n".join(lines)})

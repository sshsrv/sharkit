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

        lines: list[str] = [f"SSL Certificate for {host}:{port}:"]
        lines.append("")

        # Subject
        subject = dict(x[0] for x in cert.get("subject", ()))
        subject_str = ", ".join(f"{k}={v}" for k, v in subject.items())
        lines.append(f"  Subject:          {subject_str}")

        # Issuer
        issuer = dict(x[0] for x in cert.get("issuer", ()))
        issuer_str = ", ".join(f"{k}={v}" for k, v in issuer.items())
        lines.append(f"  Issuer:           {issuer_str}")

        # Serial number
        serial = cert.get("serialNumber", "?")
        lines.append(f"  Serial Number:    {serial}")

        # Validity
        not_before = cert.get("notBefore", "?")
        not_after = cert.get("notAfter", "?")
        lines.append(f"  Valid From:       {not_before}")
        lines.append(f"  Valid Until:      {not_after}")

        # Check expiry
        try:
            expire_dt = datetime.datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
            now = datetime.datetime.now(datetime.UTC)
            if expire_dt.replace(tzinfo=datetime.UTC) < now:
                lines.append("  Status:           *** EXPIRED ***")
            else:
                days_left = (expire_dt.replace(tzinfo=datetime.UTC) - now).days
                lines.append(f"  Status:           Valid ({days_left} days remaining)")
        except ValueError:
            pass

        # SAN
        san_ext = cert.get("subjectAltName", ())
        if san_ext:
            sans = [f"{tag}={value}" for tag, value in san_ext[:10]]
            lines.append(f"  SAN:              {', '.join(sans)}")
            if len(san_ext) > 10:
                lines.append(f"                    ... and {len(san_ext) - 10} more")

        # TLS version and cipher
        lines.append(f"  TLS Version:      {version}")
        if cipher:
            lines.append(f"  Cipher:           {cipher[0]} ({cipher[1]} bits)")

        return Result(success=True, data={"result": "\n".join(lines)})

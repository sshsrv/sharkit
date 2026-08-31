from __future__ import annotations

import socket

from sharkit.tools.base import (
    ExecutionContext,
    OptionDefinition,
    Result,
    Tool,
    ToolMetadata,
)

COMMON_SERVICES: dict[int, str] = {
    20: "FTP-Data",
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    111: "RPCBind",
    143: "IMAP",
    443: "HTTPS",
    445: "SMB",
    993: "IMAPS",
    995: "POP3S",
    3306: "MySQL",
    3389: "RDP",
    5432: "PostgreSQL",
    5900: "VNC",
    6379: "Redis",
    8080: "HTTP-Proxy",
    8443: "HTTPS-Proxy",
    9200: "Elasticsearch",
    27017: "MongoDB",
}


def _parse_ports(spec: str) -> list[int]:
    """Parse a port specification like '80,443,8000-8100'."""
    ports: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            start, end = int(start_s), int(end_s)
            if start > end:
                start, end = end, start
            if start < 1 or end > 65535:
                raise ValueError(f"Port range must be 1-65535, got {start}-{end}")
            ports.extend(range(start, end + 1))
        else:
            p = int(part)
            if p < 1 or p > 65535:
                raise ValueError(f"Port must be 1-65535, got {p}")
            ports.append(p)
    return sorted(set(ports))


class PortScannerTool(Tool):
    metadata = ToolMetadata(
        name="port_scanner",
        description="TCP port scanner with service detection",
        category="osint.recon.network",
        author="sharkit",
        version="0.1.0",
        safety="safe",
        color="#E74C3C",
    )

    def __init__(self) -> None:
        self._options: dict[str, OptionDefinition] = {
            "host": OptionDefinition(
                name="host",
                description="Target host (IP or hostname)",
                required=True,
            ),
            "ports": OptionDefinition(
                name="ports",
                description="Comma-separated ports or range (e.g. '80,443' or '1-1000')",
                required=False,
                default="80,443,22,21,25,53,8080",
            ),
            "timeout": OptionDefinition(
                name="timeout",
                description="Connection timeout in seconds",
                required=False,
                default="2",
            ),
        }

    def get_options(self) -> dict[str, OptionDefinition]:
        return self._options

    def execute(self, context: ExecutionContext) -> Result:
        host = context.options.get("host") or ""
        if not host:
            return Result(success=False, error="Option 'host' is required.")

        ports_spec = context.options.get("ports") or "80,443,22,21,25,53,8080"
        timeout_spec = context.options.get("timeout") or "2"

        try:
            timeout = float(timeout_spec)
        except ValueError:
            return Result(success=False, error="Timeout must be a number.")

        try:
            ports = _parse_ports(ports_spec)
        except ValueError as exc:
            return Result(success=False, error=f"Invalid port specification: {exc}")

        if not ports:
            return Result(success=False, error="No valid ports specified.")

        open_ports: list[dict[str, int | str]] = []
        for port in ports:
            try:
                sock = socket.create_connection((host, port), timeout=timeout)
                sock.close()
                service = COMMON_SERVICES.get(port, "unknown")
                open_ports.append({"port": port, "service": service})
            except (TimeoutError, OSError):
                continue

        if not open_ports:
            return Result(
                success=True,
                data={"result": f"No open ports found on {host}."},
            )

        lines: list[str] = [f"Open ports on {host}:"]
        for entry in open_ports:
            port = int(entry["port"])
            service = str(entry["service"])
            lines.append(f"  {port:<6} {service}")

        lines.append(f"\n{len(open_ports)} open port(s) found.")
        return Result(success=True, data={"result": "\n".join(lines)})

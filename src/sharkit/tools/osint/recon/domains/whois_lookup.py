from __future__ import annotations

import socket

from sharkit.tools.base import (
    ExecutionContext,
    OptionDefinition,
    Result,
    Tool,
    ToolMetadata,
)

WHOIS_SERVERS: dict[str, str] = {
    ".com": "whois.verisign-grs.com",
    ".net": "whois.verisign-grs.com",
    ".org": "whois.pir.org",
    ".info": "whois.afilias.net",
    ".io": "whois.nic.io",
    ".co": "whois.nic.co",
    ".me": "whois.nic.me",
    ".tv": "whois.nic.tv",
    ".cc": "whois.nic.cc",
    ".de": "whois.denic.de",
    ".uk": "whois.nic.uk",
    ".fr": "whois.nic.fr",
    ".nl": "whois.sidn.nl",
    ".eu": "whois.eu",
    ".au": "whois.auda.org.au",
    ".ca": "whois.cira.ca",
    ".us": "whois.nic.us",
    ".ru": "whois.tcinet.ru",
    ".cn": "whois.cnnic.cn",
    ".jp": "whois.jprs.jp",
    ".in": "whois.inregistry.net",
}

ARIN_PREFIXES = ("192.168.", "10.", "172.16.", "172.17.", "172.18.",
                 "172.19.", "172.20.", "172.21.", "172.22.", "172.23.",
                 "172.24.", "172.25.", "172.26.", "172.27.", "172.28.",
                 "172.29.", "172.30.", "172.31.")


def _detect_whois_server(query: str) -> str:
    """Auto-detect the correct WHOIS server based on query type."""
    # IP address check
    parts = query.split(".")
    if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
        for prefix in ARIN_PREFIXES:
            if query.startswith(prefix):
                return "whois.arin.net"
        return "whois.arin.net"

    # Domain extension check
    for ext, server in WHOIS_SERVERS.items():
        if query.endswith(ext):
            return server

    # ASN check
    if query.upper().startswith("AS"):
        return "whois.radb.net"

    # Default fallback
    return "whois.iana.org"


def _query_whois(host: str, query: str, port: int = 43) -> str:
    """Send a WHOIS query and return the raw response text."""
    sock = socket.create_connection((host, port), timeout=10)
    try:
        sock.sendall((query + "\r\n").encode("utf-8"))
        response_parts: list[bytes] = []
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response_parts.append(chunk)
        return b"".join(response_parts).decode("utf-8", errors="replace")
    finally:
        sock.close()


class WhoisLookupTool(Tool):
    metadata = ToolMetadata(
        name="whois_lookup",
        description="WHOIS lookup for domains, IPs, and ASNs",
        category="osint.recon.network",
        author="sharkit",
        version="0.1.0",
        safety="safe",
        color="#9B59B6",
    )

    def __init__(self) -> None:
        self._options: dict[str, OptionDefinition] = {
            "query": OptionDefinition(
                name="query",
                description="Domain, IP, or ASN to look up",
                required=True,
            ),
            "server": OptionDefinition(
                name="server",
                description="WHOIS server (auto-detect if empty)",
                required=False,
                default="",
            ),
        }

    def get_options(self) -> dict[str, OptionDefinition]:
        return self._options

    def execute(self, context: ExecutionContext) -> Result:
        query = context.options.get("query") or ""
        if not query:
            return Result(success=False, error="Option 'query' is required.")

        server = context.options.get("server") or ""
        if not server:
            server = _detect_whois_server(query)

        try:
            response = _query_whois(server, query)
        except Exception as exc:
            return Result(
                success=False,
                error=f"WHOIS query to {server} failed: {exc}",
            )

        if not response.strip():
            return Result(
                success=True,
                data={"result": f"No WHOIS data found for '{query}'."},
            )

        lines: list[str] = [
            f"WHOIS Lookup: {query}",
            f"Server: {server}",
            "",
            response.strip(),
        ]

        return Result(success=True, data={"result": "\n".join(lines)})

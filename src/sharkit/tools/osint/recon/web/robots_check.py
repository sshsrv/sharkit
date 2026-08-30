from __future__ import annotations

from sharkit.network.client import HttpClient
from sharkit.tools.base import (
    ExecutionContext,
    OptionDefinition,
    Result,
    Tool,
    ToolMetadata,
)

INTERESTING_PATHS = (
    "admin", "login", "api", "config", "backup",
    "debug", "test", "secret", "private",
)


class RobotsCheckTool(Tool):
    metadata = ToolMetadata(
        name="robots_check",
        description="Fetch and analyze robots.txt from a target website",
        category="osint.recon.web",
        author="sharkit",
        version="0.1.0",
        safety="safe",
        color="#3498DB",
    )

    def __init__(self) -> None:
        self._options: dict[str, OptionDefinition] = {
            "url": OptionDefinition(
                name="url",
                description="Target URL (e.g. https://example.com)",
                required=True,
            ),
        }

    def get_options(self) -> dict[str, OptionDefinition]:
        return self._options

    def execute(self, context: ExecutionContext) -> Result:
        url = (context.options.get("url") or "").strip()
        if not url:
            return Result(success=False, error="Option 'url' is required.")

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        if not url.endswith("/robots.txt"):
            url = url.rstrip("/") + "/robots.txt"

        with HttpClient() as client:
            try:
                resp = client.get(url, timeout=20)
            except Exception as exc:
                return Result(success=False, error=f"Request failed: {exc}")

        if resp.status_code == 404:
            return Result(
                success=True,
                data={"result": f"robots.txt not found at {url} (HTTP 404)."},
            )

        if resp.status_code != 200:
            return Result(
                success=False,
                error=f"HTTP {resp.status_code} fetching {url}",
            )

        try:
            content = resp.content.decode("utf-8", errors="replace")
        except Exception:
            return Result(success=False, error="Failed to decode response.")

        lines = content.splitlines()

        user_agents: list[str] = []
        rules: dict[str, list[str]] = {}
        sitemaps: list[str] = []
        current_agent = "*"
        interesting: list[str] = []

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            if stripped.lower().startswith("user-agent:"):
                agent = stripped.split(":", 1)[1].strip()
                current_agent = agent
                if agent not in user_agents:
                    user_agents.append(agent)
                if agent not in rules:
                    rules[agent] = []

            elif stripped.lower().startswith("disallow:"):
                path = stripped.split(":", 1)[1].strip()
                rule = f"Disallow: {path}" if path else "Disallow: / (everything)"
                rules.setdefault(current_agent, []).append(rule)
                if path:
                    for kw in INTERESTING_PATHS:
                        if kw in path.lower():
                            interesting.append(path)
                            break

            elif stripped.lower().startswith("allow:"):
                path = stripped.split(":", 1)[1].strip()
                rules.setdefault(current_agent, []).append(f"Allow: {path}")

            elif stripped.lower().startswith("sitemap:"):
                sm = stripped.split(":", 1)[1].strip()
                sitemaps.append(sm)

        out: list[str] = []
        out.append(f"=== robots.txt Analysis: {url} ===")
        out.append(f"User-agents targeted: {len(user_agents)} ({', '.join(user_agents)})")
        out.append(f"Total rules: {sum(len(r) for r in rules.values())}")
        out.append(f"Sitemaps found: {len(sitemaps)}")
        out.append("")

        for agent, agent_rules in rules.items():
            out.append(f"[{agent}]")
            for rule in agent_rules:
                out.append(f"  {rule}")
            out.append("")

        if sitemaps:
            out.append("Sitemaps:")
            for sm in sitemaps:
                out.append(f"  {sm}")
            out.append("")

        if interesting:
            out.append(f"Interesting paths found: {len(interesting)}")
            for p in interesting:
                out.append(f"  ! {p}")

        return Result(success=True, data={"result": "\n".join(out)})

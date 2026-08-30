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

API_URL = "http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,mobile,proxy,hosting"

DISPLAY_FIELDS = [
    ("Country", "country"),
    ("Country Code", "countryCode"),
    ("Region", "regionName"),
    ("Region Code", "region"),
    ("City", "city"),
    ("Zip Code", "zip"),
    ("Latitude", "lat"),
    ("Longitude", "lon"),
    ("Timezone", "timezone"),
    ("ISP", "isp"),
    ("Organization", "org"),
    ("AS", "as"),
    ("Mobile", "mobile"),
    ("Proxy", "proxy"),
    ("Hosting", "hosting"),
]


class IpGeolocateTool(Tool):
    metadata = ToolMetadata(
        name="ip_geolocate",
        description="IP address geolocation via ip-api.com",
        category="osint.recon.network",
        author="sharkit",
        version="0.1.0",
        safety="safe",
        color="#FF6B35",
    )

    def __init__(self) -> None:
        self._options = {
            "ip": OptionDefinition(
                name="ip",
                description="Target IP address to geolocate",
                required=True,
            ),
        }

    def get_options(self) -> dict[str, OptionDefinition]:
        return self._options

    def execute(self, context: ExecutionContext) -> Result:
        ip = context.options.get("ip") or ""
        if not ip:
            return Result(success=False, error="Option 'ip' is required.")

        url = API_URL.format(ip=ip)
        try:
            with HttpClient() as client:
                response = client.get(url)
        except Exception as exc:
            return Result(success=False, error=f"Request failed: {exc}")

        try:
            data = json.loads(response.content)
        except json.JSONDecodeError:
            return Result(success=False, error="Invalid JSON response from API.")

        if data.get("status") != "success":
            message = data.get("message", "Unknown error")
            return Result(success=False, error=f"API error: {message}")

        lines = [f"  IP Geolocation Results for {ip}", "  " + "-" * 40]
        for label, key in DISPLAY_FIELDS:
            value = data.get(key, "N/A")
            if isinstance(value, bool):
                value = "Yes" if value else "No"
            lines.append(f"  {label:<16} : {value}")

        return Result(success=True, data={"result": "\n".join(lines)})

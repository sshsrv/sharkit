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

MYLNIKOV_API = "https://api.mylnikov.org/geolocation/wifi"


class MylnikovTool(Tool):
    metadata = ToolMetadata(
        name="mylnikov",
        description="Geolocate a WiFi access point by BSSID via the Mylnikov open dataset",
        category="osint.recon.network",
        author="sharkit",
        version="0.1.0",
        safety="safe",
        color="#9B59B6",
    )

    def __init__(self) -> None:
        self._options: dict[str, OptionDefinition] = {
            "bssid": OptionDefinition(
                name="bssid",
                description="WiFi BSSID/MAC address (e.g. AA:BB:CC:DD:EE:FF)",
                required=True,
            ),
        }

    def get_options(self) -> dict[str, OptionDefinition]:
        return self._options

    def execute(self, context: ExecutionContext) -> Result:
        bssid = context.options.get("bssid") or ""
        if not bssid:
            return Result(success=False, error="Option 'bssid' is required.")

        url = f"{MYLNIKOV_API}?bssid={bssid}&format=json"

        with HttpClient() as client:
            try:
                resp = client.get(url, timeout=30)
            except Exception as exc:
                return Result(success=False, error=f"Request failed: {exc}")

        try:
            data = json.loads(resp.content)
        except Exception:
            return Result(
                success=False,
                error=f"Failed to parse response (status {resp.status_code})",
            )

        if data.get("result") != 0:
            msg = data.get("message", "Unknown error")
            return Result(success=False, error=f"API error: {msg}")

        wifi_data = data.get("data", {})
        lat = wifi_data.get("lat", "?")
        lon = wifi_data.get("lon", "?")
        wifi_range = wifi_data.get("range", "?")
        age = wifi_data.get("age", "?")

        lines: list[str] = []
        lines.append(f"WiFi geolocation for BSSID {bssid}:")
        lines.append(f"  Latitude: {lat}")
        lines.append(f"  Longitude: {lon}")
        lines.append(f"  Range: {wifi_range}m")
        lines.append(f"  Age: {age}s")

        result_text = "\n".join(lines)
        return Result(success=True, data={"result": result_text})

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

MEMPOOL_API = "https://mempool.space/api/address"


class MempoolTool(Tool):
    metadata = ToolMetadata(
        name="mempool",
        description="Look up Bitcoin address balance and transaction stats via mempool.space",
        category="osint.util.crypto",
        author="sharkit",
        version="0.1.0",
        safety="safe",
        color="#F7931A",
    )

    def __init__(self) -> None:
        self._options: dict[str, OptionDefinition] = {
            "address": OptionDefinition(
                name="address",
                description="Bitcoin address to look up",
                required=True,
            ),
        }

    def get_options(self) -> dict[str, OptionDefinition]:
        return self._options

    def execute(self, context: ExecutionContext) -> Result:
        address = context.options.get("address") or ""
        if not address:
            return Result(success=False, error="Option 'address' is required.")

        url = f"{MEMPOOL_API}/{address}"
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

        chain = data.get("chain_stats", {})
        mempool = data.get("mempool_stats", {})

        balance_sats = chain.get("balance", 0)
        funded_sum_sats = chain.get("funded_txo_sum", 0)
        spent_sum_sats = chain.get("spent_txo_sum", 0)
        tx_count = chain.get("tx_count", 0)
        funded_count = chain.get("funded_txo_count", 0)
        spent_count = chain.get("spent_txo_count", 0)
        mempool_tx_count = mempool.get("tx_count", 0)

        def sats_to_btc(sats: int) -> str:
            return f"{sats / 100_000_000:.8f}"

        lines: list[str] = [
            f"Bitcoin address: {address}",
            f"  Confirmed balance: {sats_to_btc(balance_sats)} BTC ({balance_sats} sats)",
            f"  Funded transactions: {funded_count}",
            f"  Spent transactions: {spent_count}",
            f"  Total received: {sats_to_btc(funded_sum_sats)} BTC",
            f"  Total sent: {sats_to_btc(spent_sum_sats)} BTC",
            f"  Transactions: {tx_count}",
            f"  Mempool transactions: {mempool_tx_count}",
        ]
        result_text = "\n".join(lines)
        return Result(success=True, data={"result": result_text})

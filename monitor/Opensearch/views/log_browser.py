"""
View 8 — Log Browser

Search and browse recent logs with level-based filtering.
Consolidated from opensearch.py's log search logic.
"""

import datetime
from rich.panel import Panel
from rich.table import Table
from rich import box
from monitor.config import console, LOG_COLORS
from monitor.client import search_logs
from monitor.utils import timeframe_to_minutes


def display_log_browser(timeframe: str = "1h", query_str: str = "*", level: str = None):
    """Render the Log Browser view."""
    now = datetime.datetime.now().strftime("%H:%M")
    minutes = timeframe_to_minutes(timeframe)

    console.print()
    console.rule(f"[bold cyan]OpenSearch — Log Browser[/bold cyan] [dim]({timeframe} window, as of {now})[/dim]")
    console.print()

    hits = search_logs(query_str=query_str, minutes=minutes, size=30, level=level)

    if not hits:
        console.print(Panel(
            f"  No logs found matching [bold cyan]'{query_str}'[/bold cyan] in the last {timeframe}.\n"
            "  Check your query string or timeframe.",
            title="[bold]Logs[/bold]",
            title_align="left",
            border_style="yellow",
            expand=False,
        ))
        return

    table = Table(box=box.SIMPLE, expand=True, show_header=True, header_style="bold cyan")
    table.add_column("Timestamp", style="dim", width=20)
    table.add_column("Level", width=12)
    table.add_column("Host", style="bold green", width=20)
    table.add_column("Message")

    for h in hits:
        src = h["_source"]
        
        # Determine Level (log.level -> status -> info default)
        raw_lvl = src.get("log", {}).get("level")
        if not raw_lvl:
            # Fallback for metrics/telemetry data which might use 'status'
            status = src.get("status")
            if status == "active": raw_lvl = "info"
            elif status == "failed": raw_lvl = "error"
            else: raw_lvl = "info"
        lvl = raw_lvl.lower()
        col = LOG_COLORS.get(lvl, "white")
        
        ts = src.get("@timestamp", "")[:19].replace("T", " ")
        
        # Determine Host (hostname -> node_id -> —)
        host = src.get("hostname") or src.get("node_id", "—")
        
        # Determine Message (message -> event.original -> constructed string)
        msg = src.get("message")
        if not msg:
            if "event" in src and "original" in src["event"]:
                 # Some beats put the raw JSON in event.original
                 msg = src["event"]["original"]
            else:
                 # Construct message from known metrics if available
                 parts = []
                 if "cpu_util_percent" in src: parts.append(f"CPU: {src['cpu_util_percent']}%")
                 if "mem_util_percent" in src: parts.append(f"Mem: {src['mem_util_percent']}%")
                 msg = ", ".join(parts) if parts else ""

        table.add_row(
            ts,
            f"[{col}]{lvl.upper()}[/{col}]",
            host,
            msg[:200]
        )

    console.print(table)
    console.print(f"\n[dim]Showing 30 most recent hits for query: [bold cyan]{query_str}[/bold cyan][/dim]")

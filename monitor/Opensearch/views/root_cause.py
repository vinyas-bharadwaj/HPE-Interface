"""
View 9 — Root Cause Analysis (RCA)

Diagnostic view that takes a timestamp and correlates log patterns.
Consolidated from opensearch.py's spike root cause logic.
"""

import datetime
from rich.panel import Panel
from rich.table import Table
from rich import box
from monitor.config import console, LOG_COLORS, ROOT_CAUSE_PATTERNS
from monitor.client import fetch_logs_for_spike


def display_root_cause_analysis(spike_ts: str = None, window_min: int = 5):
    """Render the Root Cause Analysis view."""
    now = datetime.datetime.now().strftime("%H:%M")

    console.print()
    console.rule(f"[bold red]OpenSearch — Root Cause Analysis[/bold red] [dim](as of {now})[/dim]")
    console.print()

    if not spike_ts:
        console.print(Panel(
            "  Please provide a spike timestamp to begin analysis.\n"
            "  Use [bold yellow]--spike-ts ISO-TIMESTAMP[/bold yellow] in the CLI.",
            title="[bold yellow]RCA Required[/bold yellow]",
            title_align="left",
            border_style="yellow",
            expand=False,
        ))
        return

    try:
        spike_dt = datetime.datetime.fromisoformat(spike_ts.replace("Z", ""))
        start = (spike_dt - datetime.timedelta(minutes=window_min)).strftime("%Y-%m-%dT%H:%M:%SZ")
        end = (spike_dt + datetime.timedelta(minutes=window_min)).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception as e:
        console.print(f"[red]Error parsing timestamp:[/red] {e}")
        return

    hits = fetch_logs_for_spike(start, end)

    if not hits:
        console.print(Panel(
            f"  No logs found in the {window_min}m window around {spike_ts}.\n"
            "  Verify connectivity and indexing state.",
            title="[bold red]Analysis Results[/bold red]",
            title_align="left",
            border_style="red",
            expand=False,
        ))
        return

    annotated = []
    seen = set()
    for h in hits:
        src = h["_source"]
        
        # Determine Message (message -> event.original -> fallback)
        msg = src.get("message")
        if not msg:
            if "event" in src and "original" in src["event"]:
                 # Extract standard JSON string if available
                 msg = src["event"]["original"]
            
            # Fallback failed? Try explicit metric fields construction
            # This handles cases where event.original might be missing or non-string
            if not msg:
                 parts = []
                 if "cpu_util_percent" in src: parts.append(f"CPU: {src['cpu_util_percent']}%")
                 if "mem_util_percent" in src: parts.append(f"Mem: {src['mem_util_percent']}%")
                 msg = ", ".join(parts) if parts else ""
            
            # Final fallback to empty string to prevent NoneType errors
            if not msg:
                msg = ""

        # Ensure msg is a string before hashing/slicing
        msg = str(msg)

        if msg[:120] in seen:
            continue
        seen.add(msg[:120])
        
        # Run pattern matching against constructed message
        reason = next(
            (label for kw, label in ROOT_CAUSE_PATTERNS if kw.lower() in msg.lower()),
            None
        )

        # Determine Host and Level
        host = src.get("hostname") or src.get("node_id", "—")
        
        raw_lvl = src.get("log", {}).get("level")
        if not raw_lvl:
            status = src.get("status")
            if status == "active": raw_lvl = "info"
            elif status == "failed": raw_lvl = "error"
            else: raw_lvl = "info"
        level = raw_lvl.lower()

        annotated.append({
            "ts": src.get("@timestamp", "")[:19].replace("T", " "),
            "host": host,
            "level": level,
            "msg": msg[:220],
            "reason": reason
        })

    annotated.sort(key=lambda x: (x["reason"] is None, x["ts"]))

    table = Table(box=box.SIMPLE, expand=True, show_header=True, header_style="bold red")
    table.add_column("Timestamp", style="dim", width=20)
    table.add_column("Level", width=10)
    table.add_column("Host", style="bold green", width=15)
    table.add_column("Diagnostic / Message")

    for a in annotated:
        col = LOG_COLORS.get(a["level"], "white")
        
        # Ensure message is a string
        safe_msg = str(a["msg"])
        
        msg_display = f"{a['reason']}\n[dim]{safe_msg}[/dim]" if a["reason"] else safe_msg
        
        table.add_row(
            a["ts"],
            f"[{col}]{a['level'].upper()}[/{col}]",
            a["host"],
            msg_display
        )

    console.print(table)
    console.print(f"\n[dim]Analyzed 100 hits around {spike_ts}. Found {len([a for a in annotated if a['reason']])} potential indicators.[/dim]")

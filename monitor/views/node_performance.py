"""
View 4 — Node Performance

Per-node table showing CPU, memory, and disk usage with
green/yellow/red status indicators and a plain English summary.
"""

from rich.panel import Panel
from rich.table import Table
from rich import box

from monitor.config import (
    console,
    CPU_WARN, CPU_CRIT,
    HEAP_WARN, HEAP_CRIT,
    DISK_WARN, DISK_CRIT,
)
from monitor.client import fetch_node_stats, fetch_disk_allocation
from monitor.utils import format_bytes, parse_size_string, status_symbol, status_color


def display_node_performance():
    """Render the Node Performance view."""
    console.print()
    console.rule("[bold cyan]OpenSearch — Node Performance[/bold cyan]")
    console.print()

    node_stats = fetch_node_stats()
    disk_alloc = fetch_disk_allocation()

    if not node_stats or "nodes" not in node_stats:
        console.print("[red]Could not retrieve node stats.[/red]")
        return

    # Build a disk lookup by node name
    disk_by_node = {}
    if disk_alloc:
        for entry in disk_alloc:
            node_name = entry.get("node", "unknown")
            disk_by_node[node_name] = {
                "used": parse_size_string(entry.get("disk.used", "0")),
                "total": parse_size_string(entry.get("disk.total", "0")),
            }

    # ── Build Table ───────────────────────────────────────────
    table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        expand=True,
    )
    table.add_column("Node", style="bold white", ratio=1)
    table.add_column("CPU", width=10, justify="right")
    table.add_column("", width=3, justify="center")  # CPU status
    table.add_column("JVM Heap", width=22, justify="right")
    table.add_column("", width=3, justify="center")  # Heap status
    table.add_column("System RAM", width=22, justify="right")
    table.add_column("Disk", width=22, justify="right")
    table.add_column("", width=3, justify="center")  # Disk status

    issues = []

    for node_id, node in node_stats["nodes"].items():
        os_info = node.get("os", {})
        node_name = node.get("name", node_id[:8])

        # CPU
        cpu_pct = os_info.get("cpu", {}).get("percent", 0)
        cpu_col = status_color(cpu_pct, CPU_WARN, CPU_CRIT)
        cpu_sym = status_symbol(cpu_pct, CPU_WARN, CPU_CRIT)
        cpu_str = f"[{cpu_col}]{cpu_pct}%[/{cpu_col}]"

        # JVM Heap (the important memory metric for OpenSearch)
        jvm_info = node.get("jvm", {}).get("mem", {})
        heap_used = jvm_info.get("heap_used_in_bytes", 0)
        heap_max = jvm_info.get("heap_max_in_bytes", 0)
        heap_pct = (heap_used / heap_max * 100) if heap_max > 0 else 0
        heap_col = status_color(heap_pct, HEAP_WARN, HEAP_CRIT)
        heap_sym = status_symbol(heap_pct, HEAP_WARN, HEAP_CRIT)
        heap_str = f"[{heap_col}]{format_bytes(heap_used)} / {format_bytes(heap_max)}[/{heap_col}]"

        # System RAM (informational only — high usage is normal for OpenSearch)
        mem_info = os_info.get("mem", {})
        mem_used = mem_info.get("used_in_bytes", 0)
        mem_total = mem_info.get("total_in_bytes", 0)
        mem_str = f"[dim]{format_bytes(mem_used)} / {format_bytes(mem_total)}[/dim]"

        # Disk
        disk_info = disk_by_node.get(node_name, {})
        disk_used = disk_info.get("used", 0)
        disk_total = disk_info.get("total", 0)
        disk_pct = (disk_used / disk_total * 100) if disk_total > 0 else 0
        disk_col = status_color(disk_pct, DISK_WARN, DISK_CRIT)
        disk_sym = status_symbol(disk_pct, DISK_WARN, DISK_CRIT)
        disk_str = f"[{disk_col}]{format_bytes(disk_used)} / {format_bytes(disk_total)}[/{disk_col}]"

        table.add_row(node_name, cpu_str, cpu_sym, heap_str, heap_sym, mem_str, disk_str, disk_sym)

        # Collect issues for summary
        if cpu_pct >= CPU_CRIT:
            issues.append(f"[red]✗[/red]  {node_name} — critically high CPU ({cpu_pct}%)")
        elif cpu_pct >= CPU_WARN:
            issues.append(f"[yellow]⚠[/yellow]  {node_name} — elevated CPU ({cpu_pct}%)")

        if heap_pct >= HEAP_CRIT:
            issues.append(f"[red]✗[/red]  {node_name} — JVM Heap at {heap_pct:.0f}% — risk of OutOfMemory error")
        elif heap_pct >= HEAP_WARN:
            issues.append(f"[yellow]⚠[/yellow]  {node_name} — JVM Heap at {heap_pct:.0f}% — consider increasing heap or reducing load")

        if disk_pct >= DISK_CRIT:
            issues.append(f"[red]✗[/red]  {node_name} — critically full disk ({disk_pct:.0f}%)")
        elif disk_pct >= DISK_WARN:
            issues.append(f"[yellow]⚠[/yellow]  {node_name} — disk getting full ({disk_pct:.0f}%)")

    console.print(table)
    console.print()

    # ── Summary ───────────────────────────────────────────────
    if issues:
        for issue in issues:
            console.print(f"  {issue}")
    else:
        console.print("  [green]✓  All nodes healthy — no performance concerns detected.[/green]")

    console.print()

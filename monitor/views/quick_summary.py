"""
View 1 — Quick Summary

The most important view: a 10-second health check for admins.
Shows cluster health, resource averages, index activity, and shard status
with plain English warnings.
"""

import datetime

from rich.panel import Panel
from rich.table import Table
from rich import box

from monitor.config import console, CPU_WARN, CPU_CRIT, HEAP_WARN, HEAP_CRIT, DISK_WARN, DISK_CRIT
from monitor.client import fetch_cluster_health, fetch_node_stats, fetch_disk_allocation, fetch_indices, fetch_shards
from monitor.utils import format_bytes, parse_size_string, status_symbol, cluster_status_symbol, cluster_status_styled


def display_quick_summary():
    """Render the Quick Summary view."""
    now = datetime.datetime.now().strftime("%H:%M")

    console.print()
    console.rule(f"[bold cyan]OpenSearch — Quick Summary[/bold cyan]  [dim](as of {now})[/dim]")
    console.print()

    warnings = []

    # ── Cluster Health ────────────────────────────────────────
    health = fetch_cluster_health()
    if health:
        status = health.get("status", "unknown")
        num_nodes = health.get("number_of_nodes", 0)
        sym = cluster_status_symbol(status)

        console.print(Panel(
            f"  Status  : {cluster_status_styled(status)} {sym}\n"
            f"  Nodes   : {num_nodes} active",
            title="[bold]Cluster Health[/bold]",
            title_align="left",
            border_style="cyan",
            expand=False,
        ))

        if status.lower() == "yellow":
            warnings.append("[yellow]⚠[/yellow]  Cluster is YELLOW — some replica shards are missing. Data is accessible but redundancy is reduced.")
        elif status.lower() == "red":
            warnings.append("[red]✗[/red]  Cluster is RED — some primary shards are unassigned. Data may be unavailable.")
    else:
        console.print("[red]Could not retrieve cluster health.[/red]")

    # ── Resources (avg across nodes) ──────────────────────────
    node_stats = fetch_node_stats()
    disk_alloc = fetch_disk_allocation()

    cpu_values = []
    mem_used_total = 0
    mem_total_total = 0
    heap_used_total = 0
    heap_max_total = 0
    node_cpu_details = []
    node_mem_details = []
    node_heap_details = []

    if node_stats and "nodes" in node_stats:
        for node_id, node in node_stats["nodes"].items():
            os_info = node.get("os", {})
            node_name = node.get("name", node_id[:8])

            # CPU
            cpu_pct = os_info.get("cpu", {}).get("percent", 0)
            cpu_values.append(cpu_pct)
            node_cpu_details.append((node_name, cpu_pct))

            # System RAM
            mem_info = os_info.get("mem", {})
            mem_used = mem_info.get("used_in_bytes", 0)
            mem_total = mem_info.get("total_in_bytes", 0)
            mem_used_total += mem_used
            mem_total_total += mem_total

            if mem_total > 0:
                mem_pct = (mem_used / mem_total) * 100
                node_mem_details.append((node_name, mem_pct))

            # JVM Heap
            jvm_info = node.get("jvm", {}).get("mem", {})
            heap_used = jvm_info.get("heap_used_in_bytes", 0)
            heap_max = jvm_info.get("heap_max_in_bytes", 0)
            heap_used_total += heap_used
            heap_max_total += heap_max

            if heap_max > 0:
                heap_pct = (heap_used / heap_max) * 100
                node_heap_details.append((node_name, heap_pct))

    disk_used_total = 0
    disk_total_total = 0
    node_disk_details = []

    if disk_alloc:
        for entry in disk_alloc:
            disk_used_str = entry.get("disk.used", "0")
            disk_total_str = entry.get("disk.total", "0")
            node_name = entry.get("node", "unknown")

            disk_used = parse_size_string(disk_used_str)
            disk_total = parse_size_string(disk_total_str)
            disk_used_total += disk_used
            disk_total_total += disk_total

            if disk_total > 0:
                disk_pct = (disk_used / disk_total) * 100
                node_disk_details.append((node_name, disk_pct))

    avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0
    cpu_sym = status_symbol(avg_cpu, CPU_WARN, CPU_CRIT)
    heap_pct_total = (heap_used_total / heap_max_total * 100) if heap_max_total > 0 else 0
    heap_sym = status_symbol(heap_pct_total, HEAP_WARN, HEAP_CRIT)
    disk_sym = status_symbol((disk_used_total / disk_total_total * 100) if disk_total_total > 0 else 0, DISK_WARN, DISK_CRIT)

    resources_text = (
        f"  CPU        : {avg_cpu:.0f}%                       {cpu_sym}\n"
        f"  JVM Heap   : {format_bytes(heap_used_total)} / {format_bytes(heap_max_total)}   {heap_sym}\n"
        f"  System RAM : {format_bytes(mem_used_total)} / {format_bytes(mem_total_total)}   [dim](normal — OpenSearch uses OS RAM as cache)[/dim]\n"
        f"  Disk       : {format_bytes(disk_used_total)} / {format_bytes(disk_total_total)} {disk_sym}"
    )

    console.print(Panel(
        resources_text,
        title="[bold]Resources (avg across nodes)[/bold]",
        title_align="left",
        border_style="cyan",
        expand=False,
    ))

    # Generate resource warnings
    for node_name, cpu_pct in node_cpu_details:
        if cpu_pct >= CPU_CRIT:
            warnings.append(f"[red]✗[/red]  CPU is at {cpu_pct}% on {node_name} — critically high, investigate immediately.")
        elif cpu_pct >= CPU_WARN:
            warnings.append(f"[yellow]⚠[/yellow]  CPU is at {cpu_pct}% on {node_name} — consider checking running tasks.")

    for node_name, heap_pct in node_heap_details:
        if heap_pct >= HEAP_CRIT:
            warnings.append(f"[red]✗[/red]  JVM Heap is at {heap_pct:.0f}% on {node_name} — critically high, risk of OutOfMemory.")
        elif heap_pct >= HEAP_WARN:
            warnings.append(f"[yellow]⚠[/yellow]  JVM Heap is at {heap_pct:.0f}% on {node_name} — consider increasing heap or reducing load.")

    for node_name, disk_pct in node_disk_details:
        if disk_pct >= DISK_CRIT:
            warnings.append(f"[red]✗[/red]  Disk is at {disk_pct:.0f}% on {node_name} — critically full, free space urgently.")
        elif disk_pct >= DISK_WARN:
            warnings.append(f"[yellow]⚠[/yellow]  Disk is at {disk_pct:.0f}% on {node_name} — consider cleaning old indices soon.")

    # ── Index Activity ────────────────────────────────────────
    indices = fetch_indices()
    if indices:
        total_indices = len(indices)
        total_data = sum(parse_size_string(idx.get("store.size", "0")) for idx in indices)

        # Find largest index
        largest_name = indices[0].get("index", "—") if indices else "—"
        largest_size = format_bytes(parse_size_string(indices[0].get("store.size", "0"))) if indices else "—"

        console.print(Panel(
            f"  Total indices  : {total_indices}\n"
            f"  Total data     : {format_bytes(total_data)}\n"
            f"  Largest index  : {largest_name} ({largest_size})",
            title="[bold]Index Activity[/bold]",
            title_align="left",
            border_style="cyan",
            expand=False,
        ))
    else:
        console.print(Panel(
            "  No index data available.",
            title="[bold]Index Activity[/bold]",
            title_align="left",
            border_style="cyan",
            expand=False,
        ))

    # ── Shards ────────────────────────────────────────────────
    all_shards = fetch_shards()
    if all_shards:
        active_count = sum(1 for s in all_shards if s.get("state", "").upper() == "STARTED")
        unassigned_count = sum(1 for s in all_shards if s.get("state", "").upper() == "UNASSIGNED")
        relocating_count = sum(1 for s in all_shards if s.get("state", "").upper() == "RELOCATING")
        initializing_count = sum(1 for s in all_shards if s.get("state", "").upper() == "INITIALIZING")

        unassigned_sym = "[green]✓[/green]" if unassigned_count == 0 else "[red]✗[/red]"

        shard_text = f"  Active     : {active_count}\n"
        if relocating_count > 0:
            shard_text += f"  Relocating : {relocating_count}\n"
        if initializing_count > 0:
            shard_text += f"  Initializing: {initializing_count}\n"
        shard_text += f"  Unassigned : {unassigned_count}  {unassigned_sym}"

        console.print(Panel(
            shard_text,
            title="[bold]Shards[/bold]",
            title_align="left",
            border_style="cyan",
            expand=False,
        ))

        if unassigned_count > 0:
            warnings.append(f"[red]✗[/red]  {unassigned_count} unassigned shard(s) detected — data redundancy may be affected.")
    else:
        console.print(Panel(
            "  No shard data available.",
            title="[bold]Shards[/bold]",
            title_align="left",
            border_style="cyan",
            expand=False,
        ))

    # ── Warnings Footer ──────────────────────────────────────
    if warnings:
        console.print()
        console.rule("[bold yellow]Alerts[/bold yellow]")
        for w in warnings:
            console.print(f"  {w}")
    else:
        console.print()
        console.print("  [green]✓  All systems healthy — no issues detected.[/green]")

    console.print()

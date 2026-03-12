"""
Menu navigation for the OpenSearch CLI Monitor.

Provides the main service menu and the OpenSearch submenu
with arrow-key selection (Vite-style) using simple-term-menu.
"""

import sys

from rich.panel import Panel
from simple_term_menu import TerminalMenu

from monitor.config import console
from monitor.views.quick_summary import display_quick_summary
from monitor.views.cluster_health import display_cluster_health
from monitor.views.index_deep_dive import display_index_deep_dive
from monitor.views.node_performance import display_node_performance
from monitor.views.shard_overview import display_shard_overview
from monitor.utils import press_enter_to_return


# ──────────────── Menu Style ───────────────────────────────────

MENU_CURSOR = "❯ "
MENU_CURSOR_STYLE = ("fg_cyan", "bold")
MENU_HIGHLIGHT_STYLE = ("fg_cyan", "bold")


# ──────────────── Main Service Menu ────────────────────────────

SERVICE_OPTIONS = [
    "OpenSearch",
    "Kafka          (coming soon)",
    "Logstash       (coming soon)",
    "All Services   (coming soon)",
    "Exit",
]


def main_service_menu(timeframe: str = "1h"):
    """Show the top-level service selector and loop until exit."""
    while True:
        console.clear()
        console.print()
        console.print(Panel.fit(
            "[bold cyan]Cluster Monitor[/bold cyan]\n"
            "[dim]Use arrow keys, press Enter to select[/dim]",
            border_style="cyan",
        ))
        console.print()

        menu = TerminalMenu(
            SERVICE_OPTIONS,
            menu_cursor=MENU_CURSOR,
            menu_cursor_style=MENU_CURSOR_STYLE,
            menu_highlight_style=MENU_HIGHLIGHT_STYLE,
        )
        choice = menu.show()

        if choice is None or choice == 4:  # Escape or Exit
            console.print("[bold green]Goodbye![/bold green]")
            sys.exit(0)
        elif choice == 0:
            opensearch_menu(timeframe=timeframe)
        elif choice in (1, 2, 3):
            console.print("\n[yellow]⚠  This service is coming soon.[/yellow]")
            press_enter_to_return()


# ──────────────── OpenSearch Submenu ───────────────────────────

OPENSEARCH_VIEWS = [
    ("Quick Summary", display_quick_summary),
    ("Cluster Health", display_cluster_health),
    ("Index Deep Dive", display_index_deep_dive),
    ("Node Performance", display_node_performance),
    ("Shard Overview", display_shard_overview),
]

OPENSEARCH_OPTIONS = [label for label, _ in OPENSEARCH_VIEWS] + ["Back to Main Menu"]


def opensearch_menu(timeframe: str = "1h"):
    """Show the OpenSearch monitoring submenu and loop until back."""
    while True:
        console.clear()
        console.print()
        console.print(Panel.fit(
            "[bold cyan]OpenSearch Monitor[/bold cyan]\n"
            f"[dim]Timeframe: {timeframe}[/dim]",
            border_style="cyan",
        ))
        console.print()

        menu = TerminalMenu(
            OPENSEARCH_OPTIONS,
            menu_cursor=MENU_CURSOR,
            menu_cursor_style=MENU_CURSOR_STYLE,
            menu_highlight_style=MENU_HIGHLIGHT_STYLE,
        )
        choice = menu.show()

        if choice is None or choice == len(OPENSEARCH_VIEWS):  # Escape or Back
            return

        _, view_fn = OPENSEARCH_VIEWS[choice]
        console.clear()
        try:
            view_fn()
        except Exception as e:
            console.print(f"\n[red]Error:[/red] {e}")

        press_enter_to_return()

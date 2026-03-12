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
    "---",
    "Kafka          (coming soon)",
    "Logstash       (coming soon)",
    "All Services   (coming soon)",
    "---",
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

        if choice is None or choice == 6:  # Escape or Exit
            console.print("[bold green]Goodbye![/bold green]")
            sys.exit(0)
        elif choice == 0:
            opensearch_menu(timeframe=timeframe)
        elif choice in (2, 3, 4):
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

TIMEFRAME_OPTIONS = ["1h", "6h", "24h", "7d"]


def _pick_timeframe(current: str) -> str:
    """Show an inline timeframe picker and return the chosen value (or current on cancel)."""
    console.clear()
    console.print()
    console.print(Panel.fit(
        f"[bold cyan]Change Timeframe[/bold cyan]\n"
        f"[dim]Current: {current}  —  Use arrow keys, Enter to confirm[/dim]",
        border_style="cyan",
    ))
    console.print()

    options = TIMEFRAME_OPTIONS + ["Cancel"]
    menu = TerminalMenu(
        options,
        menu_cursor=MENU_CURSOR,
        menu_cursor_style=MENU_CURSOR_STYLE,
        menu_highlight_style=MENU_HIGHLIGHT_STYLE,
    )
    choice = menu.show()

    if choice is None or choice == len(TIMEFRAME_OPTIONS):
        return current
    return TIMEFRAME_OPTIONS[choice]


def opensearch_menu(timeframe: str = "1h"):
    """Show the OpenSearch monitoring submenu and loop until back."""
    while True:
        console.clear()
        console.print()
        console.print(Panel.fit(
            "[bold cyan]OpenSearch Monitor[/bold cyan]\n"
            f"[dim]Timeframe: {timeframe}  —  Use arrow keys, Enter to select[/dim]",
            border_style="cyan",
        ))
        console.print()

        # Rebuild each loop so the timeframe label stays current
        view_labels = [label for label, _ in OPENSEARCH_VIEWS]
        menu_options = view_labels + [
            "---",
            f"Change Timeframe   (now: {timeframe})",
            "---",
            "Back to Main Menu",
        ]

        menu = TerminalMenu(
            menu_options,
            menu_cursor=MENU_CURSOR,
            menu_cursor_style=MENU_CURSOR_STYLE,
            menu_highlight_style=MENU_HIGHLIGHT_STYLE,
        )
        choice = menu.show()

        # Escape or "Back to Main Menu" (last item)
        if choice is None or choice == len(menu_options) - 1:
            return

        # Separator — do nothing
        if menu_options[choice] == "---":
            continue

        # Change Timeframe
        if choice == len(view_labels) + 1:  # index after first "---"
            timeframe = _pick_timeframe(timeframe)
            continue

        # View selection
        if choice < len(OPENSEARCH_VIEWS):
            _, view_fn = OPENSEARCH_VIEWS[choice]
            console.clear()
            try:
                view_fn()
            except Exception as e:
                console.print(f"\n[red]Error:[/red] {e}")
            press_enter_to_return()

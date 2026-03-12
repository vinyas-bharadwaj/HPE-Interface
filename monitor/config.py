"""
Configuration constants for the OpenSearch CLI Monitor.

Edit these values to match your OpenSearch cluster setup.
"""

from rich.console import Console

# ─────────────────────────── CONFIG ────────────────────────────
OPENSEARCH_HOST = "localhost"
OPENSEARCH_PORT = 9200
OPENSEARCH_USER = "admin"
OPENSEARCH_PASS = "8905"
OPENSEARCH_SSL = True
# ───────────────────────────────────────────────────────────────

# ─────────────────────── THRESHOLDS ────────────────────────────
# CPU thresholds (percentage)
CPU_WARN = 70
CPU_CRIT = 90

# JVM Heap thresholds (percentage)
HEAP_WARN = 75
HEAP_CRIT = 90

# System RAM thresholds (percentage)
MEM_WARN = 85
MEM_CRIT = 95

# Disk thresholds (percentage)
DISK_WARN = 80
DISK_CRIT = 90
# ───────────────────────────────────────────────────────────────

# Shared console instance
console = Console()

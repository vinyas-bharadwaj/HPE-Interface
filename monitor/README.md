# OpenSearch CLI Monitor

A terminal-based monitoring tool for semi-technical admins to monitor an OpenSearch cluster. Presents information in plain English with clear visual status indicators — no raw engineering data.

## Requirements

- Python 3.11 or 3.12
- A running OpenSearch cluster

## Setup

```bash
cd /path/to/HPE-Interface
pip install -r requirements.txt
```

## Usage

### Interactive Mode (default)
```bash
python -m monitor
```
Launches the main service menu → select OpenSearch → navigate the 5 views.

### Quick Summary (skip the menu)
```bash
python -m monitor --summary
```

### Watch Mode (auto-refresh)
```bash
python -m monitor --summary --watch 10
```
Refreshes Quick Summary every 10 seconds. Press `Ctrl+C` to stop.

### All Flags
| Flag          | Values                      | Default      | Description                                  |
|---------------|-----------------------------|--------------|----------------------------------------------|
| `--timeframe` | `1h`, `6h`, `24h`, `7d`    | `1h`         | Time window for time-windowed views           |
| `--watch`     | integer (seconds)           | off          | Auto-refresh interval                         |
| `--summary`   | flag                        | off          | Jump straight to Quick Summary                |
| `--service`   | `opensearch`, `kafka`, `logstash` | `opensearch` | Service to monitor (kafka/logstash coming soon) |

## Views

1. **Quick Summary** — 10-second health check: cluster status, resource averages, index activity, shard status
2. **Cluster Health** — Detailed cluster status with plain English explanations
3. **Index Deep Dive** — All indices sorted by size, drill into shard layouts
4. **Node Performance** — Per-node CPU, memory, disk with status indicators
5. **Shard Overview** — All shards grouped by state, unassigned highlighted

## Configuration

Edit `monitor/config.py` to change connection settings:

```python
OPENSEARCH_HOST = "localhost"
OPENSEARCH_PORT = 9200
OPENSEARCH_USER = "admin"
OPENSEARCH_PASS = "admin"
OPENSEARCH_SSL  = False
```

## Project Structure

```
monitor/
├── __init__.py          # Package init
├── __main__.py          # python -m monitor entry
├── cli.py               # Click CLI with flags
├── config.py            # Connection config + thresholds
├── client.py            # OpenSearch API data fetchers
├── utils.py             # Formatting + status symbols
├── menus.py             # Service menu + OpenSearch submenu
└── views/
    ├── __init__.py
    ├── quick_summary.py
    ├── cluster_health.py
    ├── index_deep_dive.py
    ├── node_performance.py
    └── shard_overview.py
```

# OpenSearch Monitor — Demo Commands

This guide lists the commands tailored for your environment (Index: `hpc-telemetry-*`) to showcase the new monitoring features during a demo.

## 1. Main Dashboard
Start with the standard interactive menu to show the overview.
```bash
python3 -m monitor
```
*   **Demo Path**: Arrow down to **Quick Summary** to show cluster health.

---

## 2. Default Log Browser
Show recent logs from the telemetry data (last 1 hour).
```bash
python3 -m monitor --query "*" --service opensearch
```
*   **What to show**: It now correctly parses `node_id` and displays raw JSON telemetry data.

---

## 3. Filtering Logs (Interactive)
Show how to filter logs by specific criteria using the Log Browser.

**Show only High CPU Usage (> 30%)**:
```bash
python3 -m monitor --query "cpu_util_percent:>30" --timeframe 30d
```

**Show specific nodes**:
```bash
python3 -m monitor --query "node_id:hpe-debian-node-01" --timeframe 30d
```

**Watch Mode (Live)**:
Simulate a live "tail" of the logs refreshing every 3 seconds.
```bash
python3 -m monitor --query "*" --watch 3
```

---

## 4. Root Cause Analysis (RCA)
Demonstrate the diagnostic engine using a timestamp from your existing data.

**Scenario**: "Let's investigate the activity around 5:05 PM on March 22nd."
```bash
python3 -m monitor --spike-ts "2026-03-22T17:05:30"
```
*   **Explanation**: "This scans a 10-minute window around the event. Since our system was healthy, it shows raw telemetry. If there were errors (like OOM or Disk Full), they would be highlighted red here."

---

## 5. Historical Trends
Show usage over the last month to prove data retention.
```bash
python3 -m monitor --timeframe 30d
```
*   **Action**: Select **Historical Trends** from the menu.
*   **Result**: Shows ASCII charts for CPU/Heap usage over the last 30 days.

---

## 6. Full "Power User" Command
A complex command to show off CLI capabilities:
```bash
python3 -m monitor --service opensearch --query "mem_util_percent:[20 TO 80]" --timeframe 24h --level info
```

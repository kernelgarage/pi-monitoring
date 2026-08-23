# Architecture

```
                 ┌───────────────┐
 vcgencmd/sysfs →│rpi_exporter.sh│ (runs on host, via systemd)
                 └──────┬────────┘
                        │ writes /tmp/rpi_metrics.prom
                        ▼
┌──────────────┐  scrapes  ┌────────────┐  queries  ┌─────────┐
│ node-exporter│──────────▶│ prometheus │──────────▶│ grafana │
└──────────────┘           └────────────┘           └────┬────┘
                                                            │
┌──────────────┐  ships    ┌────────────┐        queries   │
│   promtail   │──────────▶│    loki    │◀─────────────────┤
└──────────────┘           └────────────┘                  │
 (container logs                                            │
  via Docker socket)       ┌────────────┐        queries   │
                            │   tempo    │◀─────────────────┘
                            └────────────┘
```

All services join a single Docker network (`monitoring`) and bind their host ports only to `127.0.0.1` — the stack is not exposed externally by design. Reaching it remotely requires an SSH tunnel or a reverse proxy set up separately.

## Services

| Service | Role | Data retention |
|---|---|---|
| `node-exporter` | Host metrics (CPU, memory, disk, network) + Pi hardware metrics via textfile collector | n/a (scraped live) |
| `prometheus` | Metrics storage/query | 90d |
| `grafana` | Dashboards, unified query UI | n/a (state, not data) |
| `loki` | Log storage/query | 30d |
| `promtail` | Discovers every container via the Docker socket and ships stdout/stderr to Loki | n/a |
| `tempo` | Trace storage, OTLP receiver on `4317` (gRPC) / `4318` (HTTP) | 240h (10d) |

`rpi_exporter.sh` is **not** a container — it runs directly on the host, polling `vcgencmd` and sysfs every 10s and writing Prometheus text-exposition format to `/tmp/rpi_metrics.prom`, which `node-exporter` picks up read-only.

The fan-speed lookup has a hardcoded `hwmon2` path for Pi 5, with a glob fallback for other hwmon numbering — fan hwmon index isn't stable across Pi models/kernel versions, so check `/sys/class/hwmon/*/fan1_input` if fan RPM reads as 0 on your hardware.

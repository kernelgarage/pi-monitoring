# pi-monitoring

A Docker Compose observability stack for a Raspberry Pi: metrics (Prometheus), logs (Loki), and traces (Tempo), unified in Grafana — plus a host-side script that exports Pi hardware metrics (CPU temp, throttling, clock speed, voltage, fan RPM), and [`agent-monitor`](agent-monitor/) for watching a local LLM (queue depth, tokens) instead of just the hardware underneath it.

## Prerequisites

- A Linux host with Docker + Docker Compose (a Raspberry Pi, for the hardware metrics — other metrics work on any host).
- `vcgencmd` available on the host (ships with Raspberry Pi OS).

## Run it

```bash
docker compose up -d
```

Grafana is at `http://<host>:3000` (default login `admin`/`admin`, prompted to change on first login). All ports bind to `127.0.0.1` only.

### Enable Pi hardware metrics

`rpi_exporter.sh` runs on the host, not in a container. Supervise it with systemd so it survives reboots:

```ini
# /etc/systemd/system/rpi-exporter.service
[Unit]
Description=Raspberry Pi hardware metrics exporter
After=network.target

[Service]
ExecStart=/path/to/exporter/rpi_exporter.sh
Restart=always
User=<your-user>

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now rpi-exporter
```

### Agent-level monitoring

[`agent-monitor/`](agent-monitor/) is a small queue that sits in front of a local LLM (built
against Ollama) — it's already wired into this compose file and scraped by Prometheus. See its
own README for what it tracks and why.

## Docs

- [Architecture](docs/architecture.md)
- [Known limitations](docs/known-limitations.md)
- [Extending the stack](docs/extending.md)

## License

[MIT](LICENSE)

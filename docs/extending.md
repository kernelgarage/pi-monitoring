# Extending the stack

- **Dashboards.** Drop new dashboard JSON into `grafana/provisioning/dashboards/json/` — it's auto-provisioned (see `grafana/provisioning/dashboards/dashboards.yml`), no restart needed (30s poll interval).
- **Scraping another app.** Add a `job_name` under `scrape_configs` in `prometheus/prometheus.yaml` pointing at its Docker service name (if it's on the `monitoring` network) or host:port. See [`agent-monitor`](../agent-monitor/) for a worked example — an LLM-serving queue exposing its own `/metrics`.
- **Sending traces.** Point an app's OTLP exporter at `tempo:4317` (gRPC) or `tempo:4318` (HTTP) over the `monitoring` network.
- **Data directories.** `./data/` is gitignored — it's runtime state (Prometheus/Loki/Tempo storage, Grafana DB/plugins), not source. Subdirectories under it need to stay world-writable (`chmod 777`) since Loki/Tempo/Grafana run as non-root container users whose uid varies by image.

# EquiMind Backend Monitoring Guide

## Overview

The backend exposes Prometheus metrics and integrates with Grafana for comprehensive monitoring and observability.

## Quick Start

### 1. Start Backend

```bash
python main.py
```

### 2. Start Monitoring Stack

**Windows:**
```bash
start-monitoring.bat
```

**PowerShell:**
```powershell
.\start-monitoring.ps1
```

**Manual:**
```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

### 3. Access Dashboards

- **Backend Metrics**: http://localhost:8000/metrics
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001
  - Username: `admin`
  - Password: `admin`

## Available Metrics

### Event Metrics

**equimind_events_total**
- Type: Counter
- Labels: severity, decision, attack_category
- Description: Total number of security events processed

Example queries:
```promql
# Total events
sum(equimind_events_total)

# Events by severity
sum by (severity) (equimind_events_total)

# Block rate
rate(equimind_events_total{decision="BLOCK"}[5m])
```

**equimind_risk_score**
- Type: Histogram
- Buckets: 0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100
- Description: Distribution of risk scores

Example queries:
```promql
# Average risk score
histogram_quantile(0.5, equimind_risk_score_bucket)

# 95th percentile risk score
histogram_quantile(0.95, equimind_risk_score_bucket)
```

### Performance Metrics

**equimind_ml_prediction_seconds**
- Type: Histogram
- Description: Time spent on ML predictions

Example queries:
```promql
# Average prediction time
rate(equimind_ml_prediction_seconds_sum[5m]) / rate(equimind_ml_prediction_seconds_count[5m])

# 99th percentile prediction time
histogram_quantile(0.99, equimind_ml_prediction_seconds_bucket)
```

**equimind_ml_predictions_total**
- Type: Counter
- Labels: model_version
- Description: Total ML model predictions

Example queries:
```promql
# Predictions per second
rate(equimind_ml_predictions_total[1m])

# Total predictions
sum(equimind_ml_predictions_total)
```

### System Metrics

**equimind_websocket_connections**
- Type: Gauge
- Description: Number of active WebSocket connections

Example queries:
```promql
# Current connections
equimind_websocket_connections

# Max connections in last hour
max_over_time(equimind_websocket_connections[1h])
```

**equimind_entity_risk_score**
- Type: Gauge
- Labels: entity_id, entity_name
- Description: Current risk score per entity

Example queries:
```promql
# Top 5 risky entities
topk(5, equimind_entity_risk_score)

# Average entity risk
avg(equimind_entity_risk_score)
```

**equimind_blocked_events_total**
- Type: Counter
- Labels: reason
- Description: Total blocked events

Example queries:
```promql
# Block rate
rate(equimind_blocked_events_total[5m])

# Blocks by reason
sum by (reason) (equimind_blocked_events_total)
```

## Grafana Dashboard

### Import Dashboard

1. Access Grafana at http://localhost:3001
2. Login with admin/admin
3. Go to Dashboards → Import
4. Upload `grafana-dashboard.json`
5. Select Prometheus data source

### Dashboard Panels

**System Overview:**
- Total events processed
- Current tension level
- Active WebSocket connections
- ML prediction rate

**Risk Analysis:**
- Risk score distribution
- Events by severity
- Top risky entities
- Block/Challenge/Allow rates

**Performance:**
- ML prediction latency
- API response times
- Request rate
- Error rate

**Security Events:**
- Events timeline
- Attack categories
- Decision distribution
- Incident tracking

## Alerting

### Prometheus Alert Rules

Create `alerts.yml`:

```yaml
groups:
  - name: equimind_alerts
    interval: 30s
    rules:
      - alert: HighRiskScore
        expr: avg(equimind_entity_risk_score) > 70
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High average risk score detected"
          description: "Average entity risk score is {{ $value }}"

      - alert: HighBlockRate
        expr: rate(equimind_events_total{decision="BLOCK"}[5m]) > 0.5
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High block rate detected"
          description: "Block rate is {{ $value }} events/sec"

      - alert: SlowMLPredictions
        expr: histogram_quantile(0.95, equimind_ml_prediction_seconds_bucket) > 1.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "ML predictions are slow"
          description: "95th percentile prediction time is {{ $value }}s"

      - alert: NoWebSocketConnections
        expr: equimind_websocket_connections == 0
        for: 10m
        labels:
          severity: info
        annotations:
          summary: "No active WebSocket connections"
          description: "No clients connected for 10 minutes"
```

Add to `prometheus.yml`:
```yaml
rule_files:
  - "alerts.yml"
```

### Grafana Alerts

1. Go to Alerting → Alert rules
2. Create new alert rule
3. Set query and threshold
4. Configure notification channels (email, Slack, etc.)

## Monitoring Best Practices

### 1. Set Baseline Metrics

Monitor for 24-48 hours to establish baselines:
- Normal event rate
- Typical risk scores
- Average prediction latency
- Expected block rate

### 2. Configure Alerts

Set alerts based on baselines:
- Risk score > baseline + 2σ
- Block rate > baseline + 3σ
- Prediction latency > 500ms (p95)
- Zero connections for > 15 minutes

### 3. Regular Review

- Daily: Check dashboard for anomalies
- Weekly: Review alert history
- Monthly: Analyze trends and adjust thresholds

### 4. Capacity Planning

Monitor:
- Request rate trends
- Memory usage
- CPU utilization
- Disk I/O

## Troubleshooting

### Metrics Not Showing

**Check backend is running:**
```bash
curl http://localhost:8000/metrics
```

**Check Prometheus target:**
1. Go to http://localhost:9090/targets
2. Verify `equimind-backend` is UP
3. Check for scrape errors

**Check Docker containers:**
```bash
docker-compose -f docker-compose.monitoring.yml ps
```

### Grafana Dashboard Empty

**Verify data source:**
1. Go to Configuration → Data sources
2. Check Prometheus connection
3. Test & Save

**Check time range:**
- Ensure time range includes recent data
- Try "Last 15 minutes"

**Verify queries:**
- Go to Explore
- Run sample query: `equimind_events_total`

### High Memory Usage

**Check Prometheus retention:**
```yaml
# In docker-compose.monitoring.yml
command:
  - '--storage.tsdb.retention.time=7d'  # Reduce from default 15d
```

**Check Grafana cache:**
```bash
docker exec equimind-grafana grafana-cli admin reset-admin-password admin
```

## Advanced Configuration

### Custom Metrics

Add custom metrics in `monitoring.py`:

```python
from prometheus_client import Counter, Gauge, Histogram

# Custom counter
custom_metric = Counter(
    'equimind_custom_total',
    'Description of custom metric',
    ['label1', 'label2']
)

# Use in code
custom_metric.labels(label1='value1', label2='value2').inc()
```

### External Prometheus

If using external Prometheus instead of Docker:

1. Download from https://prometheus.io/download/
2. Copy `prometheus.yml` to Prometheus directory
3. Update target to `localhost:8000`
4. Run: `prometheus --config.file=prometheus.yml`

### Grafana Provisioning

Auto-provision dashboards by adding to `docker-compose.monitoring.yml`:

```yaml
grafana:
  volumes:
    - ./grafana-dashboards:/etc/grafana/provisioning/dashboards
    - ./grafana-dashboard.json:/var/lib/grafana/dashboards/equimind.json
```

## Metrics Retention

**Prometheus:**
- Default: 15 days
- Configure: `--storage.tsdb.retention.time=30d`

**Grafana:**
- Stores dashboard configs only
- Data comes from Prometheus

## Export Metrics

### Prometheus Data

```bash
# Query API
curl 'http://localhost:9090/api/v1/query?query=equimind_events_total'

# Export snapshot
curl -X POST http://localhost:9090/api/v1/admin/tsdb/snapshot
```

### Grafana Dashboard

1. Go to Dashboard settings
2. Click "JSON Model"
3. Copy JSON
4. Save to file

## Integration with External Systems

### Splunk

Use Prometheus remote write:
```yaml
remote_write:
  - url: "https://splunk.example.com/api/v1/write"
```

### Datadog

Use Datadog agent with Prometheus integration:
```yaml
instances:
  - prometheus_url: http://localhost:8000/metrics
```

### ELK Stack

Use Metricbeat with Prometheus module:
```yaml
metricbeat.modules:
  - module: prometheus
    hosts: ["localhost:8000"]
```

---

**For more information, see:**
- Prometheus docs: https://prometheus.io/docs/
- Grafana docs: https://grafana.com/docs/
- Backend API docs: http://localhost:8000/docs

# Zero Trust Risk Engine - Frontend & Preprocessing Guide

## Overview

The Zero Trust Risk Engine now includes:

1. **Web Frontend** (`frontend.html`) - User-friendly interface for analyzing network flows
2. **Preprocessing Layer** (`preprocess.py`) - Automatically derives complex features from basic user input
3. **Enhanced API** (updated `main.py`) - Accepts both simplified and full feature vectors

## Features

### What Gets Derived Automatically

The preprocessing layer takes just **11 primary inputs** from the user and derives **35+ derived features**:

#### Primary User Inputs (Required)
- **Protocol**: TCP, UDP, ICMP
- **Service**: HTTP, HTTPS, SSH, FTP, SMTP, DNS, etc.
- **Connection State**: SF, SYN, FIN, RST, etc.
- **Traffic Category**: Normal, Exploits, DoS, etc.
- **Source/Destination Bytes**: Data transferred in each direction
- **Source/Destination Packets**: Number of packets
- **Duration**: Connection duration in seconds
- **Packet Loss**: Lost packets (source/destination)

#### Automatically Derived Features

**Robust Features (byte-based):**
- TCP buffer estimates
- Response body length (service-aware)
- Packet loss metrics

**Standard Features (packet-based):**
- Window sizes (based on packets and loss)
- Data mean per packet
- Connection tuple counts
- Transaction depth
- Protocol-specific counts (FTP, HTTP)

**Flow Features (timing-based):**
- Traffic rate (bytes/second)
- Source/destination load
- Inter-packet times
- Jitter estimates
- RTT, SYN-ACK, and ACK timing
- Service-aware parameter estimation

**Binary Features:**
- FTP login detection
- Suspicious port pair detection

## Usage

### Option 1: Web Frontend (Recommended for Users)

1. **Start the server:**
   ```bash
   cd risk_engine
   uvicorn app.main:app --reload
   ```

2. **Open in browser:**
   ```
   http://localhost:8000
   ```

3. **Fill in basic network flow information** and click "Analyze Flow"

4. **View results:**
   - Risk score (0-100)
   - Risk level (LOW, MEDIUM, HIGH, CRITICAL)
   - All automatically derived features

### Option 2: API with Full Features (For Automation)

If you already have all features extracted:

```python
import requests

# Full feature vector
flow_data = {
    "proto": "tcp",
    "service": "http",
    "state": "FIN",
    "attack_cat": "Exploits",
    
    # Robust features
    "sbytes": 800,
    "dbytes": 600,
    "stcpb": 20000,
    "dtcpb": 18000,
    "response_body_len": 400,
    "sloss": 0,
    "dloss": 0,
    
    # Standard features (all required)
    "spkts": 6,
    "dpkts": 5,
    "swin": 255,
    "dwin": 255,
    "dmean": 150,
    "ct_src_dport_ltm": 1,
    "ct_dst_sport_ltm": 1,
    "trans_depth": 0,
    "ct_ftp_cmd": 0,
    "ct_flw_http_mthd": 1,
    
    # Binary features
    "is_ftp_login": 0,
    "is_sm_ips_ports": 0,
    
    # Flow features
    "dur": 0.8,
    "rate": 200,
    "sload": 900,
    "dload": 700,
    "sinpkt": 0.15,
    "dinpkt": 0.18,
    "sjit": 0.01,
    "djit": 0.02,
    "tcprtt": 0.03,
    "synack": 0.01,
    "ackdat": 0.02
}

response = requests.post("http://localhost:8000/predict", json=flow_data)
print(response.json())
```

### Option 3: API with Simplified Input (Auto-Derive)

Pass just the basic parameters:

```python
import requests

# Simplified input - features are automatically derived
flow_data = {
    "protocol": "tcp",
    "service": "http",
    "state": "SF",
    "attack_cat": "Normal",
    "src_bytes": 800,
    "dst_bytes": 600,
    "src_packets": 6,
    "dst_packets": 5,
    "duration": 0.8,
    "src_loss": 0,
    "dst_loss": 0,
    "src_port": 55123,  # optional
    "dst_port": 80      # optional
}

response = requests.post("http://localhost:8000/predict", json=flow_data)
print(response.json())
```

## API Response Format

```json
{
    "mlp_score": 0.35,
    "risk_score": [35, "LOW"],
    "derived_features": {
        "dur": 0.8,
        "rate": 2333.33,
        "sload": 1000.0,
        "dload": 750.0,
        "sinpkt": 0.133,
        "dinpkt": 0.16,
        ...
    }
}
```

## Architecture

### Data Flow

```
User Input (Primary Features)
    ↓
[preprocess_user_input()]  ← Feature derivation
    ↓
Complete Feature Vector
    ↓
[preprocess()]  ← Encoding, scaling
    ↓
Model Input (Standardized)
    ↓
[predict_mlp()]  ← Neural network inference
    ↓
Risk Score → Risk Level
```

### Feature Derivation Logic

#### TCP Buffer Estimation
- Based on average packet size and total packet count
- Typical range: 1,000 - 1,000,000 bytes

#### Window Size Estimation
- Base calculation: `max(128, min(packets * 32, 255))`
- Reduced if packet loss detected (flow control)

#### Traffic Rate Calculation
- `rate = (src_bytes + dst_bytes) / duration`
- Load calculations: `sload = src_bytes / duration`

#### Jitter Estimation
- Base jitter: `0.001 + (1 / packets) * 0.01`
- Added variance from packet loss

#### RTT Estimation
- State-aware: SYN (0.05s), SF (0.02s), FIN (0.03s), etc.
- Protocol-aware: UDP uses 0.001s

#### Service-Specific Features
- **HTTP/HTTPS**: Response body = ~80% of dst_bytes, multiple connections
- **SSH**: Single connection, larger response overhead
- **FTP**: Control + data connection tracking
- **DNS**: Multiple queries expected

## Examples

### Example 1: Normal HTTP Traffic
```json
{
    "protocol": "tcp",
    "service": "http",
    "state": "SF",
    "attack_cat": "Normal",
    "src_bytes": 500,
    "dst_bytes": 2000,
    "src_packets": 5,
    "dst_packets": 4,
    "duration": 1.2,
    "src_loss": 0,
    "dst_loss": 0
}
```
**Expected Result**: LOW risk (25-35)

### Example 2: Potential DDoS Attack
```json
{
    "protocol": "tcp",
    "service": "http",
    "state": "SYN",
    "attack_cat": "DoS",
    "src_bytes": 8000,
    "dst_bytes": 2500,
    "src_packets": 800,
    "dst_packets": 205,
    "duration": 0.2,
    "src_loss": 5,
    "dst_loss": 3
}
```
**Expected Result**: CRITICAL risk (80+)

### Example 3: SSH Connection with Suspicious Activity
```json
{
    "protocol": "tcp",
    "service": "ssh",
    "state": "SYN",
    "attack_cat": "Reconnaissance",
    "src_bytes": 15000,
    "dst_bytes": 500,
    "src_packets": 200,
    "dst_packets": 5,
    "duration": 0.05,
    "src_loss": 10,
    "dst_loss": 8
}
```
**Expected Result**: MEDIUM-HIGH risk (60-75)

## Customization

### Adding New Service Types

Edit `app/preprocess.py`, add to `SERVICE_MAPPING`:

```python
SERVICE_MAPPING = {
    # ... existing services ...
    "my_service": "my_service"
}
```

Then customize derivation methods as needed.

### Adjusting Feature Scaling

Modify estimation methods in `FeatureDeriver` class:
- `_estimate_tcp_buffer()`
- `_estimate_window_size()`
- `_estimate_jitter()`
- etc.

## Performance Notes

- **Frontend load time**: < 1 second
- **Analysis time**: 0.1-0.5 seconds per flow
- **Preprocessing**: < 10ms
- **Model inference**: 50-200ms

## Troubleshooting

### CORS Errors in Browser
- Already handled by `CORSMiddleware` in updated `main.py`
- If issues persist, ensure server is running on `localhost:8000`

### Missing Features Error
- Ensure all primary fields are provided in the API request
- Check field names match the API documentation

### Model Error
- Ensure all model files exist in `./models/`
- Check TensorFlow/Keras versions compatibility

## Future Enhancements

1. **Batch processing** - Analyze multiple flows simultaneously
2. **Custom feature weights** - User-defined importance
3. **Explanation dashboard** - SHAP value visualization
4. **Model retraining** - Adapt to network baseline
5. **Export functionality** - CSV/JSON report generation

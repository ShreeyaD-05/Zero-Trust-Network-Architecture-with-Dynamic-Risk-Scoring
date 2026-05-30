# Zero Trust Risk Engine - Quick Start Guide

## 📋 What Was Created

### 1. **Preprocessing Layer** (`app/preprocess.py`)
- Automatically derives 35+ complex features from just 11 primary inputs
- Handles service-specific feature engineering
- Examples: window size estimation, jitter calculation, RTT estimation, load computation

### 2. **Web Frontend** (`app/frontend.html`)
- Beautiful, responsive UI for network flow analysis
- Real-time risk assessment with color-coded results
- Shows derived features for transparency
- Works on desktop and mobile

### 3. **Updated API** (`app/main.py`)
- Now accepts both:
  - **Simplified input** (primary features only)
  - **Full feature vectors** (all 45+ features)
- Automatically routes to preprocessing layer when needed
- Includes CORS support for frontend access
- Serves the HTML frontend at `http://localhost:8000`

### 4. **Documentation & Testing**
- `FRONTEND_USAGE.md` - Complete usage guide
- `test_risk_engine.py` - 7 realistic test cases
- Examples for HTTP, SSH, FTP, DDoS, Reconnaissance, etc.

## 🚀 Getting Started (2 Minutes)

### Step 1: Start the Server
```bash
cd d:\semester6\Project\zeroTrustMonitor\risk_engine
uvicorn app.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 2: Open the Frontend
Open your browser and go to:
```
http://localhost:8000
```

### Step 3: Analyze Your First Flow
1. Fill in basic information (protocol, service, bytes, packets, duration)
2. Click "Analyze Flow"
3. See instant risk assessment

## 📊 What Data is Required?

### Minimal Input (11 fields)
```python
{
    "protocol": "tcp",          # TCP, UDP, ICMP
    "service": "http",          # http, ssh, ftp, dns, etc.
    "state": "SF",              # SF, SYN, FIN, RST, etc.
    "attack_cat": "Normal",     # Normal, Exploits, DoS, etc.
    "src_bytes": 800,           # Bytes from source
    "dst_bytes": 600,           # Bytes to destination
    "src_packets": 6,           # Number of src packets
    "dst_packets": 5,           # Number of dst packets
    "duration": 0.8,            # Duration in seconds
    "src_loss": 0,              # Packet loss count (src)
    "dst_loss": 0               # Packet loss count (dst)
}
```

### Everything Else is Derived Automatically!

Examples of derived features:
- TCP buffer sizes
- Window sizes
- Data rates and loads
- Jitter and RTT
- Inter-packet times
- Service-specific features

## 💡 Use Cases

### Frontend UI
- **Non-technical users** analyzing network flows
- **Security analysts** doing real-time assessments
- **Network operations** quick risk checks
- **Training/education** understanding risk factors

### API (Programmatic)
- **SIEM integration** - Bulk flow analysis
- **Packet capture tools** - Real-time analysis
- **Network monitoring** - Continuous assessment
- **Threat hunting** - Suspicious traffic detection
- **Automation** - CI/CD security checks

## 🧪 Test It Out

### Quick Test via API
```python
import requests

flow = {
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
    "dst_loss": 0
}

response = requests.post("http://localhost:8000/predict", json=flow)
print(response.json())
```

### Run Full Test Suite
```bash
python test_risk_engine.py
```

This runs 7 realistic scenarios:
- ✓ Normal HTTP traffic
- ✓ DDoS attack
- ✓ SSH reconnaissance
- ✓ FTP connection
- ✓ Backdoor activity
- ✓ DNS query
- ✓ Full feature vector

## 📈 Understanding Risk Scores

| Score | Level | Interpretation |
|-------|-------|-----------------|
| 0-29  | LOW   | Normal traffic, minimal risk |
| 30-59 | MEDIUM| Suspicious patterns detected |
| 60-79 | HIGH  | Strong indicators of attack |
| 80-100| CRITICAL| Likely malicious activity |

## 🔧 Architecture

```
User Input (11 features)
         ↓
  [Preprocessing Layer]
         ↓
Derived Features (35+)
         ↓
    [Model Input]
         ↓
  [TensorFlow Model]
         ↓
   Risk Score
   Risk Level
```

## 📁 File Structure

```
risk_engine/
├── app/
│   ├── main.py                 # ✨ Updated API with preprocessing
│   ├── frontend.html           # ✨ Web UI
│   ├── preprocess.py           # ✨ Feature derivation layer
│   ├── inference.py            # Model inference
│   ├── risk_engine.py          # Risk computation
│   ├── utils.py                # Utilities
│   ├── Data-test.txt           # Example data
│   └── txt.txt
├── models/
│   ├── mlp_model.keras
│   ├── ae_model.keras
│   └── shap_background.npy
├── requirements.txt
├── FRONTEND_USAGE.md           # ✨ Detailed guide
├── test_risk_engine.py         # ✨ Test suite
└── README.md (this file)
```

## 🎯 Key Features

✅ **Zero Configuration** - Works out of the box
✅ **Automatic Feature Derivation** - No complex manual engineering needed
✅ **Beautiful UI** - Modern, responsive interface
✅ **Real-time Analysis** - Instant risk assessment
✅ **Flexible API** - Accept simplified or full input
✅ **Well Tested** - 7 realistic test scenarios
✅ **Scalable** - Can handle batch processing

## 🐛 Troubleshooting

### Issue: "Could not connect to API"
**Solution:** Make sure the server is running
```bash
uvicorn app.main:app --reload
```

### Issue: Frontend shows only input form, no results
**Solution:** Submit the form with at least one test case
- Use default values (already pre-filled)
- Click "Analyze Flow" button

### Issue: CORS errors in browser console
**Solution:** Already handled in updated `main.py`
- If persists, check that server is on `localhost:8000`
- Clear browser cache and refresh

### Issue: Model loading error
**Solution:** Verify model files exist in `./models/`
```
models/mlp_model.keras           ✓
models/ae_model.keras            ✓
models/shap_background.npy       ✓
```

## 📚 Next Steps

1. **Explore the UI** - Open `http://localhost:8000` and try different scenarios
2. **Read** `FRONTEND_USAGE.md` - Deep dive into feature derivation
3. **Run tests** - `python test_risk_engine.py` to see real examples
4. **Integrate** - Use the API in your SIEM/monitoring tools
5. **Customize** - Adjust feature derivation for your needs

## 💬 Support

For detailed API documentation, feature descriptions, and customization guide, see `FRONTEND_USAGE.md`.

---

**Ready to analyze?** → Go to `http://localhost:8000` 🚀

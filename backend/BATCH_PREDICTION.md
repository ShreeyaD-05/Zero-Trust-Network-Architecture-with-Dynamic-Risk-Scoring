# Batch Prediction API

## Overview

The batch prediction API allows you to process multiple network flow records at once by uploading files in various formats (JSON, CSV, Excel, Parquet). The system will analyze each record and return risk scores and labels.

---

## API Endpoint

**POST** `/predict/batch`

Upload a file containing network flow data for batch risk assessment.

### Supported File Types

- **JSON** (`.json`) - Single object or array of objects
- **CSV** (`.csv`) - Comma-separated values
- **Excel** (`.xlsx`, `.xls`) - Microsoft Excel spreadsheets
- **Parquet** (`.parquet`) - Apache Parquet columnar format

---

## Request Format

### Using cURL

```bash
curl -X POST http://localhost:8000/predict/batch \
  -F "file=@sample-data.json"
```

### Using Python

```python
import requests

with open('sample-data.json', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/predict/batch',
        files={'file': f}
    )
    
result = response.json()
print(f"Processed {result['total_records']} records")
```

### Using JavaScript/Fetch

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:8000/predict/batch', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log(`Processed ${result.total_records} records`);
```

---

## Input Data Schema

Each record must contain the following fields:

### Required Fields

```json
{
  "proto": "tcp",                    // Protocol: tcp, udp, icmp
  "service": "http",                 // Service: http, https, ssh, ftp, dns
  "state": "CON",                    // Connection state: CON, FIN, REQ, RST, SYN
  "attack_cat": "Normal",            // Attack category (for reference)
  "sbytes": 1200,                    // Source bytes
  "dbytes": 800,                     // Destination bytes
  "stcpb": 50000,                    // Source TCP base sequence number
  "dtcpb": 30000,                    // Destination TCP base sequence number
  "response_body_len": 200,          // HTTP response body length
  "sloss": 0,                        // Source packets retransmitted
  "dloss": 0,                        // Destination packets retransmitted
  "spkts": 12,                       // Source packets
  "dpkts": 8,                        // Destination packets
  "swin": 256,                       // Source TCP window size
  "dwin": 256,                       // Destination TCP window size
  "dmean": 100,                      // Mean packet size
  "ct_src_dport_ltm": 1,             // Connection count
  "ct_dst_sport_ltm": 1,             // Connection count
  "trans_depth": 1,                  // Transaction depth
  "ct_ftp_cmd": 0,                   // FTP command count
  "ct_flw_http_mthd": 1,             // HTTP method count
  "is_ftp_login": 0,                 // FTP login flag (0 or 1)
  "is_sm_ips_ports": 0,              // Same IPs/ports flag (0 or 1)
  "dur": 0.5,                        // Duration in seconds
  "rate": 2400,                      // Packet rate
  "sload": 2400,                     // Source load
  "dload": 1600,                     // Destination load
  "sinpkt": 0.04,                    // Source inter-packet time
  "dinpkt": 0.06,                    // Destination inter-packet time
  "sjit": 0.001,                     // Source jitter
  "djit": 0.001,                     // Destination jitter
  "tcprtt": 0.02,                    // TCP round-trip time
  "synack": 0.01,                    // SYN-ACK time
  "ackdat": 0.005                    // ACK-DATA time
}
```

---

## Response Format

```json
{
  "filename": "sample-data.json",
  "file_type": "json",
  "total_records": 3,
  "successful": 3,
  "failed": 0,
  "summary": {
    "avg_risk_score": 45.67,
    "max_risk_score": 85.0,
    "min_risk_score": 18.0,
    "risk_level_distribution": {
      "LOW": 1,
      "MEDIUM": 1,
      "CRITICAL": 1
    }
  },
  "results": [
    {
      "row_number": 1,
      "input_data": {
        "proto": "tcp",
        "service": "http",
        ...
      },
      "prediction": {
        "risk_score": 85,
        "risk_level": "CRITICAL",
        "attack_cat": "DoS Hulk",
        "confidence": 0.92,
        "is_attack": true,
        "mlp_score": 0.8500
      },
      "status": "success"
    },
    {
      "row_number": 2,
      "input_data": {...},
      "prediction": {
        "risk_score": 18,
        "risk_level": "LOW",
        "attack_cat": "Normal",
        "confidence": 0.88,
        "is_attack": false,
        "mlp_score": 0.1800
      },
      "status": "success"
    }
  ],
  "timestamp": "2026-03-01T10:30:00Z"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `filename` | string | Original filename |
| `file_type` | string | File extension (json, csv, xlsx, parquet) |
| `total_records` | integer | Total number of records processed |
| `successful` | integer | Number of successful predictions |
| `failed` | integer | Number of failed predictions |
| `summary.avg_risk_score` | float | Average risk score across all records |
| `summary.max_risk_score` | float | Highest risk score |
| `summary.min_risk_score` | float | Lowest risk score |
| `summary.risk_level_distribution` | object | Count of records by risk level |
| `results` | array | Detailed results for each record |

### Result Object

| Field | Type | Description |
|-------|------|-------------|
| `row_number` | integer | Row number in input file (1-indexed) |
| `input_data` | object | Original input record |
| `prediction.risk_score` | integer | Risk score (0-100) |
| `prediction.risk_level` | string | Risk level (LOW, MEDIUM, HIGH, CRITICAL) |
| `prediction.attack_cat` | string | Detected attack category |
| `prediction.confidence` | float | Model confidence (0-1) |
| `prediction.is_attack` | boolean | Whether classified as attack |
| `prediction.mlp_score` | float | Raw ML model score (0-1) |
| `status` | string | "success" or "error" |
| `error` | string | Error message (if status is "error") |

---

## File Format Examples

### JSON Format

**Single Record:**
```json
{
  "proto": "tcp",
  "service": "http",
  "sbytes": 1200,
  ...
}
```

**Multiple Records:**
```json
[
  {
    "proto": "tcp",
    "service": "http",
    ...
  },
  {
    "proto": "udp",
    "service": "dns",
    ...
  }
]
```

### CSV Format

```csv
proto,service,state,attack_cat,sbytes,dbytes,...
tcp,http,CON,Normal,1200,800,...
tcp,https,SYN,DoS,8000,2500,...
udp,dns,REQ,Probe,500,300,...
```

### Excel Format

Create an Excel file with:
- First row: Column headers (field names)
- Subsequent rows: Data records

### Parquet Format

Use pandas to create:
```python
import pandas as pd

data = [
    {"proto": "tcp", "service": "http", ...},
    {"proto": "udp", "service": "dns", ...}
]

df = pd.DataFrame(data)
df.to_parquet('data.parquet')
```

---

## Usage Examples

### Example 1: Process JSON File

```bash
curl -X POST http://localhost:8000/predict/batch \
  -F "file=@sample-data.json" \
  | jq '.summary'
```

**Output:**
```json
{
  "avg_risk_score": 45.67,
  "max_risk_score": 85.0,
  "min_risk_score": 18.0,
  "risk_level_distribution": {
    "LOW": 1,
    "MEDIUM": 1,
    "CRITICAL": 1
  }
}
```

### Example 2: Process CSV File

```bash
curl -X POST http://localhost:8000/predict/batch \
  -F "file=@network-flows.csv"
```

### Example 3: Process Excel File

```bash
curl -X POST http://localhost:8000/predict/batch \
  -F "file=@traffic-data.xlsx"
```

### Example 4: Python Script

```python
import requests
import json

# Upload file
with open('sample-data.json', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/predict/batch',
        files={'file': f}
    )

result = response.json()

# Print summary
print(f"Processed: {result['total_records']} records")
print(f"Success: {result['successful']}")
print(f"Failed: {result['failed']}")
print(f"Avg Risk: {result['summary']['avg_risk_score']}")

# Print high-risk records
for r in result['results']:
    if r['prediction'] and r['prediction']['risk_score'] >= 65:
        print(f"Row {r['row_number']}: Risk {r['prediction']['risk_score']} - {r['prediction']['risk_level']}")
```

---

## Error Handling

### Invalid File Type

```json
{
  "detail": "Unsupported file type: txt. Supported: json, csv, xlsx, xls, parquet"
}
```

### Empty File

```json
{
  "detail": "File contains no data"
}
```

### Invalid JSON

```json
{
  "detail": "Invalid JSON format: Expecting value: line 1 column 1 (char 0)"
}
```

### Processing Error

```json
{
  "detail": "Processing error: Missing required field 'proto'"
}
```

### Partial Failure

If some records fail, they're marked with `"status": "error"`:

```json
{
  "row_number": 5,
  "input_data": {...},
  "prediction": null,
  "status": "error",
  "error": "Missing required field 'sbytes'"
}
```

---

## Frontend Integration

### React Component Example

```jsx
import React, { useState } from 'react';

function BatchPrediction() {
  const [file, setFile] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/predict/batch', {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Batch Prediction</h2>
      
      <form onSubmit={handleSubmit}>
        <input 
          type="file" 
          accept=".json,.csv,.xlsx,.xls,.parquet"
          onChange={handleFileChange}
        />
        <button type="submit" disabled={!file || loading}>
          {loading ? 'Processing...' : 'Upload & Analyze'}
        </button>
      </form>

      {results && (
        <div>
          <h3>Results</h3>
          <p>Total Records: {results.total_records}</p>
          <p>Successful: {results.successful}</p>
          <p>Average Risk: {results.summary.avg_risk_score}</p>
          
          <table>
            <thead>
              <tr>
                <th>Row</th>
                <th>Risk Score</th>
                <th>Risk Level</th>
                <th>Attack Category</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {results.results.map(r => (
                <tr key={r.row_number}>
                  <td>{r.row_number}</td>
                  <td>{r.prediction?.risk_score || 'N/A'}</td>
                  <td>{r.prediction?.risk_level || 'N/A'}</td>
                  <td>{r.prediction?.attack_cat || 'N/A'}</td>
                  <td>{r.prediction?.confidence || 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default BatchPrediction;
```

---

## Performance

### Throughput

- **Small files** (<100 records): <1 second
- **Medium files** (100-1000 records): 1-5 seconds
- **Large files** (1000-10000 records): 5-30 seconds

### Limits

- **Max file size**: 10MB (configurable)
- **Max records**: 10,000 per file (recommended)
- **Timeout**: 60 seconds

### Optimization Tips

1. **Use Parquet** for large datasets (faster parsing)
2. **Batch processing** - split very large files
3. **Parallel requests** - process multiple files concurrently

---

## Testing

### Test with Sample Data

```bash
# Download sample data
curl -O http://localhost:8000/sample-data.json

# Test batch prediction
curl -X POST http://localhost:8000/predict/batch \
  -F "file=@sample-data.json"
```

### Create Test CSV

```bash
cat > test-data.csv << EOF
proto,service,state,attack_cat,sbytes,dbytes,stcpb,dtcpb,response_body_len,sloss,dloss,spkts,dpkts,swin,dwin,dmean,ct_src_dport_ltm,ct_dst_sport_ltm,trans_depth,ct_ftp_cmd,ct_flw_http_mthd,is_ftp_login,is_sm_ips_ports,dur,rate,sload,dload,sinpkt,dinpkt,sjit,djit,tcprtt,synack,ackdat
tcp,http,CON,Normal,1200,800,50000,30000,200,0,0,12,8,256,256,100,1,1,1,0,1,0,0,0.5,2400,2400,1600,0.04,0.06,0.001,0.001,0.02,0.01,0.005
tcp,https,SYN,DoS,8000,2500,500000,300000,800,5,3,80,25,128,128,50,5,3,1,0,1,0,0,0.2,10000,7000,2000,0.01,0.02,0.002,0.003,0.008,0.004,0.002
EOF

curl -X POST http://localhost:8000/predict/batch \
  -F "file=@test-data.csv"
```

---

## Summary

### Key Features

✓ Multiple file format support (JSON, CSV, Excel, Parquet)  
✓ Batch processing of multiple records  
✓ Detailed results with risk scores and labels  
✓ Summary statistics  
✓ Error handling for individual records  
✓ Easy frontend integration  

### API Endpoint

- **URL**: `POST /predict/batch`
- **Input**: File upload (multipart/form-data)
- **Output**: JSON with predictions and summary

### Supported Formats

- JSON (`.json`)
- CSV (`.csv`)
- Excel (`.xlsx`, `.xls`)
- Parquet (`.parquet`)

---

**Last Updated**: March 1, 2026  
**Status**: ✓ IMPLEMENTED - Batch prediction ready

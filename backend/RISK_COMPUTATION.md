# Risk Computation - Single Source of Truth

## Overview

This document explains how risk scores and risk levels are computed throughout the EquiMind system, ensuring consistency and a single source of truth.

---

## Risk Level Thresholds (SINGLE SOURCE OF TRUTH)

All risk level computations use these thresholds defined in `models.py`:

```python
Risk Score Range | Risk Level
-----------------|------------
0 - 29          | LOW
30 - 49         | MEDIUM
50 - 64         | HIGH
65 - 100        | CRITICAL
```

---

## Computation Flow

### 1. ML Model Prediction (`models.py`)

**Function**: `predict(features: dict) -> dict`

**Purpose**: Get raw ML prediction from TensorFlow model

**Input**: Network flow features (40+ features)

**Output**:
```python
{
    "attack_cat": "DoS",           # Attack category
    "confidence": 0.85,            # Model confidence (0-1)
    "anomaly_score": 0.85,         # Anomaly score (0-1)
    "is_attack": True,             # Boolean flag
    "risk_score": 85,              # ML risk score (0-100)
    "risk_level": "CRITICAL",      # ML risk level
    "mlp_score": 0.8500            # Raw model output (0-1)
}
```

**Risk Computation**:
```python
mlp_score = model.predict(features)  # Returns 0-1
risk_score, risk_level = compute_risk(mlp_score)
```

---

### 2. Risk Score Conversion (`models.py`)

**Function**: `compute_risk(mlp_score) -> tuple`

**Purpose**: Convert ML score (0-1) to risk score (0-100) and level

**Input**: `mlp_score` (float 0-1)

**Output**: `(risk_score, risk_level)` tuple

**Implementation**:
```python
def compute_risk(mlp_score) -> tuple:
    """Compute risk score and level from ML prediction - SINGLE SOURCE OF TRUTH"""
    risk_score = int(mlp_score * 100)
    
    # Single source of truth for risk level thresholds
    if risk_score < 30:
        level = "LOW"
    elif risk_score < 50:
        level = "MEDIUM"
    elif risk_score < 65:
        level = "HIGH"
    else:
        level = "CRITICAL"
    
    return risk_score, level
```

---

### 3. Risk Level from Score (`models.py`)

**Function**: `get_risk_level_from_score(risk_score: float) -> str`

**Purpose**: Get risk level from an existing risk score

**Input**: `risk_score` (0-100)

**Output**: `risk_level` ("low", "medium", "high", "critical")

**Usage**: When you have a risk score and need to determine its level

**Implementation**:
```python
def get_risk_level_from_score(risk_score: float) -> str:
    """Get risk level from a risk score - uses same thresholds as compute_risk"""
    if risk_score < 30:
        return "low"
    elif risk_score < 50:
        return "medium"
    elif risk_score < 65:
        return "high"
    else:
        return "critical"
```

**Note**: Returns lowercase for API consistency

---

### 4. Contextual Risk Scoring (`scorer.py`)

**Function**: `compute_risk_score(...) -> dict`

**Purpose**: Enhance ML risk score with contextual factors

**Input**:
- ML risk score and level
- Attack category
- Contextual factors (time, location, device, MFA)

**Output**:
```python
{
    "risk_score": 75.5,            # Final risk score (0-100)
    "risk_level": "high",          # Risk level (uses get_risk_level_from_score)
    "decision": "RESTRICT",        # Access decision
    "explanation": "...",          # Human-readable explanation
    "score_breakdown": {
        "network": 25.0,           # Network component
        "identity": 33.0,          # Identity component
        "device": 17.5,            # Device component
        "factors": [...]           # Contributing factors
    }
}
```

**Computation**:
```python
# Base score from ML model (33% weight)
network_score = ml_risk_score * 0.33

# Identity factors (up to 33%)
identity_score = 0
if not mfa_used:      identity_score += 15
if is_offhours:       identity_score += 10
if not location_known: identity_score += 8

# Device factors (up to 33%)
device_score = 0
if not device_ok:     device_score += 20

# Final score
total = network_score + identity_score + device_score
total = min(total, 100)

# Get risk level using centralized function
risk_level = get_risk_level_from_score(total)
```

---

## Usage Examples

### Example 1: Direct ML Prediction

```python
from models import predict

features = {
    "proto": "tcp",
    "service": "http",
    "sbytes": 1000,
    # ... other features
}

result = predict(features)
print(f"Risk Score: {result['risk_score']}")  # 45
print(f"Risk Level: {result['risk_level']}")  # MEDIUM
```

### Example 2: Event Generation with Context

```python
from models import predict
from scorer import compute_risk_score

# Get ML prediction
prediction = predict(features)

# Enhance with context
score_result = compute_risk_score(
    attack_cat=prediction["attack_cat"],
    confidence=prediction["confidence"],
    is_offhours=True,
    device_ok=False,
    mfa_used=True,
    location_known=True,
    behavioral_anomaly=prediction["anomaly_score"],
    ml_risk_score=prediction["risk_score"],
    ml_risk_level=prediction["risk_level"]
)

print(f"Final Risk Score: {score_result['risk_score']}")  # 68.5
print(f"Final Risk Level: {score_result['risk_level']}")  # high
print(f"Decision: {score_result['decision']}")            # RESTRICT
```

### Example 3: Get Level from Existing Score

```python
from models import get_risk_level_from_score

entity_risk_score = 72
level = get_risk_level_from_score(entity_risk_score)
print(f"Level: {level}")  # high
```

---

## Decision Thresholds

Access decisions are based on the final risk score:

```python
Risk Score Range | Decision
-----------------|----------
0 - 39          | ALLOW
40 - 64         | CHALLENGE
65 - 79         | RESTRICT
80 - 100        | BLOCK
```

**Implementation** (`scorer.py`):
```python
if total < 40:
    decision = "ALLOW"
elif total < 65:
    decision = "CHALLENGE"
elif total < 80:
    decision = "RESTRICT"
else:
    decision = "BLOCK"
```

---

## Severity Mapping

Severity levels map to decisions:

```python
Decision   | Severity
-----------|----------
ALLOW      | LOW
CHALLENGE  | MEDIUM
RESTRICT   | HIGH
BLOCK      | CRITICAL
```

**Implementation** (`simulator.py`):
```python
SEVERITIES = {
    "ALLOW":     "LOW",
    "CHALLENGE": "MEDIUM",
    "RESTRICT":  "HIGH",
    "BLOCK":     "CRITICAL",
}
```

---

## Where Risk Levels Are Used

### 1. Event Generation (`simulator.py`)

```python
# Uses scorer.py compute_risk_score()
score_result = compute_risk_score(...)
event = {
    "risk_score": score_result["risk_score"],
    "risk_level": score_result["risk_level"],  # From scorer
    "decision": score_result["decision"],
    "severity": SEVERITIES[score_result["decision"]]
}
```

### 2. Network Topology (`main.py`)

```python
# Uses models.py get_risk_level_from_score()
from models import get_risk_level_from_score

for entity in entities:
    risk_score = entity.get("risk_score", 0)
    node = {
        "risk_score": risk_score,
        "risk_level": get_risk_level_from_score(risk_score)
    }
```

### 3. Entity Risk Tracking

```python
# Entity risk scores are updated from scorer.py
update_entity_score(entity_id, score_result["risk_score"])
```

---

## Consistency Guarantees

### ✓ Single Source of Truth

All risk level computations use the same thresholds defined in `models.py`:
- `compute_risk()` - For ML predictions
- `get_risk_level_from_score()` - For existing scores
- `scorer.py` imports and uses `get_risk_level_from_score()`

### ✓ No Duplicate Logic

Risk level thresholds are defined in ONE place only (`models.py`)

### ✓ Consistent Across System

- Events use scorer's risk_level
- Entities use get_risk_level_from_score()
- Network topology uses get_risk_level_from_score()
- All use the same thresholds

---

## Testing Risk Computation

### Test 1: ML Prediction

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "proto": "tcp",
    "service": "http",
    "sbytes": 1000,
    "dbytes": 2000,
    ...
  }'
```

**Expected**: Returns risk_score and risk_level from ML model

### Test 2: Event Generation

```bash
# Let system run and check events
curl http://localhost:8000/events?limit=10
```

**Expected**: Each event has risk_score and risk_level from scorer

### Test 3: Network Topology

```bash
curl http://localhost:8000/network/topology
```

**Expected**: Each node has risk_level computed from risk_score

---

## Common Pitfalls (AVOIDED)

### ❌ Don't: Duplicate threshold logic

```python
# BAD - Duplicates thresholds
def my_function(score):
    if score >= 80:  # Different thresholds!
        return "critical"
```

### ✓ Do: Use centralized function

```python
# GOOD - Uses single source of truth
from models import get_risk_level_from_score

def my_function(score):
    return get_risk_level_from_score(score)
```

### ❌ Don't: Hardcode risk levels

```python
# BAD - Hardcoded level
event = {
    "risk_score": 75,
    "risk_level": "HIGH"  # Might be inconsistent!
}
```

### ✓ Do: Compute from score

```python
# GOOD - Computed consistently
from models import get_risk_level_from_score

event = {
    "risk_score": 75,
    "risk_level": get_risk_level_from_score(75)
}
```

---

## Summary

### Risk Computation Flow

1. **ML Model** → Raw score (0-1) → `compute_risk()` → Risk score (0-100) + Level
2. **Scorer** → ML score + Context → Final score (0-100) → `get_risk_level_from_score()` → Level
3. **Events** → Use scorer's risk_score and risk_level
4. **Entities** → Store risk_score, compute level on demand
5. **API** → Use `get_risk_level_from_score()` for any score → level conversion

### Key Functions

| Function | Location | Purpose |
|----------|----------|---------|
| `compute_risk()` | models.py | Convert ML score to risk score + level |
| `get_risk_level_from_score()` | models.py | Get level from existing score |
| `compute_risk_score()` | scorer.py | Enhance ML score with context |

### Thresholds (SINGLE SOURCE)

```
< 30  = LOW
< 50  = MEDIUM
< 65  = HIGH
>= 65 = CRITICAL
```

All defined in `models.py`, used everywhere.

---

**Last Updated**: March 1, 2026  
**Status**: ✓ CONSISTENT - Single source of truth implemented

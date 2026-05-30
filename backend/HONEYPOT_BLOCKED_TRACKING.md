# Honeypot & Blocked Entity Tracking

## Overview

EquiMind now tracks entity status (honeypot, blocked, isolated, monitored) in the database and provides comprehensive APIs to monitor these entities and their activities.

---

## Entity Status Types

| Status | Description | Use Case |
|--------|-------------|----------|
| `active` | Normal operational status | Default state for all entities |
| `monitored` | Enhanced monitoring enabled | Suspicious but not confirmed threat |
| `isolated` | Network access restricted | Confirmed threat, limited access |
| `blocked` | All access denied | Severe threat, complete lockout |
| `honeypot` | Moved to deception environment | Observe attacker behavior safely |

---

## Database Schema Updates

### Entities Table - New Columns

```sql
status TEXT DEFAULT 'active'           -- Entity status
is_honeypot BOOLEAN DEFAULT FALSE      -- Honeypot flag
honeypot_since TIMESTAMPTZ             -- When moved to honeypot
```

### Entity Actions Table (New)

```sql
CREATE TABLE entity_actions (
    id TEXT PRIMARY KEY,
    entity_id TEXT REFERENCES entities(id),
    action_type TEXT NOT NULL,
    message TEXT,
    performed_by TEXT DEFAULT 'system',
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);
```

### Events Table - New Column

```sql
is_honeypot_activity BOOLEAN DEFAULT FALSE  -- Flag for honeypot events
```

---

## API Endpoints

### 1. Execute Action on Entity

**POST** `/entity/{entity_id}/action/{action_type}`

Execute a security action on an entity.

**Available Actions:**
- `honeypot` - Move to honeypot environment
- `monitor` - Enable enhanced monitoring
- `isolate` - Isolate from network
- `block` - Block all access
- `reset` - Reset credentials
- `unblock` - Restore to active status

**Example:**
```bash
curl -X POST http://localhost:8000/entity/u12/action/honeypot
```

**Response:**
```json
{
  "success": true,
  "entity": "n.kim",
  "action": "honeypot",
  "message": "Entity moved to honeypot environment",
  "new_status": "honeypot",
  "timestamp": "2026-03-01T10:30:00Z",
  "action_id": "action_a1b2c3d4"
}
```

### 2. Get Entity Action History

**GET** `/entity/{entity_id}/actions?limit=50`

Get all actions performed on an entity.

**Example:**
```bash
curl http://localhost:8000/entity/u12/actions
```

**Response:**
```json
{
  "entity_id": "u12",
  "entity_name": "n.kim",
  "actions": [
    {
      "id": "action_a1b2c3d4",
      "timestamp": "2026-03-01T10:30:00Z",
      "entity_id": "u12",
      "entity_name": "n.kim",
      "action_type": "honeypot",
      "message": "Entity moved to honeypot environment",
      "performed_by": "system",
      "metadata": {
        "previous_status": "active",
        "new_status": "honeypot"
      }
    }
  ],
  "total_actions": 1,
  "source": "database"
}
```

### 3. Get Honeypot Entities

**GET** `/entities/honeypot`

Get all entities currently in honeypot environment.

**Example:**
```bash
curl http://localhost:8000/entities/honeypot
```

**Response:**
```json
{
  "honeypot_entities": [
    {
      "id": "u12",
      "name": "n.kim",
      "role": "UX Designer",
      "dept": "Product",
      "risk_score": 85.5,
      "status": "honeypot",
      "is_honeypot": true,
      "honeypot_since": "2026-03-01T10:30:00Z"
    }
  ],
  "count": 1,
  "source": "database"
}
```

### 4. Get Blocked Entities

**GET** `/entities/blocked`

Get all blocked or isolated entities.

**Example:**
```bash
curl http://localhost:8000/entities/blocked
```

**Response:**
```json
{
  "blocked_entities": [
    {
      "id": "u15",
      "name": "d.contractor",
      "role": "External Consultant",
      "dept": "External",
      "risk_score": 92.0,
      "status": "blocked",
      "updated_at": "2026-03-01T11:00:00Z"
    }
  ],
  "count": 1,
  "source": "database"
}
```

### 5. Get Honeypot Activities

**GET** `/honeypot/activities?entity_id={id}&limit=100`

Get all activities (events) from honeypot users.

**Example:**
```bash
# All honeypot activities
curl http://localhost:8000/honeypot/activities

# Specific entity's honeypot activities
curl http://localhost:8000/honeypot/activities?entity_id=u12&limit=50
```

**Response:**
```json
{
  "activities": [
    {
      "id": "evt_abc123",
      "timestamp": "2026-03-01T10:35:00Z",
      "entity_id": "u12",
      "user_name": "n.kim",
      "severity": "HIGH",
      "attack_cat": "Recon",
      "risk_score": 75.5,
      "decision": "RESTRICT",
      "is_honeypot_activity": true,
      "explanation": "Reconnaissance activity. Sequential port probing."
    }
  ],
  "count": 1,
  "source": "database"
}
```

### 6. Get Honeypot Summary

**GET** `/honeypot/summary`

Get comprehensive summary of honeypot operations.

**Example:**
```bash
curl http://localhost:8000/honeypot/summary
```

**Response:**
```json
{
  "total_honeypot_entities": 1,
  "entities": [
    {
      "id": "u12",
      "name": "n.kim",
      "role": "UX Designer",
      "dept": "Product",
      "risk_score": 85.5,
      "status": "honeypot",
      "is_honeypot": true,
      "honeypot_since": "2026-03-01T10:30:00Z",
      "recent_activity_count": 15,
      "recent_activities": [
        {
          "id": "evt_abc123",
          "timestamp": "2026-03-01T10:35:00Z",
          "severity": "HIGH",
          "attack_cat": "Recon",
          "risk_score": 75.5
        }
      ]
    }
  ],
  "source": "database"
}
```

---

## Usage Workflow

### Scenario: Suspicious User Detection

**Step 1: Detect High-Risk User**
```bash
# Monitor entities
curl http://localhost:8000/entities

# User u12 shows risk_score: 85 (CRITICAL)
```

**Step 2: Move to Honeypot**
```bash
# Move to honeypot for observation
curl -X POST http://localhost:8000/entity/u12/action/honeypot
```

**Step 3: Monitor Honeypot Activities**
```bash
# Watch what they do
curl http://localhost:8000/honeypot/activities?entity_id=u12
```

**Step 4: Analyze Behavior**
```bash
# Get comprehensive summary
curl http://localhost:8000/honeypot/summary
```

**Step 5: Take Final Action**
```bash
# If confirmed malicious, block
curl -X POST http://localhost:8000/entity/u12/action/block

# If false positive, restore
curl -X POST http://localhost:8000/entity/u12/action/unblock
```

---

## Frontend Integration

### Display Honeypot Users

```javascript
// Fetch honeypot entities
const response = await fetch('http://localhost:8000/entities/honeypot');
const data = await response.json();

// Display in UI
data.honeypot_entities.forEach(entity => {
  console.log(`${entity.name} - In honeypot since ${entity.honeypot_since}`);
});
```

### Display Blocked Users

```javascript
// Fetch blocked entities
const response = await fetch('http://localhost:8000/entities/blocked');
const data = await response.json();

// Display in UI
data.blocked_entities.forEach(entity => {
  console.log(`${entity.name} - Status: ${entity.status}`);
});
```

### Show Honeypot Activities

```javascript
// Fetch honeypot activities
const response = await fetch('http://localhost:8000/honeypot/activities?limit=50');
const data = await response.json();

// Display timeline
data.activities.forEach(activity => {
  console.log(`${activity.timestamp}: ${activity.user_name} - ${activity.explanation}`);
});
```

### Entity Action Button

```javascript
async function moveToHoneypot(entityId) {
  const response = await fetch(
    `http://localhost:8000/entity/${entityId}/action/honeypot`,
    { method: 'POST' }
  );
  
  const result = await response.json();
  
  if (result.success) {
    alert(`${result.entity} moved to honeypot`);
    // Refresh entity list
  }
}
```

---

## Database Queries

### Get Honeypot Entities (SQL)

```sql
SELECT * FROM entities 
WHERE is_honeypot = TRUE 
ORDER BY honeypot_since DESC;
```

### Get Honeypot Activities (SQL)

```sql
SELECT * FROM events 
WHERE is_honeypot_activity = TRUE 
ORDER BY timestamp DESC 
LIMIT 100;
```

### Get Entity Actions (SQL)

```sql
SELECT * FROM entity_actions 
WHERE entity_id = 'u12' 
ORDER BY timestamp DESC;
```

### Get Blocked Entities (SQL)

```sql
SELECT * FROM entities 
WHERE status IN ('blocked', 'isolated') 
ORDER BY updated_at DESC;
```

---

## Monitoring Dashboard

### Key Metrics to Display

1. **Honeypot Status**
   - Total entities in honeypot
   - Total honeypot activities today
   - Most active honeypot user

2. **Blocked Entities**
   - Total blocked entities
   - Recently blocked (last 24h)
   - Blocked by department

3. **Action History**
   - Recent actions taken
   - Actions by type
   - Actions by operator

### Example Dashboard Query

```bash
# Get all metrics at once
curl http://localhost:8000/honeypot/summary
curl http://localhost:8000/entities/blocked
curl http://localhost:8000/simulation/stats
```

---

## Security Considerations

### Production Implementation

1. **Authentication Required**
   - Only authorized SOC analysts can execute actions
   - Log who performed each action

2. **Approval Workflow**
   - High-impact actions (block, honeypot) require approval
   - Implement multi-step confirmation

3. **Audit Trail**
   - All actions logged to immutable audit log
   - Include reason for action

4. **Automated Rollback**
   - Auto-restore if false positive detected
   - Time-limited honeypot periods

### Example with Authentication

```python
@app.post("/entity/{entity_id}/action/{action_type}")
async def entity_action(
    entity_id: str, 
    action_type: str,
    current_user: User = Depends(get_current_user)  # Add auth
):
    # Check permissions
    if not current_user.has_permission("entity_actions"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Log who performed action
    action_record["performed_by"] = current_user.username
    
    # ... rest of implementation
```

---

## Testing

### Test Honeypot Flow

```bash
# 1. Move entity to honeypot
curl -X POST http://localhost:8000/entity/u12/action/honeypot

# 2. Verify status
curl http://localhost:8000/entities/honeypot

# 3. Generate some events (wait 30 seconds)
sleep 30

# 4. Check honeypot activities
curl http://localhost:8000/honeypot/activities?entity_id=u12

# 5. Restore entity
curl -X POST http://localhost:8000/entity/u12/action/unblock
```

### Test Blocked Flow

```bash
# 1. Block entity
curl -X POST http://localhost:8000/entity/u15/action/block

# 2. Verify blocked
curl http://localhost:8000/entities/blocked

# 3. Check action history
curl http://localhost:8000/entity/u15/actions

# 4. Unblock
curl -X POST http://localhost:8000/entity/u15/action/unblock
```

---

## Summary

### New Features

✓ Entity status tracking (active, monitored, isolated, blocked, honeypot)  
✓ Honeypot environment with activity tracking  
✓ Blocked entity management  
✓ Complete action audit trail  
✓ Comprehensive APIs for frontend integration  
✓ Database persistence with Supabase  

### API Endpoints

- `POST /entity/{id}/action/{type}` - Execute action
- `GET /entity/{id}/actions` - Get action history
- `GET /entities/honeypot` - List honeypot entities
- `GET /entities/blocked` - List blocked entities
- `GET /honeypot/activities` - Get honeypot activities
- `GET /honeypot/summary` - Get honeypot summary

### Database Tables

- `entities` - Updated with status and honeypot fields
- `entity_actions` - New table for action audit trail
- `events` - Updated with is_honeypot_activity flag

---

**Last Updated**: March 1, 2026  
**Status**: ✓ IMPLEMENTED - Honeypot & blocked tracking active

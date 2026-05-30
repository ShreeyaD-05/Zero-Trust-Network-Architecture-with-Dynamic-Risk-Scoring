# Supabase Integration Setup Guide

This guide will help you set up Supabase as the database backend for EquiMind Zero Trust Risk Engine.

## Overview

The system now supports dynamic user management with Supabase, replacing the hardcoded entity list. Features include:

- 20-person organization with realistic roles and departments
- Dynamic risk score updates stored in real-time
- Event logging to database
- Automatic fallback to hardcoded data if Supabase is unavailable

## Prerequisites

- Supabase account (free tier works fine)
- Python 3.8+
- Existing EquiMind installation

## Step 1: Create Supabase Project

1. Go to [https://supabase.com](https://supabase.com)
2. Sign up or log in
3. Click "New Project"
4. Fill in:
   - Project name: `equimind-risk-engine` (or your choice)
   - Database password: (save this securely)
   - Region: Choose closest to you
5. Wait for project to be created (~2 minutes)

## Step 2: Get Your Credentials

1. In your Supabase project dashboard, go to **Settings** → **API**
2. Copy these values:
   - **Project URL** (looks like: `https://xxxxx.supabase.co`)
   - **anon/public key** (long string starting with `eyJ...`)

## Step 3: Configure Environment Variables

1. Create or update `.env` file in the `backend` directory:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here

# Existing configuration
EVENT_INTERVAL_SECONDS=3
```

2. Replace the placeholder values with your actual credentials from Step 2

## Step 4: Create Database Schema

1. In Supabase dashboard, go to **SQL Editor**
2. Click **New Query**
3. Copy the entire contents of `supabase_schema.sql`
4. Paste into the SQL editor
5. Click **Run** (or press Ctrl+Enter)
6. You should see: "Success. No rows returned"

This creates two tables:
- `entities` - Stores users and service accounts
- `events` - Stores security events and risk assessments

## Step 5: Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs the Supabase Python client and other dependencies.

## Step 6: Seed the Database

Run the seed script to populate your database with 20 entities:

```bash
python seed_database.py
```

You should see output like:
```
============================================================
EquiMind Database Seeding
============================================================

Seeding 20 entities...
------------------------------------------------------------
✓ Created: j.hernandez          | Senior Backend Engineer    | Engineering
✓ Created: r.chen               | Frontend Engineer          | Engineering
...
------------------------------------------------------------

Seeding complete: 20/20 entities created
============================================================
```

## Step 7: Verify Setup

1. In Supabase dashboard, go to **Table Editor**
2. Click on `entities` table
3. You should see 20 rows with users and service accounts

## Step 8: Start the Backend

```bash
python main.py
```

Look for this line in the output:
```
INFO:     Using Supabase database with 20 entities
```

If you see this instead:
```
INFO:     Using fallback mode with 13 hardcoded entities
```

Then Supabase connection failed. Check your credentials in `.env`.

## Verification

Test the API endpoints:

```bash
# Check status (should show database_mode: "supabase")
curl http://localhost:8000/status

# Get all entities
curl http://localhost:8000/entities

# Get specific entity
curl http://localhost:8000/entity/u01
```

## Database Structure

### Entities Table

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT | Unique identifier (u01, s01, etc.) |
| name | TEXT | Entity name (username or service name) |
| role | TEXT | Job role or service type |
| dept | TEXT | Department (Engineering, IT, Finance, etc.) |
| location | TEXT | Physical or logical location |
| device | TEXT | Device identifier |
| trust_reserve | INTEGER | Trust points (0-15) |
| risk_score | NUMERIC | Current risk score (0-100) |
| created_at | TIMESTAMPTZ | Creation timestamp |
| updated_at | TIMESTAMPTZ | Last update timestamp |

### Events Table

Stores all security events with full context including risk scores, decisions, and kill chain tracking.

## Organization Structure (20 Entities)

The seeded organization includes:

- **Engineering** (4 people): Backend, Frontend, ML, DevOps engineers
- **IT & Security** (3 people): DBA, Security Analyst, IT Support
- **Finance** (3 people): Data Analyst, Finance Manager, Financial Analyst
- **Product & Design** (2 people): Product Manager, UX Designer
- **HR & Operations** (2 people): HR Manager, Operations Manager
- **External** (2 people): Contractors with higher risk profiles
- **Service Accounts** (4 accounts): Database, API, Backup, Monitoring services

## Monitoring Risk Scores

Risk scores are updated in real-time as events are simulated. You can:

1. **View in Supabase Dashboard**: Table Editor → entities → Sort by risk_score
2. **Query via API**: `GET /entities` returns all entities with current scores
3. **Watch events**: `GET /events` shows recent security events

## Advanced: Event Logging

To enable event logging to Supabase (optional):

1. Uncomment the event logging code in `simulator.py`
2. Events will be stored in the `events` table
3. Query historical events: `GET /events?limit=100`

## Troubleshooting

### "Using fallback mode" message

- Check `.env` file exists and has correct credentials
- Verify SUPABASE_URL and SUPABASE_KEY are set
- Test connection: `python -c "from database import init_supabase; init_supabase()"`

### "Failed to fetch entities" errors

- Verify tables were created (check SQL Editor)
- Run seed script again: `python seed_database.py`
- Check Supabase project is not paused (free tier pauses after inactivity)

### Connection timeout

- Check your internet connection
- Verify Supabase project region
- Try restarting the backend

## Fallback Mode

If Supabase is unavailable, the system automatically falls back to hardcoded entities. This ensures the application continues working even without database connectivity.

To force fallback mode for testing:
1. Remove or comment out SUPABASE_URL in `.env`
2. Restart backend

## Next Steps

- Monitor risk scores in real-time via the frontend
- Query events table for security analytics
- Customize entity data in Supabase Table Editor
- Add more entities using the seed script as a template

## Support

For issues or questions:
- Check Supabase logs: Dashboard → Logs
- Review backend logs for error messages
- Verify API connectivity: `curl http://localhost:8000/status`

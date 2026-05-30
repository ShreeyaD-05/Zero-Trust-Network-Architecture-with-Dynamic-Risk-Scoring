# Supabase Quick Start - 5 Minutes

Get EquiMind running with Supabase in 5 minutes.

## 1. Create Supabase Project (2 min)

1. Go to [supabase.com](https://supabase.com) → New Project
2. Name: `equimind` | Password: (save it) | Region: (closest)
3. Wait for creation

## 2. Setup Database (1 min)

1. Dashboard → **SQL Editor** → New Query
2. Copy all from `supabase_schema.sql` → Paste → Run
3. Should see: "Success. No rows returned"

## 3. Configure Backend (1 min)

Create `backend/.env`:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
EVENT_INTERVAL_SECONDS=3
```

Get URL and Key from: Dashboard → Settings → API

## 4. Install & Seed (1 min)

```bash
cd backend
pip install supabase postgrest
python seed_database.py
```

Should see: "Seeding complete: 20/20 entities created"

## 5. Start Backend

```bash
python main.py
```

Look for: `INFO: Using Supabase database with 20 entities`

## Verify

```bash
curl http://localhost:8000/status
```

Should show: `"database_mode": "supabase"`

## Done!

Your backend now uses Supabase with 20 dynamic entities. Risk scores update in real-time in the database.

## View Data

Supabase Dashboard → Table Editor → `entities` table

## Troubleshooting

**"Using fallback mode"** → Check `.env` credentials

**"Failed to fetch"** → Run seed script again

**No .env file** → Create it in `backend/` directory

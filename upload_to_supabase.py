"""
upload_to_supabase.py — refreshes the Supabase materialized view after a data update.

Usage:
  1. Set SUPABASE_SERVICE_KEY env variable (find it in Supabase → Project Settings → API → service_role key)
     $env:SUPABASE_SERVICE_KEY = "eyJ..."   (PowerShell)
     export SUPABASE_SERVICE_KEY="eyJ..."   (bash)
  2. Run: python upload_to_supabase.py

The service key is never committed to git. The anon key in index.html is safe (read-only, RLS-protected).
"""
import os, requests

SUPABASE_URL = 'https://yntahmnlvritixjebmvi.supabase.co'
SERVICE_KEY  = os.environ.get('SUPABASE_SERVICE_KEY')

if not SERVICE_KEY:
    print('ERROR: set SUPABASE_SERVICE_KEY environment variable first.')
    print('  Find it in Supabase → Project Settings → API → service_role (secret)')
    raise SystemExit(1)

headers = {
    'apikey':        SERVICE_KEY,
    'Authorization': f'Bearer {SERVICE_KEY}',
    'Content-Type':  'application/json',
}

print('Refreshing materialized view mv_dashboard_cache …')
resp = requests.post(
    f'{SUPABASE_URL}/rest/v1/rpc/refresh_dashboard_cache',
    headers=headers,
    json={}
)
if resp.status_code == 404:
    # Fallback: run SQL via the management API isn't available here.
    # Ask user to run the SQL manually or via Supabase dashboard.
    print('refresh_dashboard_cache function not found.')
    print('Run this SQL in Supabase SQL Editor:')
    print('  REFRESH MATERIALIZED VIEW mv_dashboard_cache;')
else:
    resp.raise_for_status()
    print('Done.')

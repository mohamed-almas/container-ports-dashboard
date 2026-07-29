"""
assemble.py — previously injected dashboard_data.json into the template.
Data is now served live from Supabase (get_dashboard_data RPC), so this
script simply copies dashboard_template.html → index.html.

After a data refresh, run:
  1. python build_data.py          (re-generates dashboard_data.json locally)
  2. python upload_to_supabase.py  (refreshes the Supabase materialized view)
  3. git add index.html && git commit && git push  (if template changed)
"""
import shutil, os

src = 'dashboard_template.html'
dst = 'index.html'
shutil.copy(src, dst)
print(f'Copied {src} → {dst}  ({os.path.getsize(dst)/1e3:.0f} KB)')

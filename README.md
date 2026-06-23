# Container Ports Dashboard

Live dashboard: https://mohamed-almas.github.io/container-ports-dashboard/

Global container port throughput & capacity dashboard with Global / Region /
Coastal Region / Country / Port drill-down, annual trends, CAGR, YoY,
rankings and utilization.

## Files

- `Container Ports.xlsx` — source data (`thru`, `cap`, `port_&_geo` sheets, joined on `adpg_port_id`)
- `build_data.py` — reads the Excel file, aggregates by region/coastal region/country/port, writes `dashboard_data.json`
- `dashboard_template.html` — dashboard UI/JS template (Chart.js), with `__DATA_JSON__` placeholder
- `assemble.py` — injects `dashboard_data.json` into the template, writes `index.html`
- `index.html` — the deployed dashboard (this is what GitHub Pages serves)

## Refresh workflow (annual refresh or data corrections)

1. Update `Container Ports.xlsx` with the corrected/refreshed data (same sheet names and columns).
2. Regenerate the data and dashboard:
   ```
   python build_data.py
   python assemble.py
   ```
3. Check it locally by opening `index.html` in a browser.
4. Commit and push:
   ```
   git add "Container Ports.xlsx" dashboard_data.json index.html
   git commit -m "Refresh data through <year>"
   git push
   ```
5. GitHub Pages redeploys automatically within ~1 minute of the push.

## Notes on the data

- `build_data.py` treats years through 2024 as actuals; 2025-2030 are carried
  as indicative/forecast figures present in the source file.
- Utilization (`throughput / capacity`) can exceed 100% for some ports — this
  reflects a definitional gap between reported throughput (which can include
  transshipment counted multiple times) and nominal terminal capacity in the
  source file, not a calculation error.

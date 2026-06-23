import pandas as pd
import numpy as np
import json

thru = pd.read_excel('_work.xlsx', sheet_name='thru')
cap = pd.read_excel('_work.xlsx', sheet_name='cap')
geo = pd.read_excel('_work.xlsx', sheet_name='port_&_geo')

geo_small = geo[['adpg_port_id','Port','Coastal Region','Clarksons Region','iso3Code','countryName','Region','portLat','portLon']].drop_duplicates(subset=['adpg_port_id'])
geo_small = geo_small.rename(columns={'Clarksons Region':'ClarksonsRegion','Coastal Region':'CoastalRegion','countryName':'Country'})

thru['Year'] = pd.to_datetime(thru['Date']).dt.year
cap['Date'] = pd.to_datetime(cap['Date'], errors='coerce')
cap['Year'] = cap['Date'].dt.year

# historical cutoff: last year with near-full port coverage (actuals), forecast beyond
HIST_END = 2024
FC_END = 2030  # keep some forecast horizon, trim far-future flat tail

thru_h = thru[thru['Year'] <= FC_END].copy()
cap_h = cap[cap['Year'] <= FC_END].copy()

thru_h = thru_h.merge(geo_small, on='adpg_port_id', how='left', suffixes=('','_geo'))
cap_h = cap_h.merge(geo_small, on='adpg_port_id', how='left', suffixes=('','_geo'))

# annual throughput per port (sum if duplicates per port-year, take mean to avoid double count across sources -> use mean per port-year then sum)
port_year_thru = thru_h.groupby(['adpg_port_id','Year'], as_index=False).agg(Volume=('Volume','mean'))
port_year_cap = cap_h.groupby(['adpg_port_id','Year'], as_index=False).agg(Capacity=('Capacity','mean'))

port_year = port_year_thru.merge(port_year_cap, on=['adpg_port_id','Year'], how='left')
port_year = port_year.merge(geo_small, on='adpg_port_id', how='left')
port_year['Utilization'] = port_year['Volume'] / port_year['Capacity']

def cagr(series_by_year, y0, y1):
    s = series_by_year
    if y0 not in s.index or y1 not in s.index or s[y0] <= 0:
        return None
    n = y1 - y0
    if n <= 0:
        return None
    return (s[y1]/s[y0])**(1/n) - 1

def build_level(df, keycol, namecol=None):
    namecol = namecol or keycol
    g = df.groupby([keycol,'Year'], as_index=False)['Volume'].sum()
    pivot = g.pivot(index=keycol, columns='Year', values='Volume')
    out = {}
    years = sorted(df['Year'].dropna().unique().tolist())
    for k in pivot.index:
        s = pivot.loc[k]
        out[k] = {
            'name': k,
            'years': years,
            'volumes': [None if pd.isna(s.get(y)) else round(float(s.get(y)),1) for y in years]
        }
    return out, years

global_g = thru_h.groupby('Year', as_index=False)['Volume'].sum().rename(columns={'Volume':'TotalVolume'})
global_cap = cap_h.groupby('Year', as_index=False)['Capacity'].sum().rename(columns={'Capacity':'TotalCapacity'})
global_df = global_g.merge(global_cap, on='Year', how='left')
global_df = global_df.sort_values('Year')
global_df['YoY'] = global_df['TotalVolume'].pct_change()*100
global_df['Utilization'] = global_df['TotalVolume']/global_df['TotalCapacity']*100

region_data, region_years = build_level(thru_h.dropna(subset=['Region']), 'Region')
coastal_data, coastal_years = build_level(thru_h.dropna(subset=['CoastalRegion']), 'CoastalRegion')
country_data, country_years = build_level(thru_h.dropna(subset=['Country']), 'Country')
port_data, port_years = build_level(thru_h.dropna(subset=['Port']), 'Port')

# capacity totals by level for utilization
def build_cap_level(df, keycol):
    g = df.groupby([keycol,'Year'], as_index=False)['Capacity'].sum()
    pivot = g.pivot(index=keycol, columns='Year', values='Capacity')
    return pivot

region_cap = build_cap_level(cap_h.dropna(subset=['Region']), 'Region')
coastal_cap = build_cap_level(cap_h.dropna(subset=['CoastalRegion']), 'CoastalRegion')
country_cap = build_cap_level(cap_h.dropna(subset=['Country']), 'Country')
port_cap = build_cap_level(cap_h.dropna(subset=['Port']), 'Port')

def attach_util(data_dict, cap_pivot):
    for k, rec in data_dict.items():
        caps = []
        utils = []
        for i, y in enumerate(rec['years']):
            c = cap_pivot.loc[k, y] if (k in cap_pivot.index and y in cap_pivot.columns) else None
            c = None if pd.isna(c) else float(c)
            caps.append(round(c,1) if c else None)
            v = rec['volumes'][i]
            if c and v is not None and c > 0:
                utils.append(round(v/c*100,1))
            else:
                utils.append(None)
        rec['capacities'] = caps
        rec['utilization'] = utils

attach_util(region_data, region_cap)
attach_util(coastal_data, coastal_cap)
attach_util(country_data, country_cap)
attach_util(port_data, port_cap)

def cagr_for_rec(rec, y0, y1):
    years = rec['years']
    if y0 not in years or y1 not in years:
        return None
    v0 = rec['volumes'][years.index(y0)]
    v1 = rec['volumes'][years.index(y1)]
    if v0 is None or v1 is None or v0 <= 0:
        return None
    n = y1-y0
    if n<=0: return None
    return round(((v1/v0)**(1/n)-1)*100,2)

for d in [region_data, coastal_data, country_data, port_data]:
    for k, rec in d.items():
        rec['cagr_5y'] = cagr_for_rec(rec, 2019, 2024)
        rec['cagr_10y'] = cagr_for_rec(rec, 2014, 2024)
        years = rec['years']
        if 2024 in years and 2023 in years:
            v24 = rec['volumes'][years.index(2024)]
            v23 = rec['volumes'][years.index(2023)]
            rec['yoy_2024'] = round((v24/v23-1)*100,2) if (v24 and v23) else None
        else:
            rec['yoy_2024'] = None
        rec['vol_2024'] = rec['volumes'][years.index(2024)] if 2024 in years else None
        rec['vol_2014'] = rec['volumes'][years.index(2014)] if 2014 in years else None

# port-level metadata for filtering/joining (region, coastal, country)
port_meta = geo_small.set_index('Port')[['Region','CoastalRegion','Country']].to_dict('index')

# country meta: region mapping
country_meta = geo_small.drop_duplicates(subset=['Country']).set_index('Country')[['Region']].to_dict('index')

# top ports 2024 ranking with prior rank (2014) for "rank change"
top_ports_2024 = sorted(
    [(k,v['vol_2024']) for k,v in port_data.items() if v['vol_2024']],
    key=lambda x: -x[1]
)[:50]

top_ports_2014 = sorted(
    [(k,v['vol_2014']) for k,v in port_data.items() if v['vol_2014']],
    key=lambda x: -x[1]
)
rank_2014 = {k:i+1 for i,(k,v) in enumerate(top_ports_2014)}

top_ports_list = []
for i,(k,v) in enumerate(top_ports_2024):
    meta = port_meta.get(k, {})
    top_ports_list.append({
        'rank': i+1,
        'port': k,
        'volume_2024': round(v,1),
        'country': meta.get('Country'),
        'region': meta.get('Region'),
        'coastal_region': meta.get('CoastalRegion'),
        'cagr_10y': port_data[k]['cagr_10y'],
        'yoy_2024': port_data[k]['yoy_2024'],
        'rank_2014': rank_2014.get(k),
        'rank_change': (rank_2014.get(k) - (i+1)) if rank_2014.get(k) else None,
        'utilization_2024': port_data[k]['utilization'][port_data[k]['years'].index(2024)] if 2024 in port_data[k]['years'] else None
    })

output = {
    'meta': {
        'hist_end': HIST_END,
        'forecast_end': FC_END,
        'generated_note': 'Throughput in TEU. Capacity in TEU annual nominal capacity.'
    },
    'global': {
        'years': global_df['Year'].tolist(),
        'volume': [round(x,1) for x in global_df['TotalVolume'].tolist()],
        'capacity': [None if pd.isna(x) else round(x,1) for x in global_df['TotalCapacity'].tolist()],
        'yoy': [None if pd.isna(x) else round(x,2) for x in global_df['YoY'].tolist()],
        'utilization': [None if pd.isna(x) else round(x,1) for x in global_df['Utilization'].tolist()]
    },
    'region': region_data,
    'coastal_region': coastal_data,
    'country': country_data,
    'port': port_data,
    'port_meta': port_meta,
    'country_meta': country_meta,
    'top_ports_2024': top_ports_list
}

with open('dashboard_data.json','w', encoding='utf-8') as f:
    json.dump(output, f)

print("global years", output['global']['years'])
print("num regions", len(region_data))
print("num coastal", len(coastal_data))
print("num countries", len(country_data))
print("num ports", len(port_data))
print("global vol 2024", output['global']['volume'][output['global']['years'].index(2024)])
print("top 10 ports 2024:")
for p in top_ports_list[:10]:
    print(p)
import os
print("file size MB", os.path.getsize('dashboard_data.json')/1e6)

import json, urllib.request, time
from collections import Counter

BASE = "https://gis.water.ca.gov/arcgis/rest/services/Environment/i07_WellCompletionReports/FeatureServer/0/query"
FIELDS = "WCRNumber,DecimalLatitude,DecimalLongitude,PlannedUseFormerUse,TotalCompletedDepth,StaticWaterLevel,Township,Range,Section,City,B118WellUse,CountyName"
BATCH = 2000
COUNTIES = ["Kern", "Tulare", "Fresno", "Kings", "Madera", "Merced", "San Joaquin", "Stanislaus"]

all_wells = []

for county in COUNTIES:
    offset = 0
    county_count = 0
    while True:
        url = f"{BASE}?where=CountyName='{county}'&outFields={FIELDS}&f=json&resultRecordCount={BATCH}&resultOffset={offset}&orderByFields=OBJECTID"
        try:
            with urllib.request.urlopen(urllib.request.Request(url), timeout=90) as resp:
                data = json.loads(resp.read())
        except Exception as e:
            print(f"  Error at offset {offset}: {e}")
            break
        features = data.get("features", [])
        if not features:
            break
        for feat in features:
            a = feat["attributes"]
            lat = a.get("DecimalLatitude")
            lng = a.get("DecimalLongitude")
            if lat and lng and lat != 0 and lng != 0:
                well = {
                    "id": a.get("WCRNumber", ""),
                    "lat": round(lat, 6),
                    "lng": round(lng, 6),
                    "use": a.get("B118WellUse") or a.get("PlannedUseFormerUse") or "Unknown",
                    "depth_ft": a.get("TotalCompletedDepth"),
                    "water_level_ft": None,
                    "city": (a.get("City") or "").strip(),
                    "county": county,
                    "trs": f"{a.get('Township','')}{a.get('Range','')}{a.get('Section','')}".strip(),
                }
                swl = a.get("StaticWaterLevel")
                if swl:
                    try:
                        well["water_level_ft"] = float(swl)
                    except:
                        pass
                all_wells.append(well)
                county_count += 1
        offset += BATCH
        time.sleep(0.3)
    print(f"  {county}: {county_count:,} wells")

print(f"\nTOTAL: {len(all_wells):,} wells across {len(COUNTIES)} counties")

uses = Counter(w["use"] for w in all_wells)
print("\nWell types:")
for use, count in uses.most_common(10):
    print(f"  {use:45s} {count:,}")

counties = Counter(w["county"] for w in all_wells)
print("\nBy county:")
for c, count in counties.most_common():
    print(f"  {c:20s} {count:,}")

out_path = "/Users/mmm/Downloads/waterxchane/data/monitoring/kern_wells.json"
with open(out_path, "w") as f:
    json.dump(all_wells, f)

import os
size = os.path.getsize(out_path)
print(f"\nSaved: {size/1024/1024:.1f} MB")

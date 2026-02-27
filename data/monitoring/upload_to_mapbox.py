"""
Upload GeoJSON files to Mapbox as tilesets using the Uploads API.
"""
import json
import os
import time
import boto3
import requests

SK_TOKEN = os.environ.get("MAPBOX_SECRET_TOKEN", "")
USERNAME = "ctu2"
HYDRO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hydrology")

UPLOADS = [
    {
        "file": os.path.join(HYDRO_DIR, "gw_elevation_contours.geojson"),
        "tileset": f"{USERNAME}.gw-elevation-contours",
        "name": "GW Elevation Contours Spring 2025",
    },
    {
        "file": os.path.join(HYDRO_DIR, "gw_level_change_contours.geojson"),
        "tileset": f"{USERNAME}.gw-level-change-contours",
        "name": "GW Level Change 2014-2024",
    },
    {
        "file": os.path.join(HYDRO_DIR, "c2vsim_watersheds.geojson"),
        "tileset": f"{USERNAME}.c2vsim-watersheds",
        "name": "C2VSim Small Watersheds",
    },
    {
        "file": os.path.join(HYDRO_DIR, "gw_elevation_points.geojson"),
        "tileset": f"{USERNAME}.gw-elevation-points",
        "name": "GW Elevation Points Spring 2024",
    },
]


def upload_one(info):
    filepath = info["file"]
    if not os.path.exists(filepath):
        print(f"  SKIP: {filepath} not found")
        return

    size_mb = os.path.getsize(filepath) / 1024 / 1024
    print(f"\n{'='*60}")
    print(f"Uploading: {info['name']} ({size_mb:.1f} MB)")
    print(f"  Tileset: {info['tileset']}")

    # Step 1: Get S3 credentials
    print("  1. Getting upload credentials...")
    creds_url = f"https://api.mapbox.com/uploads/v1/{USERNAME}/credentials?access_token={SK_TOKEN}"
    creds = requests.post(creds_url).json()
    if "accessKeyId" not in creds:
        print(f"  ERROR getting credentials: {creds}")
        return

    # Step 2: Upload to S3
    print("  2. Uploading to S3 staging...")
    s3 = boto3.client(
        "s3",
        aws_access_key_id=creds["accessKeyId"],
        aws_secret_access_key=creds["secretAccessKey"],
        aws_session_token=creds["sessionToken"],
        region_name="us-east-1",
    )
    s3.upload_file(filepath, creds["bucket"], creds["key"])
    print(f"     Staged OK")

    # Step 3: Create upload
    print("  3. Creating tileset...")
    upload_url = f"https://api.mapbox.com/uploads/v1/{USERNAME}?access_token={SK_TOKEN}"
    result = requests.post(upload_url, json={
        "url": creds["url"],
        "tileset": info["tileset"],
        "name": info["name"],
    }).json()

    if "id" not in result:
        print(f"  ERROR creating upload: {result}")
        return

    upload_id = result["id"]
    print(f"     Upload ID: {upload_id}")

    # Step 4: Poll for completion
    print("  4. Processing", end="", flush=True)
    for _ in range(120):
        time.sleep(3)
        status_url = f"https://api.mapbox.com/uploads/v1/{USERNAME}/{upload_id}?access_token={SK_TOKEN}"
        status = requests.get(status_url).json()
        if status.get("complete"):
            if status.get("error"):
                print(f"\n     ERROR: {status['error']}")
            else:
                print(f"\n     DONE! Tileset ready: {info['tileset']}")
            return
        print(".", end="", flush=True)

    print("\n     TIMEOUT — check https://studio.mapbox.com/tilesets/")


if __name__ == "__main__":
    for info in UPLOADS:
        upload_one(info)
    print("\n\nAll uploads complete!")
    print("View at: https://studio.mapbox.com/tilesets/")

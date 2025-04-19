import requests
from datetime import datetime, timezone
import math
import os

# ------------------ Config ------------------
LAT = 33.752473    # Your latitude (e.g., Lahore)
LON = 72.778760     # Your longitude
RADIUS_KM = 400   # Alert if quake is within this radius
MIN_MAG = 3.0     # Minimum magnitude for alert

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") # Reads from environment variable
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID") # Reads from environment variable


# --- Check if variables are set ---
if not TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN environment variable not set.")
    exit(1) # Exit if the token isn't found
if not CHAT_ID:
    print("Error: TELEGRAM_CHAT_ID environment variable not set.")
    exit(1) # Exit if the chat ID isn't found
# -------------------------------------------

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def get_quakes():
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
    res = requests.get(url).json()
    recent_quakes = []
    print(f"Fetching recent earthquakes (min magnitude: {MIN_MAG}, max distance: {RADIUS_KM} km)...")
    for feature in res["features"]:
        props = feature["properties"]
        coords = feature["geometry"]["coordinates"]
        lon, lat = coords[0], coords[1]
        depth = coords[2]  # Depth in km
        mag = props["mag"]
        place = props["place"]
        # Fix deprecated datetime method
        time = datetime.fromtimestamp(props["time"] / 1000, timezone.utc)
        time_str = time.strftime("%Y-%m-%d %H:%M:%S")

        dist = haversine(LAT, LON, lat, lon)
        if mag and mag >= MIN_MAG and dist <= RADIUS_KM:
            # Print earthquake information
            print(f"Earthquake found: Magnitude {mag} at {place}, {int(dist)} km away, Time: {time}")
            
            msg = (f"🌍 *Earthquake Alert!*\n"
                  f"Magnitude: {mag}\n"
                  f"Location: {place}\n"
                  f"Distance: {int(dist)} km from home\n"
                  f"Depth: {depth:.1f} km\n"
                  f"Time: {time_str} UTC")
            
            recent_quakes.append(msg)
    print(f"Total earthquakes meeting criteria: {len(recent_quakes)}")
    return recent_quakes

def send_alert(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    print(f"Attempting to send alert: {msg[:50]}...")
    data = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    }
    # Keep header to prevent connection reuse issues, good practice
    headers = {
        'Connection': 'close'
    }
    try:
        # Explicit timeout, include headers
        response = requests.post(url, data=data, headers=headers, timeout=30)
        print(f"Telegram Response Status Code: {response.status_code}")
        response.raise_for_status() # Raise exception for 4xx/5xx errors
        print("Alert sent successfully.")
    except requests.exceptions.Timeout:
        print(f"Error: Timeout after 30 seconds connecting/reading from Telegram API. URL: {url}")
    except requests.exceptions.ConnectionError as e:
        print(f"Error: Connection Error connecting to Telegram API. Check network/firewall. Details: {e}")
    except requests.exceptions.HTTPError as e:
        # Log Telegram's error response for debugging
        print(f"Error: HTTP Error from Telegram API. Status Code: {e.response.status_code}")
        print(f"Telegram Response Body: {e.response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error: General request exception sending Telegram alert: {e}")

if __name__ == "__main__":
    print(f"Script started at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    alerts = get_quakes()
    print(f"Alerts found: {len(alerts)}")
    if not alerts:
        print("No relevant earthquakes found matching criteria.")
    else:
        for alert in alerts:
            send_alert(alert)
            # Optional: Add a small delay if sending multiple alerts very quickly
            # import time
            # time.sleep(1)
    print("Script finished.")
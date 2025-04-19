import requests
from datetime import datetime, timezone
import math
import os

# ------------------ Config ------------------
LAT = 33.752473    # Your latitude (e.g., Lahore)
LON = 72.778760     # Your longitude
RADIUS_KM = 400   # Alert if quake is within this radius
MIN_MAG = 3.0     # Minimum magnitude for alert

# TOKEN = os.getenv("7833414139:AAEIaMi0G3hRUqCbYtU7NgKEiDVVJ9fGyNE")
# CHAT_ID = os.getenv("8151509577")
TOKEN = "7833414139:AAEIaMi0G3hRUqCbYtU7NgKEiDVVJ9fGyNE"
CHAT_ID = "8151509577"
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
    print(f"Sending alert: {msg}")
    data = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    }
    #close eonnection
    headers = {
        "Connection": "close"
    }
    # requests.post(url, data=data)
    requests.post(url, data=data, headers=headers)

if __name__ == "__main__":
    alerts = get_quakes()
    print(f"Alerts found: {len(alerts)}")
    for alert in alerts:
        send_alert(alert)

import requests
from datetime import datetime, timezone, timedelta # Import timedelta
import math
import os

# --- (Your Config: LAT, LON, RADIUS_KM, MIN_MAG, TOKEN, CHAT_ID) ---
# Make sure LAT, LON, RADIUS_KM, MIN_MAG are defined here
MIN_MAG = 3.0 # Minimum magnitude to alert on
RADIUS_KM = 500.0 # Maximum distance from your location in km
LAT = 33.755712 # Your latitude (e.g., San Francisco)
LON = 72.773742 # Your longitude (e.g., San Francisco)

# --- (Your haversine function) ---
def haversine(lat1, lon1, lat2, lon2):
    # ... (your haversine implementation) ...
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def get_quakes():
    # --- (Your get_quakes setup: url, request, error handling) ---
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
    headers = { # Good practice: Identify your script
        'User-Agent': 'MyEarthquakeAlertBot/1.0 (github.com/your_username/your_repo)' # Customize!
    }
    try:
        res = requests.get(url, timeout=20, headers=headers)
        res.raise_for_status()
        data = res.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching earthquake data from USGS: {e}")
        return []

    recent_quakes_data = [] # Store tuples of (message, stats_dict)
    print(f"Fetching recent earthquakes (min magnitude: {MIN_MAG}, max distance: {RADIUS_KM} km)...")

    now_utc = datetime.now(timezone.utc) # Get current time once

    for feature in data.get("features", []):
        props = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        coords = geometry.get("coordinates")
        event_id = feature.get("id", "N/A") # Get the primary feature ID

        # Basic checks for essential data
        if not coords or len(coords) < 3 or not props:
            continue

        lon, lat, depth = coords[0], coords[1], coords[2]
        mag = props.get("mag")
        place = props.get("place", "Unknown Location")
        time_ms = props.get("time")
        event_type = props.get("type", "unknown") # e.g., "earthquake", "quarry blast"

        # More detailed checks
        if mag is None or time_ms is None: # Magnitude and time are essential
             continue
        # Ensure magnitude is a number before comparison
        if not isinstance(mag, (int, float)):
            try:
                mag = float(mag) # Try converting if it's a string number
            except (ValueError, TypeError):
                continue # Skip if magnitude isn't a valid number

        try:
            time_utc = datetime.fromtimestamp(time_ms / 1000, timezone.utc)
            time_str = time_utc.strftime("%Y-%m-%d %H:%M:%S %Z") # e.g., 2023-10-27 10:50:00 UTC
            time_ago = now_utc - time_utc # Calculate time difference
        except (TypeError, ValueError):
            continue # Skip if time is invalid

        dist = haversine(LAT, LON, lat, lon)

        # Your filtering criteria
        if mag >= MIN_MAG and dist <= RADIUS_KM:

            # --- Extract More Single-Event Stats ---
            # Use .get() for safety, providing default values (None or "N/A")

            mag_type = props.get("magType", "N/A")     # Magnitude type (ml, mb, mw)
            status = props.get("status", "N/A")       # "automatic" or "reviewed"
            tsunami = props.get("tsunami", 0)         # Tsunami flag (0 or 1)
            sig = props.get("sig", "N/A")             # Significance (0-1000)
            net = props.get("net", "N/A")             # Contributing network (us, ci, ak)
            nst = props.get("nst")                    # Number of stations used (integer or None)
            dmin = props.get("dmin")                  # Distance to nearest station (degrees, float or None)
            rms = props.get("rms")                    # RMS travel time residual (float or None)
            gap = props.get("gap")                    # Largest azimuthal gap (degrees, float or None)
            felt = props.get("felt")                  # Number of felt reports (integer or None)
            cdi = props.get("cdi")                    # Max Community Decimal Intensity (float or None)
            mmi = props.get("mmi")                    # Max Modified Mercalli Intensity (float or None)
            alert = props.get("alert")                # PAGER alert level (string or None) - green, yellow, orange, red
            updated_ms = props.get("updated")         # Last update time
            updated_str = "N/A"
            if updated_ms:
                try:
                    updated_utc = datetime.fromtimestamp(updated_ms / 1000, timezone.utc)
                    updated_str = updated_utc.strftime("%Y-%m-%d %H:%M:%S %Z")
                except (TypeError, ValueError):
                    pass # Ignore update time if invalid

            # --- Calculate Derived Stats ---
            # Time Ago String (more human-readable)
            seconds_ago = time_ago.total_seconds()
            if seconds_ago < 60:
                time_ago_str = f"{int(seconds_ago)} seconds ago"
            elif seconds_ago < 3600:
                time_ago_str = f"{int(seconds_ago / 60)} minutes ago"
            else:
                time_ago_str = f"{seconds_ago / 3600:.1f} hours ago"

            # Depth Classification (example thresholds)
            if depth < 70:
                depth_category = "Shallow"
            elif depth < 300:
                depth_category = "Intermediate"
            else:
                depth_category = "Deep"

            # --- Store Stats in a Dictionary ---
            event_stats = {
                "id": event_id,
                "magnitude": mag,
                "mag_type": mag_type,
                "location": place,
                "latitude": lat,
                "longitude": lon,
                "distance_km": int(dist),
                "depth_km": depth,
                "depth_category": depth_category,
                "event_time_utc": time_str,
                "time_ago": time_ago_str,
                "event_type": event_type,
                "status": status,
                "significance": sig,
                "network": net,
                "tsunami_warning": "Yes" if tsunami == 1 else "No",
                "pager_alert": alert if alert else "None",
                "felt_reports": felt if felt is not None else 0,
                "max_cdi": cdi if cdi is not None else "N/A",
                "max_mmi": mmi if mmi is not None else "N/A",
                "num_stations": nst if nst is not None else "N/A",
                "station_gap": gap if gap is not None else "N/A",
                "min_station_dist_deg": dmin if dmin is not None else "N/A",
                "rms_residual": rms if rms is not None else "N/A",
                "last_updated_utc": updated_str
            }

            # --- Format the Alert Message (Select stats you want) ---
            msg = (f"🌍 *Earthquake Alert!*\n\n"
                   f"*Magnitude:* {mag} {mag_type}\n"
                   f"*Location:* {place}\n"
                   f"*Distance:* {int(dist)} km away from me\n"
                   f"*Depth:* {depth:.1f} km ({depth_category})\n"
                   f"*Time:* {time_str} ({time_ago_str})\n"
                   f"*Type:* {event_type.capitalize()}\n"
                   f"*Status:* {status.capitalize()}\n"
                   f"*Significance:* {sig}\n"
                   f"*Felt Reports:* {event_stats['felt_reports']}\n" # Use dict for clarity
                   f"*Tsunami Warning:* {event_stats['tsunami_warning']}\n"
                   f"*PAGER Alert:* {event_stats['pager_alert']}\n"
                   f"\n_ID: {event_id}_") # Include ID for reference

            # Add conditional stats if they exist
            if event_stats['max_cdi'] != "N/A":
                msg += f"\n*Max Intensity (CDI):* {event_stats['max_cdi']}"
            # Add others like MMI, num_stations etc. if desired

            # --- Print Extended Info Locally ---
            print("-" * 30)
            print(f"Earthquake Found (ID: {event_id}):")
            for key, value in event_stats.items():
                 print(f"  {key.replace('_', ' ').capitalize()}: {value}")
            print("-" * 30)

            recent_quakes_data.append((msg, event_stats)) # Append tuple

    print(f"Total earthquakes meeting criteria: {len(recent_quakes_data)}")
    return recent_quakes_data

# --- (Your send_alert function) ---
def send_alert(msg):
    # ... (your send_alert implementation using TOKEN and CHAT_ID) ...
    # Remember to read TOKEN/CHAT_ID from os.environ in production/Actions
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_FALLBACK_TOKEN_FOR_LOCAL_TEST") # Example fallback
    CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "YOUR_FALLBACK_CHATID_FOR_LOCAL_TEST") # Example fallback
    if not TOKEN or not CHAT_ID or "YOUR_FALLBACK" in TOKEN:
         print("Warning: Telegram secrets not properly set.")
         # return # Optionally return here if secrets aren't set

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    print(f"Attempting to send alert: {msg[:60]}...") # Limit print length
    data = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    }
    headers = {'Connection': 'close'}
    try:
        response = requests.post(url, data=data, headers=headers, timeout=30)
        print(f"Telegram Response Status Code: {response.status_code}")
        response.raise_for_status()
        print("Alert sent successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Error sending Telegram alert: {e}")
        if hasattr(e, 'response') and e.response is not None:
             print(f"Telegram Response Body: {e.response.text}")


if __name__ == "__main__":
    print(f"Script started at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    # Get list of tuples: (alert_message, stats_dictionary)
    alerts_data = get_quakes()
    print(f"Alerts found: {len(alerts_data)}")

    if not alerts_data:
        print("No relevant earthquakes found matching criteria.")
    else:
        # --- Example: Print summary stats after finding quakes ---
        magnitudes = [stats['magnitude'] for msg, stats in alerts_data]
        distances = [stats['distance_km'] for msg, stats in alerts_data]
        if alerts_data:
             print("\n--- Summary Statistics for Alerted Quakes ---")
             print(f"  Max Magnitude: {max(magnitudes)}")
             print(f"  Avg Magnitude: {sum(magnitudes)/len(magnitudes):.2f}")
             print(f"  Closest Distance: {min(distances)} km")
             print(f"  Average Distance: {sum(distances)/len(distances):.1f} km")
             # Add more summary stats here if needed
             print("-------------------------------------------")

        # Send the alerts
        for alert_msg, event_stats_dict in alerts_data:
            # You could potentially use more data from event_stats_dict here
            # before sending, or decide *not* to send based on some stat.
            send_alert(alert_msg)
            # Optional delay
            # import time
            # time.sleep(1)

    print("Script finished.")
import matplotlib.pyplot as plt
import numpy as np
from obspy import UTCDateTime
from obspy.clients.fdsn import Client

# Define time range for the seismogram
start_time = UTCDateTime("2025-04-19T06:48:10")  # Modify as needed
duration = 5600  # Duration in seconds (2 minutes)


# Station information
network = "TJ"      # Network code
station = "GHARM"   # Station code
location = "*"      # Location code (wildcard)
channel = "HHZ"     # Vertical component channel (Z)

# Connect to IRIS data center
client = Client("IRIS")

try:
    # Fetch waveform data
    print(f"Fetching data for {station} from {start_time} for {duration} seconds...")
    st = client.get_waveforms(network, station, location, channel, 
                             start_time, start_time + duration)
    # Basic processing
    st.detrend("linear")
    st.filter("bandpass", freqmin=0.1, freqmax=10)
    
    # Plot the seismogram
    plt.figure(figsize=(12, 6), facecolor='black')
    plt.style.use('dark_background')
    
    for tr in st:
        time = np.linspace(0, tr.stats.endtime - tr.stats.starttime, tr.stats.npts)
        plt.plot(time, tr.data, 'w-', linewidth=0.8)
        
    plt.title(f"Seismogram - Station: {station}_{network}, Vertical Component")
    plt.xlabel("Time (seconds) since " + start_time.strftime("%Y-%m-%d %H:%M:%S"))
    plt.ylabel("Amplitude", color='white')
    plt.grid(True, linestyle='--', alpha=0.3, color='#555555')
    
    # Add model pick markers if available
    # model_pick_time = ... # Add your model pick time here
    # plt.axvline(x=model_pick_time, color='r', linestyle='--', label='Model Pick')

    ax = plt.gca()
    ax.spines['bottom'].set_color('white')
    ax.spines['top'].set_color('white') 
    ax.spines['right'].set_color('white')
    ax.spines['left'].set_color('white')
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    
    plt.tight_layout()
    plt.savefig(f"seismogram_{station}_{start_time.date}.png", dpi=300, facecolor='black')
    plt.show()
    
except Exception as e:
    print(f"Error: {e}")
    print("Possible issues:")
    print("- Station code may be incorrect")
    print("- Data might not be available for the specified time range")
    print("- Network connectivity problems")
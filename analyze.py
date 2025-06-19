import matplotlib.pyplot as plt
import numpy as np
from obspy import UTCDateTime
from obspy.clients.fdsn import Client

def fetch_waveform(client, network, station, location, channel, start_time, duration):
    print(f"Fetching data for {station} from {start_time} for {duration} seconds...")
    st = client.get_waveforms(network, station, location, channel, 
                             start_time, start_time + duration)
    return st

def preprocess_stream(st, freqmin=0.5, freqmax=8):
    st.detrend("linear")
    st.taper(max_percentage=0.05)
    st.filter("bandpass", freqmin=freqmin, freqmax=freqmax, corners=4, zerophase=True)
    return st

def plot_seismogram(st, station, network, start_time):
    # Create a figure with two subplots stacked vertically
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), facecolor='black', sharex=True)
    plt.style.use('dark_background')
    
    # Plot waveform on the top subplot
    for tr in st:
        time = np.linspace(0, tr.stats.endtime - tr.stats.starttime, tr.stats.npts)
        ax1.plot(time, tr.data, color='cyan', linewidth=1.5, alpha=0.85, label=f"{tr.id}")
    
    ax1.set_title(f"Seismogram - Station: {station}_{network}, Vertical Component", color='white', fontsize=16)
    ax1.set_ylabel("Amplitude", color='white', fontsize=13)
    ax1.grid(True, linestyle='--', alpha=0.4, color='#888888')
    ax1.tick_params(axis='x', colors='white')
    ax1.tick_params(axis='y', colors='white')
    ax1.legend(loc='upper right', fontsize=10)
    
    # Add spectrogram to the bottom subplot
    for tr in st:
        # Create spectrogram using matplotlib
        spec, freqs, t, im = ax2.specgram(tr.data, NFFT=256, Fs=tr.stats.sampling_rate,
                                         noverlap=128, cmap='viridis', 
                                         scale='dB', vmin=-80, vmax=0)
    
    ax2.set_xlabel("Time (seconds) since " + start_time.strftime("%Y-%m-%d %H:%M:%S"), color='white', fontsize=13)
    ax2.set_ylabel("Frequency (Hz)", color='white', fontsize=13)
    ax2.set_title("Spectrogram", color='white', fontsize=16)
    ax2.tick_params(axis='x', colors='white')
    ax2.tick_params(axis='y', colors='white')
    
    # Add a colorbar for the spectrogram
    cbar = plt.colorbar(im, ax=ax2)
    cbar.set_label('Power (dB)', color='white', fontsize=12)
    cbar.ax.yaxis.set_tick_params(color='white')
    plt.setp(plt.getp(cbar.ax, 'yticklabels'), color='white')
    
    # Set spine colors for both plots
    for ax in [ax1, ax2]:
        ax.spines['bottom'].set_color('white')
        ax.spines['top'].set_color('white') 
        ax.spines['right'].set_color('white')
        ax.spines['left'].set_color('white')
    
    plt.tight_layout()
    plt.subplots_adjust(hspace=0.3)  # Adjust space between subplots
    plt.show()

def main():
    # Parameters
    start_time = UTCDateTime("2025-06-19T19:34:10")
    duration = 5*60
    network = "GE"
    station = "KBU"
    location = "*"
    channel = "BHZ"
    client = Client("IRIS")
    try:
        st = fetch_waveform(client, network, station, location, channel, start_time, duration)
        st = preprocess_stream(st, freqmin=0.5, freqmax=8)
        plot_seismogram(st, station, network, start_time)
    except Exception as e:
        print(f"Error: {e}")
        print("Possible issues:")
        print("- Station code may be incorrect")
        print("- Data might not be available for the specified time range")
        print("- Network connectivity problems")

if __name__ == "__main__":
    main()

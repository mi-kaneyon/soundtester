import os
import sys
import sounddevice as sd
import numpy as np
import matplotlib
# Set the matplotlib backend to 'Agg' to prevent using GUI backends like Qt
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
import contextlib
from datetime import datetime

# Suppress UserWarnings about missing glyphs in matplotlib
warnings.filterwarnings("ignore", category=UserWarning, module='matplotlib.font_manager')

# Audio settings
RATE = 44100          # Sampling rate
DURATION = 30         # Duration in seconds
FREQUENCY = 1000      # Frequency in Hz
CHANNELS = 1          # Number of channels (1 for mono)

# Generate a sine wave with amplitude ±1.0
def generate_sine_wave(frequency, duration, rate):
    t = np.linspace(0, duration, int(rate * duration), endpoint=False)
    return np.sin(2 * np.pi * frequency * t)  # Amplitude set to ±1.0

# Play and record audio
def play_and_record():
    print("Generating sine wave...")
    sine_wave = generate_sine_wave(FREQUENCY, DURATION, RATE)
    recorded_data = np.zeros((int(RATE * DURATION), CHANNELS))

    # Callback function for playback and recording
    def callback(in_data, out_data, frames, time_info, status):
        start = callback.frame
        end = start + frames

        # Processing playback data
        if start >= len(sine_wave):
            # If no more playback data, fill out_data with zeros
            out_data[:] = np.zeros((frames, CHANNELS))
        else:
            frames_to_copy = min(len(sine_wave) - start, frames)
            out_data[:frames_to_copy] = sine_wave[start:start+frames_to_copy].reshape(-1, CHANNELS)
            if frames_to_copy < frames:
                out_data[frames_to_copy:] = np.zeros((frames - frames_to_copy, CHANNELS))

        # Processing recording data
        frames_to_copy = min(len(recorded_data) - start, frames)
        if frames_to_copy > 0:
            recorded_chunk = np.frombuffer(in_data, dtype=np.float32).reshape(-1, CHANNELS)
            recorded_data[start:start+frames_to_copy] = recorded_chunk[:frames_to_copy]
        else:
            # If no more space to save recorded data, do nothing
            pass

        callback.frame += frames

    callback.frame = 0

    print("Starting playback and recording...")
    with sd.Stream(samplerate=RATE, channels=CHANNELS, dtype='float32', callback=callback):
        sd.sleep(int((DURATION + 0.5) * 1000))

    print("Playback and recording finished.")

    # Calculate correlation coefficients for each segment
    segment_duration = 2  # Duration of each segment in seconds
    start_time = 3        # Start time in seconds
    end_time = DURATION - segment_duration  # End time in seconds

    correlations = []
    segment_times = []

    while start_time <= end_time:
        start_sample = int(RATE * start_time)
        end_sample = int(RATE * (start_time + segment_duration))

        # Extract segments
        sine_wave_segment = sine_wave[start_sample:end_sample]
        recorded_segment = recorded_data.flatten()[start_sample:end_sample]

        # Normalize the signals
        sine_wave_segment_norm = sine_wave_segment / np.max(np.abs(sine_wave_segment))
        recorded_segment_norm = recorded_segment / np.max(np.abs(recorded_segment))

        # Scale recorded signal to match sine wave amplitude
        scaling_factor = np.max(np.abs(sine_wave_segment)) / (np.max(np.abs(recorded_segment)) + 1e-8)  # Add small value to prevent division by zero
        recorded_segment_scaled = recorded_segment * scaling_factor

        # Normalize the scaled recorded signal
        recorded_segment_scaled_norm = recorded_segment_scaled / np.max(np.abs(recorded_segment_scaled))

        # Invert the recorded signal
        recorded_segment_inverted = -recorded_segment_scaled_norm

        # Calculate the correlation coefficients
        correlation = np.corrcoef(sine_wave_segment_norm, recorded_segment_scaled_norm)[0, 1]
        correlation_inverted = np.corrcoef(sine_wave_segment_norm, recorded_segment_inverted)[0, 1]

        # Select the best correlation coefficient
        if abs(correlation) > abs(correlation_inverted):
            final_correlation = correlation
        else:
            final_correlation = correlation_inverted  # Use the inverted signal

        print(f"Segment {start_time}-{start_time + segment_duration}s: Correlation coefficient = {final_correlation:.4f}")

        correlations.append(abs(final_correlation))
        segment_times.append(start_time)

        start_time += segment_duration  # Move to the next segment

    # Calculate the average correlation coefficient
    mean_corr = np.mean(correlations)

    print(f"\nAverage Correlation Coefficient: {mean_corr:.4f}")

    # Determine overall test result
    if mean_corr > 0.6:
        print("Test Result: Sound test success!")
    else:
        print("Test Result: Sound test failed.")

    # Get current date in YYYYMMDD format
    current_date = datetime.now().strftime("%Y%m%d")

    # Plot the original sine wave and recorded signal
    plt.figure(figsize=(12, 6))

    # Original sine wave
    plt.subplot(2, 1, 1)
    time_axis = np.linspace(0, DURATION, len(sine_wave))
    plt.plot(time_axis, sine_wave, label='Original Sine Wave')
    plt.title('Original Sine Wave')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.grid(True)
    plt.legend()

    # Recorded signal
    plt.subplot(2, 1, 2)
    time_axis = np.linspace(0, DURATION, len(recorded_data))
    plt.plot(time_axis, recorded_data.flatten(), label='Recorded Signal')
    # Add vertical lines at segment boundaries
    for st in segment_times:
        plt.axvline(x=st, color='red', linestyle='--', alpha=0.7)
        plt.axvline(x=st + segment_duration, color='red', linestyle='--', alpha=0.7)
    plt.title('Recorded Signal with Segment Boundaries')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    # Save the plot to a file with the current date in the filename
    plt.savefig(f"{current_date}_original_recorded_signals.png")
    plt.close()

    # Plot the correlation coefficients for each segment
    plt.figure(figsize=(10, 5))
    plt.plot(segment_times, correlations, marker='o', linestyle='-', color='blue')
    plt.title('Correlation Coefficient for Each Segment')
    plt.xlabel('Start Time of Segment (s)')
    plt.ylabel('Absolute Correlation Coefficient')
    plt.ylim(0, 1)
    plt.grid(True)
    plt.tight_layout()
    # Save the correlation plot to a file with the current date in the filename
    plt.savefig(f"{current_date}_correlation_coefficients.png")
    plt.close()

if __name__ == "__main__":
    # Suppress stderr messages (e.g., Qt messages)
    with contextlib.redirect_stderr(open(os.devnull, 'w')):
        play_and_record()

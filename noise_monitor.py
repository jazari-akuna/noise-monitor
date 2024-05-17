import sounddevice as sd
import numpy as np
import csv
from datetime import datetime
import os
import time

# Configuration
NOISE_LEVEL_THRESHOLD = int(os.getenv('NOISE_LEVEL_THRESHOLD', -18))  # in dB
MAX_TIME_BETWEEN_NOISE = int(os.getenv('MAX_TIME_BETWEEN_NOISE', 5))  # in seconds
AVERAGING_PERIOD = 0.4  # in seconds
SAMPLE_RATE = 44100  # Sample rate in Hz

# Initialize variables
is_noise = False
noise_start_time = None
last_noise_time = None
noise_buffer = []

# Function to measure the sound level
def measure_sound(indata, frames, time, status):
    global is_noise, noise_start_time, last_noise_time, noise_buffer

    # Convert audio samples to dB
    volume_norm = 10 * np.log10(np.mean(indata**2) + 1e-10)
    current_time = datetime.now()

    if volume_norm > NOISE_LEVEL_THRESHOLD:
        noise_buffer.append(volume_norm)
        if not is_noise:
            noise_start_time = current_time
            is_noise = True
            print(f"Noise started at {noise_start_time}")  # Debug statement
        last_noise_time = current_time
        print(f"Noise detected, buffer size: {len(noise_buffer)}, level: {volume_norm:.2f} dB")  # Debug statement
    elif is_noise:
        if (current_time - last_noise_time).seconds > MAX_TIME_BETWEEN_NOISE:
            disturbance_duration = last_noise_time - noise_start_time
            if disturbance_duration.total_seconds() > 0:
                mean_noise_level = np.mean(noise_buffer)  # Use average noise level from the buffer
                log_to_csv(noise_start_time, last_noise_time, disturbance_duration, mean_noise_level)
                print(f"Logged disturbance from {noise_start_time} to {last_noise_time}, duration: {disturbance_duration}, mean level: {mean_noise_level:.1f} dB")  # Debug statement
            is_noise = False
            noise_buffer = []  # Clear the buffer
            print("Noise stopped and buffer cleared")  # Debug statement
    else:
        # Maintain a buffer only during noise periods
        if len(noise_buffer) > int(AVERAGING_PERIOD * SAMPLE_RATE / frames):
            noise_buffer.pop(0)

    print(f"Current noise level: {volume_norm:.2f} dB")  # Debug statement

# Function to log the disturbance to CSV
def log_to_csv(start_time, end_time, duration, mean_noise_level):
    with open('disturbance_log.csv', 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            start_time.strftime('%d.%m.%Y'),
            start_time.strftime('%H:%M:%S'),
            end_time.strftime('%H:%M:%S'),
            f'{int(duration.total_seconds() // 60):02}:{int(duration.total_seconds() % 60):02}',
            f'{mean_noise_level:.1f} dB'
        ])

# Main function
if __name__ == "__main__":
    # Create the CSV file and write the header if it doesn't exist
    if not os.path.isfile('disturbance_log.csv'):
        with open('disturbance_log.csv', 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['day', 'start time', 'end time', 'duration', 'mean noise level'])

    try:
        with sd.InputStream(callback=measure_sound, samplerate=SAMPLE_RATE):
            print("Monitoring noise disturbances...")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping noise monitoring...")

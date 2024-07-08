import pyaudio
import wave
import numpy as np
import os
import matplotlib.pyplot as plt

# 録音設定
FORMAT = pyaudio.paInt16
CHANNELS = 2  # デバイス情報から取得した最大チャネル数
RATE = 44100
CHUNK = 4096
RECORD_SECONDS = 10
WAVE_OUTPUT_FILENAME = "output.wav"
PLAYBACK_DEVICE_INDEX = 8
RECORDING_DEVICE_INDEX = 8
TEST_TONE_FILENAME = "test_tone.wav"

audio = pyaudio.PyAudio()

# テスト音楽ファイルの再生
print("Playing test tone...")
wf = wave.open(TEST_TONE_FILENAME, 'rb')

stream = audio.open(format=audio.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True, output_device_index=PLAYBACK_DEVICE_INDEX)

data = wf.readframes(CHUNK)

while data != b'':
    stream.write(data)
    data = wf.readframes(CHUNK)

stream.stop_stream()
stream.close()

print("Playback finished.")

# 録音開始
print("Recording...")
stream = audio.open(format=FORMAT, channels=CHANNELS,
                    rate=RATE, input=True, input_device_index=RECORDING_DEVICE_INDEX,
                    frames_per_buffer=CHUNK)

frames = []

try:
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
except IOError as e:
    print(f"Error while recording: {e}")

print("Recording finished.")

# 録音終了
stream.stop_stream()
stream.close()

# 録音データをファイルに保存（エラーが発生しても収集したデータを保存）
if frames:
    waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(audio.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()
    print("Recorded data saved to file.")
else:
    print("No data recorded.")

# ノイズレベルの解析とグラフ描画
def analyze_noise_level(wave_file, threshold):
    if not os.path.isfile(wave_file):
        print(f"File not found: {wave_file}")
        return
    
    wf = wave.open(wave_file, 'rb')
    frames = wf.readframes(-1)
    frames = np.frombuffer(frames, dtype=np.int16)
    wf.close()

    rms = np.sqrt(np.mean(frames**2))
    print(f"RMS Noise Level: {rms}")

    # SNRの計算
    signal_power = np.mean(frames**2)
    noise_power = np.var(frames)
    snr = 10 * np.log10(signal_power / noise_power)
    print(f"Signal-to-Noise Ratio (SNR): {snr} dB")

    # 波形のプロット
    plt.figure(figsize=(10, 4))
    plt.plot(frames, label="Recorded Signal")
    plt.axhline(y=threshold, color='r', linestyle='--', label="Threshold")
    plt.axhline(y=-threshold, color='r', linestyle='--')
    plt.title('Recorded Audio Waveform')
    plt.xlabel('Sample')
    plt.ylabel('Amplitude')
    plt.legend()
    plt.show()

# 録音後にノイズレベルを解析
threshold_value = 30000  # しきい値を設定（適切な値に調整してください）
analyze_noise_level(WAVE_OUTPUT_FILENAME, threshold_value)

audio.terminate()

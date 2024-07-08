import numpy as np
from scipy.io.wavfile import write

# パラメータ設定
samplerate = 44100  # 44.1kHz
duration = 10  # 10秒
frequency = 440  # A4 (440Hz)

t = np.linspace(0., duration, int(samplerate * duration))
signal = 0.5 * np.sin(2. * np.pi * frequency * t)

# 整数形式に変換
signal_int = np.int16(signal * 32767)

# 音声ファイルとして保存
write("test_tone.wav", samplerate, signal_int)

print("Sound file 'test_tone.wav' created successfully.")

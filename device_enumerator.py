import pyaudio

audio = pyaudio.PyAudio()
for i in range(audio.get_device_count()):
    device_info = audio.get_device_info_by_index(i)
    if device_info['maxInputChannels'] > 0:
        print(f"Device ID: {i} - {device_info['name']} - Channels: {device_info['maxInputChannels']}")
audio.terminate()


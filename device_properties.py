import pyaudio

def list_supported_sample_rates(device_index):
    audio = pyaudio.PyAudio()
    info = audio.get_device_info_by_index(device_index)
    supported_rates = [8000, 16000, 32000, 44100, 48000, 96000]
    print(f"Testing supported sample rates for device: {info['name']}")
    for rate in supported_rates:
        try:
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=rate,
                input=True,
                input_device_index=device_index
            )
            stream.close()
            print(f"Supported sample rate: {rate}")
        except Exception as e:
            print(f"Sample rate {rate} not supported: {e}")
    audio.terminate()

# Замените 20 на индекс вашего устройства
list_supported_sample_rates(2)

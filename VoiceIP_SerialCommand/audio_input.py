"""
audio_input.py - microphone capture only.

Responsibilities:
  * list / select input devices
  * open the microphone as 16 kHz mono 16-bit PCM (what Vosk expects)
  * hand raw audio chunks to the rest of the program through a queue

The sounddevice callback runs on a separate audio thread, so it does the bare
minimum (copy bytes into a queue). All real work happens on the main thread.
"""
import queue

import numpy as np
import sounddevice as sd

import config


class AudioInputError(Exception):
    """Raised for any microphone / audio-device problem."""


def list_input_devices():
    """Return a list of dicts describing every device that can record."""
    try:
        all_devices = sd.query_devices()
        hostapis = sd.query_hostapis()
        default_in = sd.default.device[0]
    except Exception as exc:  # PortAudio not usable at all
        raise AudioInputError(f"Cannot query audio devices: {exc}") from exc

    found = []
    for index, dev in enumerate(all_devices):
        if dev["max_input_channels"] > 0:
            found.append({
                "index": index,
                "name": dev["name"],
                "hostapi": hostapis[dev["hostapi"]]["name"],
                "default_samplerate": dev["default_samplerate"],
                "is_default": index == default_in,
            })
    return found


def print_input_devices():
    devices = list_input_devices()
    if not devices:
        print("No input devices found. Check Windows microphone settings.")
        return
    print("Available input devices:")
    for d in devices:
        mark = "  <-- default" if d["is_default"] else ""
        print(f"  [{d['index']:>2}] {d['name']}  ({d['hostapi']}, "
              f"{int(d['default_samplerate'])} Hz){mark}")
    print("\nSelect one with:  python main.py --device <index>")


def resolve_device(device):
    """Turn None / int / '3' / 'name fragment' into a PortAudio device index."""
    if device is None:
        return None
    if isinstance(device, int):
        return device
    text = str(device).strip()
    if text.isdigit():
        return int(text)
    matches = [d for d in list_input_devices() if text.lower() in d["name"].lower()]
    if not matches:
        raise AudioInputError(
            f'No input device matches "{text}". Run: python main.py --list-devices')
    return matches[0]["index"]


def chunk_rms(chunk: bytes) -> float:
    """Root-mean-square level of a raw int16 chunk (used by --mic-test)."""
    samples = np.frombuffer(chunk, dtype=np.int16).astype(np.float64)
    if samples.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(samples ** 2)))


class MicrophoneStream:
    """Continuous microphone capture. Use start()/stop() or `with`."""

    def __init__(self, device=None, sample_rate=config.SAMPLE_RATE,
                 channels=config.CHANNELS, block_size=config.BLOCK_SIZE,
                 dtype=config.DTYPE, max_queue=config.QUEUE_MAX_CHUNKS):
        self._device = device
        self._sample_rate = sample_rate
        self._channels = channels
        self._block_size = block_size
        self._dtype = dtype
        self._queue = queue.Queue(maxsize=max_queue)
        self._stream = None
        self.device_name = "unknown"
        self.dropped_chunks = 0

    # -- audio thread -------------------------------------------------------
    def _callback(self, indata, frames, time_info, status):
        try:
            self._queue.put_nowait(bytes(indata))
        except queue.Full:
            self.dropped_chunks += 1  # main thread too slow; drop, don't block

    # -- lifecycle ----------------------------------------------------------
    def start(self):
        try:
            index = resolve_device(self._device)
            sd.check_input_settings(device=index, channels=self._channels,
                                    dtype=self._dtype, samplerate=self._sample_rate)
            info = sd.query_devices(index if index is not None else sd.default.device[0])
            self.device_name = info["name"]
            self._stream = sd.RawInputStream(
                samplerate=self._sample_rate, blocksize=self._block_size,
                device=index, channels=self._channels, dtype=self._dtype,
                callback=self._callback)
            self._stream.start()
        except AudioInputError:
            raise
        except (sd.PortAudioError, ValueError, OSError) as exc:
            self._stream = None
            raise AudioInputError(
                f"Could not open the microphone: {exc}\n"
                "  - Windows Settings > Privacy & security > Microphone: allow "
                "desktop apps (and PyCharm) to use the microphone.\n"
                "  - Try another device: python main.py --list-devices") from exc

    def read(self, timeout=0.5):
        """Return the next audio chunk (bytes), or None if none arrived in time."""
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            if self._stream is not None and not self._stream.active:
                raise AudioInputError("Microphone stream stopped "
                                      "(device unplugged or disabled?).")
            return None

    def stop(self):
        """Safe to call more than once."""
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc_info):
        self.stop()
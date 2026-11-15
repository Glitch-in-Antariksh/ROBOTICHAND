"""
main.py - wires microphone -> Vosk -> classifier -> terminal output.

Run from PyCharm (right-click > Run 'main') or:  python main.py
Options:  --list-devices | --device <idx|name> | --mic-test | --show-partial

FUTURE ARDUINO HOOK: handle_command() is the single place where an accepted
command is acted on. Later, import a serial module and send
str(command.command_id) there. Nothing else needs to change.
"""
import argparse
import signal
import sys
import time
from serial_link import SerialLink
import config
from audio_input import (AudioInputError, MicrophoneStream, chunk_rms,
                         print_input_devices)
from command_classifier import CommandClassifier, Status
from speech_recognition import ModelLoadError, SpeechRecognizer

SEPARATOR = "-" * 32


def parse_args():
    p = argparse.ArgumentParser(description="Voice-controlled gripper (Python side)")
    p.add_argument("--list-devices", action="store_true", help="list microphones and exit")
    p.add_argument("--device", default=None, help="microphone index or name fragment")
    p.add_argument("--model", default=None, help="path to the Vosk model folder")
    p.add_argument("--mic-test", action="store_true", help="show mic level for 5 s and exit")
    p.add_argument("--show-partial", action="store_true", help="print live partial results")
    return p.parse_args()


def _raise_interrupt(signum, frame):
    raise KeyboardInterrupt


def spoken_list():
    names = list(config.COMMANDS)
    return ", ".join(names[:-1]) + " or " + names[-1]


def handle_command(command, serial_link):
    """Act on an accepted command."""

    print(f"Recognised command: {command.name}")
    print(f"Command ID: {command.command_id}")
    print(f"Configuration: {command.description}")
    serial_link.send_command(command.command_id)


def run_mic_test(device, seconds=5):
    print(f"Microphone test for {seconds} s - speak normally.")
    with MicrophoneStream(device=device) as mic:
        print(f"Using: {mic.device_name}")
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            chunk = mic.read(0.5)
            if chunk is None:
                continue
            level = chunk_rms(chunk)
            print(f"{level:7.0f} |{'#' * min(40, int(level / 100))}")
    print("Done. Silence should read low (<300); speech should clearly rise "
          "(roughly 800+). A flat 0 means the mic is muted/blocked.")


def listen_loop(mic, recognizer, classifier, show_partial, serial_link):
    last_name, last_time = None, 0.0
    while True:
        chunk = mic.read(timeout=0.5)
        if chunk is None:
            continue
        result = recognizer.feed(chunk)
        if result is None:
            continue

        if not result.is_final:                       # partial: display only
            if show_partial:
                print(f"  (hearing: {result.text})")
            continue

        outcome = classifier.classify(result.text, result.word_confidences)
        if outcome.status is Status.NO_SPEECH:        # silence / noise
            continue

        print(f'User says: "{result.text}"\n')
        if outcome.status is Status.NOT_RECOGNISED:
            print("Command not recognised.")
            print(f"Please say {spoken_list()}.")
        else:
            now = time.monotonic()
            cmd = outcome.command
            if (cmd.name == last_name and
                    now - last_time < config.REPEAT_COOLDOWN_SECONDS):
                print(f"Repeated {cmd.name} ignored "
                      f"(within {config.REPEAT_COOLDOWN_SECONDS:g} s).")
            else:
                handle_command(cmd, serial_link)
                last_name, last_time = cmd.name, now
        print(f"\n{SEPARATOR}\n")


def main():
    args = parse_args()
    device = args.device if args.device is not None else config.AUDIO_DEVICE
    model_dir = args.model or config.MODEL_DIR

    # Windows: PyCharm's Stop button sends Ctrl+Break; treat it like Ctrl+C.
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, _raise_interrupt)

    try:
        if args.list_devices:
            print_input_devices()
            return 0
        if args.mic_test:
            run_mic_test(device)
            return 0
    except AudioInputError as exc:
        print(f"Microphone error: {exc}")
        return 3
    except KeyboardInterrupt:
        return 0

    print("VOICE-CONTROLLED ROBOTIC GRIPPER")
    print(SEPARATOR)

    classifier = CommandClassifier(config.COMMANDS, config.FILLER_WORDS,
                                   config.MIN_CONFIDENCE, config.MAX_COMMAND_WORDS)
    try:
        recognizer = SpeechRecognizer(
            model_dir, config.SAMPLE_RATE,
            vocabulary=classifier.vocabulary() if config.USE_GRAMMAR else None)
    except ModelLoadError as exc:
        print(f"Model error: {exc}")
        return 2
    print("Speech recognition initialised.")
    serial_link = SerialLink(port="COM3", baudrate=9600)

    if not serial_link.connect():
        print("Could not connect to Arduino. Check the USB cable and COM port.")
        return 4

    mic = MicrophoneStream(device=device)
    try:
        mic.start()
    except AudioInputError as exc:
        print(f"Microphone error: {exc}")
        return 3
    print(f"Microphone connected: {mic.device_name}")
    print("Listening for commands...  (Ctrl+C to stop)\n")

    exit_code = 0
    try:
        listen_loop(
            mic,
            recognizer,
            classifier,
            args.show_partial or config.SHOW_PARTIAL,
            serial_link
        )
    except KeyboardInterrupt:
        print("\nStopping...")
    except AudioInputError as exc:
        print(f"\nMicrophone error: {exc}")
        exit_code = 3
    finally:
        mic.stop()
        serial_link.close()
        print("Shutdown complete.")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
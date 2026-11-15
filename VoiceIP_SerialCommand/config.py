"""
config.py - every tunable parameter lives here.

Nothing in this file talks to hardware or loads libraries, so it is safe to
import from any module.
"""
from pathlib import Path

# ----------------------------------------------------------------------------
# Paths (pathlib keeps Windows backslashes/spaces out of our way)
# ----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models" / "vosk-model"

# ----------------------------------------------------------------------------
# Audio capture. Vosk small models are trained on 16 kHz mono 16-bit PCM.
# ----------------------------------------------------------------------------
SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "int16"
BLOCK_SIZE = 4000          # frames per chunk -> 4000 / 16000 = 0.25 s
QUEUE_MAX_CHUNKS = 100     # ~25 s of audio buffered before chunks are dropped

# None = Windows default input device. Or set an index (e.g. 1) or a name
# fragment (e.g. "Microphone Array"). Run `python main.py --list-devices`.
AUDIO_DEVICE = None

# ----------------------------------------------------------------------------
# Commands. "id" is what will later be sent to the Arduino over serial.
# "aliases" are the spoken words that map to the command (lower case).
# ----------------------------------------------------------------------------
COMMANDS = {
    "OPEN":  {"id": 1, "description": "Open gripper",         "aliases": ["open"]},
    "GRIP":  {"id": 2, "description": "Grip an object",       "aliases": ["grip"]},
    "POINT": {"id": 3, "description": "Pointing configuration", "aliases": ["point"]},
}

# Harmless words that may accompany a command ("open please", "grip now").
# Any other word in the utterance causes it to be rejected.
FILLER_WORDS = {"please", "now", "the"}

# ----------------------------------------------------------------------------
# Recognition / classification behaviour
# ----------------------------------------------------------------------------
# Restrict Vosk to the command vocabulary (+ fillers + [unk]). Much more
# reliable than free dictation for a 3-word demo; unrelated speech becomes
# [unk] and is rejected.
USE_GRAMMAR = True

# Per-word confidence Vosk must report for the command word (0.0 - 1.0).
# Raise if noise triggers commands; lower if real commands get rejected.
MIN_CONFIDENCE = 0.60

# Longest utterance (in words) that may still count as a command.
MAX_COMMAND_WORDS = 3

# Ignore the SAME command if it is accepted again within this many seconds.
# 0 disables. (Different commands are never suppressed.)
REPEAT_COOLDOWN_SECONDS = 1.0

# Print live partial results (for debugging only; partials never trigger).
SHOW_PARTIAL = False
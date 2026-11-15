"""
speech_recognition.py - offline speech-to-text with Vosk.

Responsibilities:
  * locate and load the local Vosk model
  * accept raw audio chunks and return recognition results
  * separate PARTIAL results (live guess, still changing) from FINAL results
    (utterance finished). Only final results are ever acted on.

Note: this file shares its name with the PyPI package "SpeechRecognition".
That package is not used here; do not `pip install SpeechRecognition` in this
project's environment.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path

from vosk import KaldiRecognizer, Model, SetLogLevel


class ModelLoadError(Exception):
    """Raised when the Vosk model is missing or cannot be loaded."""


@dataclass
class RecognitionResult:
    is_final: bool
    text: str
    # [(word, confidence), ...] - only filled for final results
    word_confidences: list = field(default_factory=list)


def _looks_like_model(path: Path) -> bool:
    return (path / "am").is_dir() and (path / "conf").is_dir()


def find_model_root(model_dir: Path):
    """
    Accept either the model folder itself or a folder that contains it
    (Windows extraction often creates models/vosk-model/vosk-model-small-.../).
    """
    model_dir = Path(model_dir)
    if not model_dir.is_dir():
        return None
    if _looks_like_model(model_dir):
        return model_dir
    for child in sorted(model_dir.iterdir()):
        if child.is_dir() and _looks_like_model(child):
            return child
    return None


class SpeechRecognizer:
    def __init__(self, model_dir, sample_rate, vocabulary=None):
        """
        vocabulary: optional list of words. If given, recognition is restricted
        to these words plus "[unk]" (Vosk grammar mode).
        """
        root = find_model_root(model_dir)
        if root is None:
            raise ModelLoadError(
                f"Vosk model not found in:\n  {model_dir}\n"
                "Download vosk-model-small-en-us-0.15 and extract it so that\n"
                "  models/vosk-model/am, conf, graph ... exist (see README.md).")

        SetLogLevel(-1)  # silence Kaldi's very verbose logging
        try:
            self._model = Model(str(root))
            if vocabulary:
                grammar = json.dumps(sorted(set(vocabulary)) + ["[unk]"])
                self._rec = KaldiRecognizer(self._model, sample_rate, grammar)
            else:
                self._rec = KaldiRecognizer(self._model, sample_rate)
            self._rec.SetWords(True)  # include per-word confidence
        except Exception as exc:
            raise ModelLoadError(f"Failed to load Vosk model at {root}: {exc}") from exc

        self._last_partial = ""

    def feed(self, chunk: bytes):
        """
        Process one audio chunk.
        Returns:
          RecognitionResult(is_final=True)  - an utterance just finished
                                              (text may be "" for silence/noise)
          RecognitionResult(is_final=False) - partial text, only when it changed
          None                              - nothing new
        Vosk's AcceptWaveform() returns True exactly once per finished
        utterance, so a final result is never produced twice.
        """
        if self._rec.AcceptWaveform(chunk):
            data = json.loads(self._rec.Result())
            self._last_partial = ""
            words = [(w.get("word", ""), float(w.get("conf", 1.0)))
                     for w in data.get("result", [])]
            return RecognitionResult(True, data.get("text", "").strip(), words)

        partial = json.loads(self._rec.PartialResult()).get("partial", "").strip()
        if partial != self._last_partial:
            self._last_partial = partial
            if partial:
                return RecognitionResult(False, partial)
        return None

    def reset(self):
        self._rec.Reset()
        self._last_partial = ""
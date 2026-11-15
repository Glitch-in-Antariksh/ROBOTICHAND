"""
command_classifier.py - turn recognised text into a command (or reject it).

Pure Python: no audio, no Vosk, no hardware. That makes it easy to test
(see test_classifier.py) and to reuse.

Matching rules (all must hold for an utterance to count as a command):
  1. After removing filler words ("please", "now", "the"), every remaining
     word must be a known command word. One stray word => reject.
  2. All command words must map to the SAME command ("open grip" => reject).
  3. The utterance may not exceed MAX_COMMAND_WORDS words.
  4. Each command word's recognition confidence must be >= MIN_CONFIDENCE.
So "please open" works, but "can you open the door" and "opening" do not.
"""
import re
from dataclasses import dataclass
from enum import Enum

_TOKEN = re.compile(r"\[unk\]|[a-z']+")


class Status(Enum):
    MATCHED = "matched"
    NO_SPEECH = "no_speech"            # empty text (silence / noise)
    NOT_RECOGNISED = "not_recognised"  # speech, but not a valid command


@dataclass(frozen=True)
class Command:
    name: str
    command_id: int
    description: str


@dataclass
class ClassificationResult:
    status: Status
    command: Command = None
    text: str = ""
    reason: str = ""


class CommandClassifier:
    def __init__(self, commands: dict, filler_words=(), min_confidence=0.0,
                 max_words=3):
        self.commands = {}
        self._alias_to_name = {}
        seen_ids = set()
        for name, spec in commands.items():
            if spec["id"] in seen_ids:
                raise ValueError(f"Duplicate command id {spec['id']}")
            seen_ids.add(spec["id"])
            self.commands[name] = Command(name, spec["id"], spec["description"])
            for alias in spec["aliases"]:
                alias = alias.lower()
                if alias in self._alias_to_name:
                    raise ValueError(f"Alias '{alias}' used by two commands")
                self._alias_to_name[alias] = name
        self._fillers = {w.lower() for w in filler_words}
        self._min_conf = min_confidence
        self._max_words = max_words

    def vocabulary(self):
        """Words the speech engine should listen for."""
        return sorted(set(self._alias_to_name) | self._fillers)

    def classify(self, text, word_confidences=None) -> ClassificationResult:
        tokens = _TOKEN.findall((text or "").lower())
        if not tokens:
            return ClassificationResult(Status.NO_SPEECH, text=text or "")

        def reject(reason):
            return ClassificationResult(Status.NOT_RECOGNISED, text=text, reason=reason)

        if len(tokens) > self._max_words:
            return reject("too many words")

        content = [t for t in tokens if t not in self._fillers]
        if not content:
            return reject("only filler words")
        if any(t not in self._alias_to_name for t in content):
            return reject("contains words that are not commands")

        names = {self._alias_to_name[t] for t in content}
        if len(names) > 1:
            return reject("ambiguous: more than one command")

        if word_confidences:
            for word, conf in word_confidences:
                if word in self._alias_to_name and conf < self._min_conf:
                    return reject(f"low confidence ({conf:.2f})")

        return ClassificationResult(Status.MATCHED,
                                    command=self.commands[names.pop()], text=text)
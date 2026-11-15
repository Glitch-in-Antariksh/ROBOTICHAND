"""Offline self-test of the classifier. No microphone or model needed.
Run:  python test_classifier.py"""
import config
from command_classifier import CommandClassifier, Status

c = CommandClassifier(config.COMMANDS, config.FILLER_WORDS,
                      config.MIN_CONFIDENCE, config.MAX_COMMAND_WORDS)

# (text, confidences, expected command name or None)
CASES = [
    ("open", None, "OPEN"), ("grip", None, "GRIP"), ("point", None, "POINT"),
    ("Open.", None, "OPEN"), ("please open", None, "OPEN"), ("grip now", None, "GRIP"),
    ("open open", None, "OPEN"),
    ("", None, None), ("   ", None, None),
    ("[unk]", None, None), ("open [unk]", None, None),
    ("open grip", None, None), ("hello there", None, None),
    ("can you open the door please", None, None), ("opening", None, None),
    ("the", None, None), ("please", None, None),
    ("open", [("open", 0.30)], None),
    ("open", [("open", 0.95)], "OPEN"),
]

failed = 0
for text, conf, expected in CASES:
    r = c.classify(text, conf)
    got = r.command.name if r.status is Status.MATCHED else None
    ok = got == expected
    failed += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {text!r:34} -> {got}")
print(f"\n{len(CASES) - failed}/{len(CASES)} passed")
raise SystemExit(1 if failed else 0)
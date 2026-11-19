#v1.1 Save/Load

import hashlib
import json

from pathlib import Path

SALT = "SALT_42"

def _sign(payload):
    return hashlib.sha256((payload + SALT).encode()).hexdigest()

class Persistence:
    @staticmethod
    def load_high_scores(path, difficulties, limit):
        scores = {d: [] for d in difficulties}

        # A missing, unreadable or corrupt file just means no highscores yet
        try:
            content = Path(path).read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            return scores
        if len(content) < 2:
            return scores

        payload = "\n".join(content[:-1])
        sig = content[-1]

        if _sign(payload) != sig:
            return scores

        for line in payload.splitlines():
            try:
                diff, score, name = line.split(",")
                score = int(score)
            except ValueError:
                continue        # skip a broken line, keep the rest
            if diff in scores:
                scores[diff].append((score, name))

        for diff in scores:
            scores[diff].sort(reverse=True)
            scores[diff] = scores[diff][:limit]

        return scores

    @staticmethod
    def save_high_scores(path, high_scores):
        lines = []
        for diff, entries in high_scores.items():
            for score, name in entries:
                lines.append(f"{diff},{score},{name}")

        payload = "\n".join(lines)
        sig = _sign(payload)

        with open(path, "w", encoding="utf-8") as f:
            f.write(payload + "\n")
            f.write(sig)

    @staticmethod
    def load_preferences(path):
        """Saved player settings as a dict; {} when the file is missing or broken."""
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    @staticmethod
    def save_preferences(path, preferences):
        Path(path).write_text(json.dumps(preferences, indent=2), encoding="utf-8")
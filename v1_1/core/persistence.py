#v1.1 Save/Load

import hashlib

from pathlib import Path

SALT = "SALT_42"

def _sign(payload):
    return hashlib.sha256((payload + SALT).encode()).hexdigest()

class Persistence:
    @staticmethod
    def load_high_scores(path, difficulties, limit):
        scores = {d: [] for d in difficulties}
        path = Path(path)

        if not path.exists():
            return scores

        content = path.read_text(encoding="utf-8").splitlines()
        if len(content) < 2:
            return scores

        payload = "\n".join(content[:-1])
        sig = content[-1]

        if _sign(payload) != sig:
            return scores

        for line in payload.splitlines():
            diff, score, name = line.split(",")
            if diff in scores:
                scores[diff].append((int(score), name))

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

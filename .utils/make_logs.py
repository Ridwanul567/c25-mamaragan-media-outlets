"""Creates a "code_review" directory and ensures that "report.txt" and "report.json" exist."""

import os


def init_logs():
    os.makedirs("code_review", exist_ok=True)
    for filename in ["report.txt", "report.json"]:
        path = os.path.join("code_review", filename)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write("")


if __name__ == "__main__":
    init_logs()

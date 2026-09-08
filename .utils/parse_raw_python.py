"""Parses the raw Pylint report from 'code_review/report.txt'
and writes the average score to 'code_review/report.json'."""

import json
import re
import os


def parse_pylint_report():
    report_path = os.path.join("code_review", "report.txt")
    json_path = os.path.join("code_review", "report.json")

    score = 0.0
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Match standard Pylint output pattern: "Your code has been rated at X.XX/10"
            match = re.search(r"rated at (-?\d+\.\d+)/10", content)
            if match:
                score = float(match.group(1))

    # Clamp scores below 0 to 0.0 for badge consistency
    score = max(0.0, score)

    data = {"average_score": round(score, 2)}
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    parse_pylint_report()

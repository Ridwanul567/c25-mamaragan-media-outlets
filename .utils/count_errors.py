"""Counts the number of Pylint errors and fatal messages in 'code_review/report.txt'."""

import os
import re


def count_errors():
    report_path = os.path.join("code_review", "report.txt")
    error_count = 0
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            for line in f:
                # Count Pylint Error (E) and Fatal (F) message codes
                if re.search(r":\s*[EF]\d{4}:", line):
                    error_count += 1
    print(error_count)


if __name__ == "__main__":
    count_errors()

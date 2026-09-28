"""
clean_schemes.py

Cleans an EXISTING schemes.json produced by extract_schemes.py:
  1. Fixes text encoding mojibake (e.g. â€œ -> ", â‚¹ -> ₹, ï»¿ -> removed)
  2. Removes the duplicate scheme card + website footer junk that gets
     appended after "Sources And References" in every field

USAGE:
    pip install ftfy --break-system-packages
    python clean_schemes.py --input schemes.json --output schemes_clean.json
"""

import argparse
import json
import re

try:
    import ftfy
    HAS_FTFY = True
except ImportError:
    HAS_FTFY = False

# Fallback manual fixes if ftfy isn't installed
MANUAL_FIXES = {
    "â€œ": '"', "â€\x9d": '"', "â€​": '"',
    "â€™": "'", "â€˜": "'",
    "â€“": "–", "â€”": "—",
    "â‚¹": "₹",
    "ï»¿": "",
    "Â©": "©",
    "Â®": "®",
    "Â​": "",
}

# Markers where real content ends and duplicate/footer junk begins.
# We cut the text at the FIRST occurrence of any of these.
CUTOFF_MARKERS = [
    "Sources And References",
    "Sources and References",
]


def fix_encoding(text: str) -> str:
    if not text:
        return text
    if HAS_FTFY:
        text = ftfy.fix_text(text)
    for bad, good in MANUAL_FIXES.items():
        text = text.replace(bad, good)
    return text


def strip_trailing_junk(text: str) -> str:
    """Cut text at the first occurrence of a known trailing-junk marker."""
    if not text:
        return text
    earliest = len(text)
    for marker in CUTOFF_MARKERS:
        idx = text.find(marker)
        if idx != -1 and idx < earliest:
            earliest = idx
    return text[:earliest].strip(" .")


def clean_scheme(scheme: dict) -> dict:
    cleaned = {}
    for key, value in scheme.items():
        if isinstance(value, str):
            value = fix_encoding(value)
            # Only strip trailing junk from long free-text fields
            if key in ("details", "benefits", "eligibility",
                        "application_process", "documents_required", "faqs"):
                value = strip_trailing_junk(value)
        cleaned[key] = value
    return cleaned


def main():
    parser = argparse.ArgumentParser(description="Clean an existing schemes.json file")
    parser.add_argument("--input", required=True, help="Path to raw schemes.json")
    parser.add_argument("--output", default="schemes_clean.json", help="Path for cleaned output")
    args = parser.parse_args()

    if not HAS_FTFY:
        print("NOTE: ftfy not installed — using manual fallback fixes only.")
        print("For best results run: pip install ftfy --break-system-packages\n")

    with open(args.input, "r", encoding="utf-8") as f:
        schemes = json.load(f)

    cleaned_schemes = [clean_scheme(s) for s in schemes]

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(cleaned_schemes, f, indent=2, ensure_ascii=False)

    print(f"Cleaned {len(cleaned_schemes)} schemes -> {args.output}")


if __name__ == "__main__":
    main()

"""
extract_schemes.py

Extracts and structures Indian government scheme data from the
gov_myscheme PDF dataset (shrijayan/gov_myscheme on Hugging Face)
into clean JSON, ready to feed into a RAG pipeline.

USAGE:
    1. Download all PDFs from:
       https://huggingface.co/datasets/shrijayan/gov_myscheme
       into a local folder, e.g. ./text_data/

    2. Install dependencies:
       pip install pdfplumber --break-system-packages

    3. Run:
       python extract_schemes.py --input ./text_data --output schemes.json

OUTPUT FORMAT (one JSON object per scheme):
{
    "file": "aavy.pdf",
    "scheme_name": "Atal Awasiya Vidyala Yojana",
    "state_or_ministry": "Uttar Pradesh",
    "details": "...",
    "benefits": "...",
    "eligibility": "...",
    "application_process": "...",
    "documents_required": "...",
    "faqs": "..."
}
"""

import argparse
import json
import re
from pathlib import Path

import pdfplumber

# Known noise phrases that appear in every scraped page (website chrome, not scheme content)
NOISE_PATTERNS = [
    r"Are you sure you want to sign out\?",
    r"Cancel",
    r"Sign\s*Out",
    r"Eng\s*English/[^\s]+",
    r"Sign\s*In",
    r"Back",
    r"Something went wrong\. Please try again later\.",
    r"Ok",
    r"You need to sign in before applying for schemes",
    r"It seems you have already initiated your application earlier\.",
    r"To know more please visit",
    r"Apply Now",
    r"Check Eligibility",
    r"Was this helpful\?",
    r"News and Updates",
    r"No new news and updates available",
    r"Share",
    r"Â©\d{4}.*?v-\d+\.\d+\.\d+",  # footer block (copyright ... version number)
]

# The section headers that repeat in every scheme document
SECTIONS = [
    "Details",
    "Benefits",
    "Eligibility",
    "Application Process",
    "Documents Required",
    "Frequently Asked Questions",
]


def clean_text(text: str) -> str:
    """Remove repeated website UI noise from raw extracted PDF text."""
    for pattern in NOISE_PATTERNS:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_sections(text: str) -> dict:
    """
    Split cleaned text into sections based on known headers.
    The PDFs repeat headers twice (nav menu + actual section) —
    we take the SECOND occurrence of each header as the real split point.
    """
    # Find all header positions (case-sensitive match on exact header text)
    positions = []
    for header in SECTIONS:
        matches = [m.start() for m in re.finditer(re.escape(header), text)]
        if len(matches) >= 2:
            positions.append((matches[1], header))  # second occurrence = real section
        elif len(matches) == 1:
            positions.append((matches[0], header))

    positions.sort()

    result = {}
    for i, (pos, header) in enumerate(positions):
        start = pos + len(header)
        end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
        result[header] = text[start:end].strip(" .")

    return result


def extract_scheme_name(text: str) -> str:
    """Scheme name is typically the very first words of the PDF, before 'Are you sure...'."""
    match = re.match(r"^(.*?)(Are you sure|Details|Benefits)", text)
    if match:
        return match.group(1).strip()
    return "Unknown Scheme"


# All Indian states + union territories, longest first so e.g. "Andhra Pradesh"
# is matched before "Andhra" and "West Bengal" before "Bengal".
STATES_AND_UTS = sorted([
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Jammu and Kashmir",
    "Ladakh", "Lakshadweep", "Puducherry",
], key=len, reverse=True)


def extract_state_or_ministry(text: str, scheme_name: str) -> str:
    """
    Identify which state/UT or central ministry a scheme belongs to.

    On myScheme pages the jurisdiction appears immediately before the scheme
    name in the page body (e.g. "LakshadweepAtal Awasiya Vidyala Yojana" or
    "Ministry of EducationAICTE - Grant..."), so we look for the text that
    directly precedes an occurrence of the scheme name.
    """
    if scheme_name and scheme_name != "Unknown Scheme":
        # Look at occurrences of the scheme name after the first (the first is
        # the PDF title; later ones sit in the body, preceded by jurisdiction).
        occurrences = [m.start() for m in re.finditer(re.escape(scheme_name), text)]
        for pos in occurrences[1:]:
            preceding = text[max(0, pos - 120):pos]

            # A central ministry/department label
            ministry = re.search(
                r"((?:Ministry|Department)\s+of\s+[A-Za-z,&\s]+?)$",
                preceding.strip(),
            )
            if ministry:
                return ministry.group(1).strip(" ,&")

            # A state or union territory name
            for state in STATES_AND_UTS:
                if preceding.rstrip().endswith(state):
                    return state

    # Fallback: first state/ministry mentioned anywhere in the document
    ministry = re.search(r"(?:Ministry|Department)\s+of\s+[A-Za-z,&\s]{3,40}", text)
    for state in STATES_AND_UTS:
        if re.search(r"\b" + re.escape(state) + r"\b", text):
            return state
    if ministry:
        return ministry.group(0).strip(" ,&")

    return "Unknown"


def process_pdf(pdf_path: Path) -> dict:
    with pdfplumber.open(pdf_path) as pdf:
        raw_text = " ".join(page.extract_text() or "" for page in pdf.pages)

    scheme_name = extract_scheme_name(raw_text)
    state_or_ministry = extract_state_or_ministry(raw_text, scheme_name)
    cleaned = clean_text(raw_text)
    sections = split_sections(cleaned)

    return {
        "file": pdf_path.name,
        "scheme_name": scheme_name,
        "state_or_ministry": state_or_ministry,
        "details": sections.get("Details", ""),
        "benefits": sections.get("Benefits", ""),
        "eligibility": sections.get("Eligibility", ""),
        "application_process": sections.get("Application Process", ""),
        "documents_required": sections.get("Documents Required", ""),
        "faqs": sections.get("Frequently Asked Questions", ""),
    }


def main():
    parser = argparse.ArgumentParser(description="Extract structured scheme data from PDFs")
    parser.add_argument("--input", required=True, help="Folder containing scheme PDFs")
    parser.add_argument("--output", default="schemes.json", help="Output JSON file path")
    args = parser.parse_args()

    input_dir = Path(args.input)
    pdf_files = sorted(input_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {input_dir}")
        return

    results = []
    for i, pdf_path in enumerate(pdf_files, 1):
        try:
            scheme_data = process_pdf(pdf_path)
            results.append(scheme_data)
            print(f"[{i}/{len(pdf_files)}] Processed: {pdf_path.name}")
        except Exception as e:
            print(f"[{i}/{len(pdf_files)}] FAILED: {pdf_path.name} — {e}")

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nDone. {len(results)} schemes written to {args.output}")


if __name__ == "__main__":
    main()

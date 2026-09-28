"""
add_missing_schemes.py

Adds critical national schemes that were missing from the myScheme
dataset (Ayushman Bharat/PMJAY, PM-Kisan) directly into your cleaned
schemes JSON, in the exact same format as everything else.

USAGE:
    python add_missing_schemes.py --input schemes_final_clean.json --output schemes_final_clean.json
"""

import argparse
import json

MISSING_SCHEMES = [
    {
        "file": "manual_ayushman_bharat_pmjay.pdf",
        "scheme_name": "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (PMJAY)",
        "state_or_ministry": "Ministry of Health and Family Welfare",
        "details": (
            "Ayushman Bharat Pradhan Mantri Jan Arogya Yojana (AB PM-JAY) is the "
            "Government of India's flagship health insurance scheme, launched to "
            "achieve Universal Health Coverage. It provides eligible families with "
            "health insurance coverage of up to Rs. 5 lakh per year for secondary and "
            "tertiary hospital care, at any empanelled public or private hospital "
            "across India. Treatment under the scheme is cashless and paperless. "
            "A special provision, the Ayushman Vay Vandana Card, extends this same "
            "Rs. 5 lakh cover to every senior citizen aged 70 years and above, "
            "regardless of their family income."
        ),
        "benefits": (
            "Health insurance cover of Rs. 5 lakh per family per year for hospital "
            "treatment. Cashless and paperless treatment at any empanelled hospital "
            "anywhere in India (the cover is fully portable across states). "
            "All senior citizens aged 70 and above get an additional Rs. 5 lakh "
            "cover for themselves through the Ayushman Vay Vandana Card, on top of "
            "any existing family cover, regardless of income."
        ),
        "eligibility": (
            "Poor and vulnerable families identified under the SECC 2011 deprivation "
            "criteria (both rural and urban) are eligible for the base scheme. "
            "Separately, all senior citizens aged 70 years or above are eligible for "
            "the Ayushman Vay Vandana Card regardless of their income or family "
            "coverage status. You can check your eligibility on the official PMJAY "
            "website using the 'Am I Eligible' tool, or through the Ayushman App."
        ),
        "application_process": (
            "Online/Offline. Step 1: Visit the official PMJAY website (pmjay.gov.in) "
            "or the Ayushman App, or go to your nearest Common Service Centre (CSC). "
            "Step 2: Check eligibility using the 'Am I Eligible' tool by entering your "
            "mobile number and state. Step 3: Complete identity verification through "
            "Aadhaar e-KYC (OTP or biometric). Step 4: For senior citizens applying "
            "through the Ayushman Vay Vandana Card, the CSC operator (Ayushman Mitra) "
            "will help complete registration on the spot. Step 5: Once approved, "
            "download or collect your Ayushman card. Show this card at any "
            "empanelled hospital to receive cashless treatment."
        ),
        "documents_required": (
            "Aadhaar card (mandatory for identity verification and e-KYC). "
            "Ration card or family ID details. Mobile number for OTP verification. "
            "For senior citizens applying under the Ayushman Vay Vandana Card, "
            "only Aadhaar card and basic family details are typically needed since "
            "age alone determines eligibility, regardless of income."
        ),
        "faqs": (
            "Is there an age-based Ayushman Bharat benefit for elderly people? "
            "Yes. Every senior citizen aged 70 and above gets Rs. 5 lakh health "
            "cover through the Ayushman Vay Vandana Card, regardless of income. "
            "Where can I use my Ayushman card? At any hospital empanelled under "
            "PMJAY, anywhere in India. Is treatment really free? Yes, treatment at "
            "empanelled hospitals under the scheme is cashless, meaning you do not "
            "pay out of pocket for covered treatments. How do I check if a hospital "
            "near me is empanelled? Visit the PMJAY website and use the hospital "
            "search tool by selecting your state and district."
        ),
    },
    {
        "file": "manual_pm_kisan.pdf",
        "scheme_name": "Pradhan Mantri Kisan Samman Nidhi Yojana (PM-Kisan)",
        "state_or_ministry": "Ministry of Agriculture and Farmers Welfare",
        "details": (
            "Pradhan Mantri Kisan Samman Nidhi Yojana (PM-Kisan) is a Central "
            "Government scheme that provides direct income support to landholding "
            "farmer families across India. Launched in February 2019, the scheme "
            "transfers money directly into farmers' bank accounts to help meet "
            "agricultural and household expenses."
        ),
        "benefits": (
            "Eligible farmer families receive Rs. 6,000 per year, paid directly into "
            "their bank account in three equal installments of Rs. 2,000 every four "
            "months, through Direct Benefit Transfer (DBT)."
        ),
        "eligibility": (
            "The farmer family (husband, wife, and minor children counted as one "
            "unit) must own cultivable agricultural land registered in their name "
            "as per state or Union Territory land records. Only one registration is "
            "permitted per family. Institutional landholders such as companies, "
            "trusts, and societies are not eligible. Completion of e-KYC and "
            "Aadhaar-bank account linking (NPCI seeding) is mandatory to receive "
            "installments."
        ),
        "application_process": (
            "Online/Offline. Step 1: Visit the official PM-Kisan portal (pmkisan.gov.in) "
            "or your nearest Common Service Centre (CSC), or use the PM Kisan mobile "
            "app. Step 2: Register using your Aadhaar number and complete OTP or "
            "biometric e-KYC verification. Step 3: Provide your land ownership "
            "records (Khata, Khasra, Jamabandi, or Patta depending on your state) "
            "and bank account details. Step 4: Ensure your Aadhaar is linked to your "
            "bank account for the money to be transferred. Step 5: Confirm and "
            "submit your registration. e-KYC must be kept up to date each year to "
            "keep receiving installments without delay."
        ),
        "documents_required": (
            "Aadhaar card (mandatory for identity verification and e-KYC). "
            "Bank account details with active savings account, preferably Aadhaar-"
            "linked, for Direct Benefit Transfer. Land ownership records showing "
            "cultivable agricultural land in your name (format varies by state, e.g. "
            "Khata, Khasra, Jamabandi, or Patta). Mobile number linked to Aadhaar for "
            "OTP verification and SMS updates on installment status."
        ),
        "faqs": (
            "How much money do farmers get under PM-Kisan? Rs. 6,000 per year, paid "
            "in three installments of Rs. 2,000 every four months. How do I check my "
            "installment status? Visit the PM-Kisan portal or app and use the "
            "beneficiary status check with your Aadhaar number. What happens if my "
            "e-KYC is not done? Payments may be delayed or stopped until e-KYC is "
            "completed. Can a family have more than one registration? No, only one "
            "registration is allowed per farmer family."
        ),
    },
]


def main():
    parser = argparse.ArgumentParser(description="Add critical missing schemes to the dataset")
    parser.add_argument("--input", required=True, help="Path to schemes_final_clean.json")
    parser.add_argument("--output", required=True, help="Path to write the updated file")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        schemes = json.load(f)

    existing_names = {s.get("scheme_name", "").strip().lower() for s in schemes}
    added = 0

    for scheme in MISSING_SCHEMES:
        if scheme["scheme_name"].strip().lower() not in existing_names:
            schemes.append(scheme)
            added += 1
        else:
            print(f"Skipped (already present): {scheme['scheme_name']}")

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(schemes, f, indent=2, ensure_ascii=False)

    print(f"\nAdded {added} new scheme(s). Total schemes now: {len(schemes)}")
    print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()

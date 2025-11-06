#!/usr/bin/env python3
"""
Script to extract certificate completion dates from PDFs and web URLs.
This script can be run to automatically update the README with certificate dates.

Requirements:
    pip install PyPDF2 requests beautifulsoup4 selenium
"""

import PyPDF2
import re
from datetime import datetime
import json
import os

# PDF Files and their descriptions
PDF_CERTIFICATES = {
    "1750612081484.pdf": {
        "description": "Pragmatic Clean Architecture - Milan Jovanović",
        "section": "Milan Jovanović - TECH"
    },
    "1750612186642 (1).pdf": {
        "description": "Modular Monolith Architecture - Milan Jovanović",
        "section": "Milan Jovanović - TECH"
    },
    "1638557969[4562].pdf": {
        "description": "Impacta, Full-Stack",
        "section": "Outros"
    },
    "Certificado Freshers -William Silva[1260].pdf": {
        "description": "MoveOn, Soft skills",
        "section": "Outros"
    },
    "certificate-introducao-a-ciencia-de-dados-30-61081f20e32fc3306067d375.pdf": {
        "description": "Ciência de Dados",
        "section": "Outros"
    }
}

# Online certificate URLs that need to be checked
ONLINE_CERTIFICATES = {
    "Balta.io": [
        "https://balta.io/certificados/a8d6e584-9226-4f37-a7d7-9db1cd7ef8b5",
        "https://balta.io/certificados/2bdb46a8-dbc1-4bae-b568-6839258bca85",
        "https://balta.io/certificados/da7aa9ce-22d1-493f-a998-c81fafb6af2e",
        "https://balta.io/certificados/df82d85a-07c3-40df-8b9f-dd223ef61bce",
        "https://balta.io/certificados/770fe2e2-5427-4645-9e77-9cf19f973e38",
        "https://balta.io/certificados/c20b8dec-8feb-4c57-ab53-6865ddd36690",
        "https://balta.io/certificados/7db012fb-f15d-4b77-8e6e-287167af16f1",
        "https://balta.io/certificados/467f4cc8-d1ff-498a-b623-8344756d8072",
        "https://balta.io/certificados/0ff6375f-8423-4eff-a707-1f2216a81781",
        "https://balta.io/certificados/0ff6375f-8423-4eff-a707-1f2216a81781",  # duplicate
        "https://balta.io/certificados/52c5f8f0-9456-4b7d-8cf9-d943f8ed74cc",
        "https://balta.io/certificados/cb75db37-029a-4d50-9eba-657c97569b29",
        "https://balta.io/certificados/d6b8aaa1-2d27-4a17-b141-fb1e571a1cdc",
        "https://baltaio.blob.core.windows.net/static/images/experience/2021/certificates/5f0dc0af-4099-7219-6c1a-a27b00000000-experience.png",
        "https://balta.io/certificados/dcaf19fc-107b-4d63-ae93-88a5abd9bcfc",
        "https://balta.io/certificados/6bf6ba8e-1330-4e54-a05a-d7e73616c7cb",
        "https://balta.io/certificados/f5574f7d-3f27-489d-9da1-624a8710519b",
    ],
    "Udemy": [
        "https://www.udemy.com/certificate/UC-da53ebdc-c097-4ab6-a507-d3d2dc452624",
        "https://www.udemy.com/certificate/UC-806cef6b-f58e-4a76-8a67-2b85537a1318",
        "https://www.udemy.com/certificate/UC-d3657a07-e389-40f8-8535-a46f98e04a7f/",
        "https://www.udemy.com/certificate/UC-f3fb4b47-54f6-41a9-bf95-4cd2566b1d82/",
        "https://www.udemy.com/certificate/UC-abec3b4d-115f-474e-bbef-b1a746f4fd0f/",
        "https://www.udemy.com/certificate/UC-6dc30584-1764-493b-88ea-6259d3c1846e/",
    ],
    "Pluralsight": [
        "https://github.com/user-attachments/assets/0bce683b-f429-42fe-b461-2a671d3dc03d",
        "https://github.com/user-attachments/assets/f622d10b-969b-43f5-bc08-ce12ecb3034c",
        "https://github.com/user-attachments/assets/7d44f38f-05c6-4af8-b36d-134c27836df9",
        "https://github.com/user-attachments/assets/61ea03cb-f67e-479b-8261-e5f528b9bcb2",
        "https://github.com/user-attachments/assets/392840e4-04f9-4949-abe5-6270d85f105a",
    ]
}


def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        print(f"Error reading {pdf_path}: {str(e)}")
        return ""


def find_dates_in_text(text):
    """Find potential dates in text using various patterns"""
    # Common date patterns
    patterns = [
        # YYYY-MM-DD
        (r'\b(\d{4}[-/]\d{1,2}[-/]\d{1,2})\b', 'iso'),
        # DD/MM/YYYY or MM/DD/YYYY
        (r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b', 'slash'),
        # Month DD, YYYY
        (r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b', 'english'),
        # DD Month YYYY (Portuguese)
        (r'\b(\d{1,2}\s+(?:de\s+)?(?:jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)[a-z]*\s+(?:de\s+)?\d{4})\b', 'portuguese'),
        # Month YYYY (Portuguese)
        (r'\b((?:Janeiro|Fevereiro|Março|Abril|Maio|Junho|Julho|Agosto|Setembro|Outubro|Novembro|Dezembro)\s+(?:de\s+)?\d{4})\b', 'portuguese_full'),
    ]
    
    all_dates = []
    for pattern, date_type in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        all_dates.extend([(match, date_type) for match in matches])
    
    return all_dates


def extract_date_from_pdf(pdf_path):
    """Extract completion date from a PDF certificate"""
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return None
    
    dates = find_dates_in_text(text)
    
    # Look for dates near completion-related keywords
    completion_keywords = [
        'date:', 'concluído', 'concluded', 'completed', 'completion',
        'graduating', 'awarded', 'issued', 'certificado'
    ]
    
    # Return the most relevant date (near completion keywords)
    text_lower = text.lower()
    for date, date_type in dates:
        for keyword in completion_keywords:
            # Check if date appears near completion keyword
            keyword_pos = text_lower.find(keyword)
            date_pos = text_lower.find(date.lower())
            if keyword_pos != -1 and date_pos != -1 and abs(keyword_pos - date_pos) < 200:
                return date
    
    # If no date found near keywords, return the last date found
    return dates[-1][0] if dates else None


def main():
    """Main function to extract all certificate dates"""
    results = {}
    
    print("=" * 70)
    print("EXTRACTING CERTIFICATE DATES FROM LOCAL PDFs")
    print("=" * 70)
    
    # Process PDF files
    for pdf_file, info in PDF_CERTIFICATES.items():
        if os.path.exists(pdf_file):
            print(f"\nProcessing: {info['description']}")
            date = extract_date_from_pdf(pdf_file)
            if date:
                print(f"  ✓ Date found: {date}")
                results[pdf_file] = {
                    'description': info['description'],
                    'date': date,
                    'section': info['section']
                }
            else:
                print(f"  ✗ No date found")
                results[pdf_file] = {
                    'description': info['description'],
                    'date': 'Not found',
                    'section': info['section']
                }
        else:
            print(f"\n✗ File not found: {pdf_file}")
    
    # Save results to JSON
    with open('certificate_dates.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    print(f"\nExtracted dates from {len(results)} PDF certificates")
    print("Results saved to: certificate_dates.json")
    
    print("\n" + "=" * 70)
    print("ONLINE CERTIFICATES (require manual verification)")
    print("=" * 70)
    for platform, urls in ONLINE_CERTIFICATES.items():
        print(f"\n{platform}: {len(urls)} certificates")
        print("  These certificates need to be accessed manually to extract dates:")
        for url in urls[:3]:  # Show first 3 as examples
            print(f"  - {url}")
        if len(urls) > 3:
            print(f"  ... and {len(urls) - 3} more")
    
    print("\n" + "=" * 70)
    print("To extract dates from online certificates, you'll need to:")
    print("1. Access each URL manually in a browser")
    print("2. Look for the completion/issue date on the certificate")
    print("3. Update the README.md with the extracted dates")
    print("=" * 70)


if __name__ == "__main__":
    main()

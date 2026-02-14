"""
Simple test script to demonstrate PDF reading functionality
"""

import sys
sys.path.append('src')

from pdf_reader import read_pdf_bank_statement, clean_pdf_data

def test_pdf_reader():
    """
    Test the PDF reader with a sample PDF file
    """
    print("=== PDF Reader Test ===")
    
    # You would replace this with your actual PDF file
    pdf_file = "your_bank_statement.pdf"
    
    print(f"Looking for PDF file: {pdf_file}")
    
    # For demonstration, let's show what the function does
    print("\nWhat the PDF reader does:")
    print("1. Opens the PDF file")
    print("2. Extracts table from first page")
    print("3. Converts to DataFrame")
    print("4. Standardizes column names")
    print("5. Cleans the data")
    
    print("\nTo use with your bank statement:")
    print("1. Save your bank statement as PDF")
    print("2. Place it in the project directory")
    print("3. Run: python main.py --file your_statement.pdf")
    
    print("\nExample usage:")
    print("python main.py --file chase_statement.pdf")
    print("python main.py --file bankofamerica_statement.pdf")

if __name__ == "__main__":
    test_pdf_reader()

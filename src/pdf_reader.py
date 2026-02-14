import pandas as pd
import pdfplumber

def read_pdf_bank_statement(pdf_path):
    """
    Simple PDF reader for bank statements
    Extracts table from first page and converts to DataFrame
    
    Args:
        pdf_path (str): Path to PDF file
        
    Returns:
        pd.DataFrame: Bank transactions in standard format
    """
    
    print(f"Opening PDF file: {pdf_path}")
    
    # Open the PDF file
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"PDF has {len(pdf.pages)} pages")
            
            # Get the first page
            first_page = pdf.pages[0]
            print("Reading first page...")
            
            # Extract table from the page
            table = first_page.extract_table()
            
            if table is None:
                print("No table found on first page")
                return None
            
            print(f"Found table with {len(table)} rows and {len(table[0])} columns")
            
            # Convert to DataFrame
            df = pd.DataFrame(table[1:], columns=table[0])  # Skip header row
            
            print("Table extracted successfully")
            print(f"Columns found: {list(df.columns)}")
            
            # Try to standardize column names
            df = standardize_columns(df)
            
            return df
            
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

def standardize_columns(df):
    """
    Standardize column names to match our expected format
    
    Args:
        df (pd.DataFrame): Raw DataFrame from PDF
        
    Returns:
        pd.DataFrame: DataFrame with standardized columns
    """
    
    print("Standardizing column names...")
    
    # Get current columns
    columns = [col.lower().strip() for col in df.columns]
    print(f"Current columns: {columns}")
    
    # Look for date column
    date_col = None
    for i, col in enumerate(columns):
        if 'date' in col or 'transaction' in col:
            date_col = i
            print(f"Found date column: {df.columns[i]}")
            break
    
    # Look for description column
    desc_col = None
    for i, col in enumerate(columns):
        if 'description' in col or 'merchant' in col or 'details' in col:
            desc_col = i
            print(f"Found description column: {df.columns[i]}")
            break
    
    # Look for amount column
    amount_col = None
    for i, col in enumerate(columns):
        if 'amount' in col or 'debit' in col or 'credit' in col or 'value' in col:
            amount_col = i
            print(f"Found amount column: {df.columns[i]}")
            break
    
    # Create standardized DataFrame
    if date_col is not None and desc_col is not None and amount_col is not None:
        print("All required columns found, creating standard format...")
        
        standard_df = pd.DataFrame({
            'Date': df.iloc[:, date_col],
            'Description': df.iloc[:, desc_col],
            'Amount': df.iloc[:, amount_col]
        })
        
        print("Standardization complete")
        return standard_df
    else:
        print("Could not find all required columns")
        print(f"Date column: {date_col}")
        print(f"Description column: {desc_col}")
        print(f"Amount column: {amount_col}")
        return df

def clean_pdf_data(df):
    """
    Clean data extracted from PDF
    
    Args:
        df (pd.DataFrame): Raw DataFrame from PDF
        
    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    
    print("Cleaning PDF data...")
    
    # Remove empty rows
    df = df.dropna(how='all')
    print(f"Dropped empty rows, {len(df)} rows remaining")
    
    # Clean amount column (remove currency symbols, convert to numeric)
    if 'Amount' in df.columns:
        print("Cleaning amount column...")
        df['Amount'] = df['Amount'].astype(str).str.replace('$', '').str.replace(',', '')
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        print("Amount column cleaned")
    
    # Clean description column
    if 'Description' in df.columns:
        print("Cleaning description column...")
        df['Description'] = df['Description'].astype(str).str.strip()
        df['Description'] = df['Description'].replace('nan', '')
        print("Description column cleaned")
    
    print("Data cleaning complete")
    return df

if __name__ == "__main__":
    # Example usage
    pdf_file = "bank_statement.pdf"
    
    print("Starting PDF processing...")
    
    # Read PDF
    df = read_pdf_bank_statement(pdf_file)
    
    if df is not None:
        print("\nRaw data from PDF:")
        print(df.head())
        
        # Clean data
        clean_df = clean_pdf_data(df)
        
        print("\nCleaned data:")
        print(clean_df.head())
        
        # Save to CSV for testing with main classifier
        output_file = "pdf_transactions.csv"
        clean_df.to_csv(output_file, index=False)
        print(f"\nSaved cleaned data to {output_file}")
        
        print(f"\nReady to run: python main.py --file {output_file}")
    else:
        print("Failed to read PDF")

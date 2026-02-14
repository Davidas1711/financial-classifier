import pandas as pd
import re
import json
import difflib

# Pre-compiled regex patterns for performance
WHITESPACE_PATTERN = re.compile(r'\s+')
CURRENCY_PATTERN = re.compile(r'[$,€£¥]')


class DataCleaner:
    def __init__(self, config_path="../config/mapping.json"):
        self.config = self._load_config(config_path)
        
    def _load_config(self, config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    def clean_data(self, df, date_col=None, desc_col=None, amount_col=None):
        """
        Clean and standardize transaction data
        """
        cleaned_df = df.copy()
        
        # Try to infer column names if not provided
        if not all([date_col, desc_col, amount_col]):
            date_col, desc_col, amount_col = self._infer_columns(cleaned_df)
        
        # Clean dates
        cleaned_df = self._clean_dates(cleaned_df, date_col)
        
        # Clean descriptions
        cleaned_df = self._clean_descriptions(cleaned_df, desc_col)
        
        # Clean amounts
        cleaned_df = self._clean_amounts(cleaned_df, amount_col)
        
        # Apply PII masking if enabled
        if self.config['settings']['private_mode']:
            cleaned_df = self._mask_pii(cleaned_df, desc_col)
        
        return cleaned_df
    
    def _infer_columns(self, df):
        """
        Infer which columns represent date, description, and amount
        """
        columns = df.columns.str.lower()
        
        # Find date column
        date_col = None
        date_keywords = ['date', 'transaction date', 'trans date', 'posted date', 'time']
        for col in columns:
            if any(keyword in col for keyword in date_keywords):
                date_col = df.columns[columns.get_loc(col)]
                break
        
        # Find description column
        desc_col = None
        desc_keywords = ['description', 'merchant', 'payee', 'transaction', 'details', 'memo']
        for col in columns:
            if any(keyword in col for keyword in desc_keywords):
                desc_col = df.columns[columns.get_loc(col)]
                break
        
        # Find amount column
        amount_col = None
        amount_keywords = ['amount', 'value', 'debit', 'credit', 'transaction amount']
        for col in columns:
            if any(keyword in col for keyword in amount_keywords):
                amount_col = df.columns[columns.get_loc(col)]
                break
        
        # Fallback to first columns if inference fails
        if not date_col and len(df.columns) > 0:
            date_col = df.columns[0]
        if not desc_col and len(df.columns) > 1:
            desc_col = df.columns[1]
        if not amount_col and len(df.columns) > 2:
            amount_col = df.columns[2]
        
        return date_col, desc_col, amount_col
    
    def _clean_dates(self, df, date_col):
        """
        Standardize date formats with flexible parsing for international formats
        """
        if date_col not in df.columns:
            return df
        
        # Try multiple date formats commonly used internationally
        date_formats = [
            '%Y-%m-%d',    # 2024-01-15 (ISO)
            '%m/%d/%Y',    # 01/15/2024 (US)
            '%d/%m/%Y',    # 15/01/2024 (European)
            '%Y.%m.%d',    # 2024.01.15 (German)
            '%d %b %Y',    # 15 Jan 2024 (UK)
            '%b %d, %Y',   # Jan 15, 2024 (US)
            '%Y/%m/%d',    # 2024/01/15 (Asian)
            '%d-%m-%Y',    # 15-01-2024 (European)
            '%m-%d-%Y',    # 01-15-2024 (US alternative)
        ]
        
        # Try each format until one works
        for fmt in date_formats:
            try:
                df[date_col] = pd.to_datetime(df[date_col], format=fmt, errors='coerce')
                # Check if we successfully parsed most dates
                if df[date_col].notna().sum() > len(df) * 0.8:  # 80% success rate
                    break
            except:
                continue
        
        # If no format worked well, let pandas try automatically
        if df[date_col].isna().sum() > len(df) * 0.2:  # More than 20% failed
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        # Format as YYYY-MM-DD for consistency
        df[date_col] = df[date_col].dt.strftime('%Y-%m-%d')
        
        return df
    
    def _clean_descriptions(self, df, desc_col):
        """
        Clean and standardize merchant descriptions
        """
        if desc_col not in df.columns:
            return df
        
        # Convert to string and handle NaN
        df[desc_col] = df[desc_col].astype(str)
        
        # Remove extra whitespace
        df[desc_col] = df[desc_col].str.strip()
        
        # Remove common prefixes/suffixes
        patterns_to_remove = [
            r'^POS\s*',  # Point of Sale
            r'^ACH\s*',  # ACH transactions
            r'^DC\s*',   # Debit Card
            r'^CC\s*',   # Credit Card
            r'\s*#\d+$',  # Transaction numbers at end
            r'\s*\*\d+$',  # Starred numbers at end
        ]
        
        for pattern in patterns_to_remove:
            df[desc_col] = df[desc_col].str.replace(pattern, '', regex=True)
        
        # Standardize case (title case for readability)
        df[desc_col] = df[desc_col].str.title()
        
        # Remove multiple spaces (using pre-compiled pattern)
        df[desc_col] = df[desc_col].str.replace(WHITESPACE_PATTERN, ' ', regex=True)
        
        return df
    
    def _clean_amounts(self, df, amount_col):
        """
        Clean and standardize amount values
        """
        if amount_col not in df.columns:
            return df
        
        # Convert to string first to handle various formats
        df[amount_col] = df[amount_col].astype(str)
        
        # Remove currency symbols and commas (using pre-compiled pattern)
        df[amount_col] = df[amount_col].str.replace(CURRENCY_PATTERN, '', regex=True)
        
        # Handle parentheses for negative numbers (e.g., (100.00) = -100.00)
        df[amount_col] = df[amount_col].str.replace(r'^\((.*?)\)$', r'-\1', regex=True)
        
        # Convert to float
        df[amount_col] = pd.to_numeric(df[amount_col], errors='coerce')
        
        return df
    
    def _mask_pii(self, df, desc_col):
        """
        Mask personally identifiable information in descriptions
        """
        if desc_col not in df.columns:
            return df
        
        def mask_sensitive_info(text):
            if pd.isna(text) or text == 'nan':
                return text
            
            text = str(text)
            
            # Mask account numbers (sequences of 8+ digits)
            text = re.sub(r'\b(\d{4})\d{4,}(\d{4})\b', r'\1****\2', text)
            
            # Mask phone numbers
            text = re.sub(r'\b(\d{3})\d{3,}(\d{4})\b', r'\1****\2', text)
            
            # Mask email addresses
            text = re.sub(r'\b([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b', 
                         r'****@\2', text)
            
            # Mask names (simple heuristic - capitalize words that look like names)
            # This is very basic and may need refinement
            words = text.split()
            masked_words = []
            for word in words:
                if len(word) > 2 and word[0].isupper() and word[1:].islower():
                    if len(word) <= 4:
                        masked_words.append(word[0] + '*' * (len(word) - 1))
                    else:
                        masked_words.append(word[:2] + '*' * (len(word) - 2))
                else:
                    masked_words.append(word)
            
            return ' '.join(masked_words)
        
        df[desc_col] = df[desc_col].apply(mask_sensitive_info)
        
        return df
    
    def standardize_merchant_names(self, df, desc_col):
        """
        Standardize merchant names using fuzzy matching
        """
        if desc_col not in df.columns:
            return df
        
        # Get unique merchant names
        unique_merchants = df[desc_col].dropna().unique()
        
        # Create mapping for similar names
        merchant_mapping = {}
        
        for i, merchant1 in enumerate(unique_merchants):
            if merchant1 in merchant_mapping:
                continue
                
            for j, merchant2 in enumerate(unique_merchants[i+1:], i+1):
                similarity = difflib.SequenceMatcher(None, merchant1.lower(), merchant2.lower()).ratio()
                
                if similarity >= self.config['settings']['fuzzy_match_threshold']:
                    # Use the shorter, cleaner name as the standard
                    if len(merchant2) < len(merchant1) or merchant2.count(' ') < merchant1.count(' '):
                        merchant_mapping[merchant1] = merchant2
                    else:
                        merchant_mapping[merchant2] = merchant1
        
        # Apply mapping
        df[desc_col] = df[desc_col].replace(merchant_mapping)
        
        return df

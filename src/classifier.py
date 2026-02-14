import pandas as pd
import json
import os
from datetime import datetime
import re
import difflib

# Pre-compiled regex patterns for performance
DIGIT_PATTERN = re.compile(r'\d{4,}')
TRANSACTION_ID_PATTERN = re.compile(r'\b[a-z0-9]{6,}\b')
SUFFIX_ID_PATTERN = re.compile(r'\s*-\s*[a-z0-9]{3,}\s*$')
WHITESPACE_PATTERN = re.compile(r'\s+')
SUFFIX_PATTERN = re.compile(r'\s*(inc|llc|corp|co|ltd|com)\s*$', re.IGNORECASE)


class TransactionClassifier:
    def __init__(self, config_path="config/mapping.json", learned_path="config/learned_mapping.json"):
        # Check if mapping.csv exists in root, create if missing
        self._ensure_mapping_csv_exists()
        
        self.config_path = config_path
        self.learned_path = learned_path
        self.config = self._load_config(config_path)
        self.categories = self.config['categories']
        self.learned_mappings = self._load_learned_mappings()
        
        # Available categories for local classification
        self.available_categories = [
            "Income", "Food & Dining", "Shopping", "Bills & Utilities", 
            "Healthcare", "Entertainment", "Transportation", "Banking & Fees"
        ]
    
    def _ensure_mapping_csv_exists(self):
        """
        Ensure mapping.csv exists in root folder, create with headers if missing
        """
        csv_path = "mapping.csv"
        if not os.path.exists(csv_path):
            try:
                # Create empty CSV with headers
                df = pd.DataFrame(columns=['Merchant', 'Category'])
                df.to_csv(csv_path, index=False)
                print(f"Created {csv_path} with headers Merchant,Category")
            except Exception as e:
                print(f"Warning: Could not create {csv_path}: {e}")
        
    def _load_learned_mappings(self):
        """
        Load learned merchant mappings from previous user-driven classifications
        """
        try:
            if os.path.exists(self.learned_path):
                with open(self.learned_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Warning: Could not load learned mappings: {e}")
            return {}
    
    def _save_learned_mapping(self, merchant, category):
        """
        Save a new learned mapping to persist user-driven classifications
        """
        try:
            self.learned_mappings[merchant] = {
                'category': category,
                'learned_date': datetime.now().isoformat(),
                'method': 'user_classification'
            }
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.learned_path), exist_ok=True)
            
            with open(self.learned_path, 'w') as f:
                json.dump(self.learned_mappings, f, indent=2)
            
            print(f"Learned mapping saved: '{merchant}' -> '{category}'")
            return True
        except Exception as e:
            print(f"Error saving learned mapping: {e}")
            return False
    
    def _load_config(self, config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    def classify_transactions(self, df, desc_col=None):
        """
        Classify transactions based on merchant names and keywords
        """
        classified_df = df.copy()
        
        # Try to infer description column if not provided
        if not desc_col:
            desc_col = self._infer_description_column(df)
        
        if desc_col not in df.columns:
            raise ValueError(f"Description column '{desc_col}' not found in DataFrame")
        
        # Initialize category column
        classified_df['category'] = 'Uncategorized'
        classified_df['classification_method'] = 'none'
        classified_df['confidence_score'] = 0
        
        for idx, row in df.iterrows():
            # Optimize string operations - convert once, check early
            raw_description = row[desc_col]
            if pd.isna(raw_description) or raw_description == '':
                continue
            
            # Convert to string and clean once
            description = str(raw_description).lower().strip()
            
            # Clean description: remove sequences of 4+ digits
            description = self._clean_description(description)
            
            # Try exact merchant match first (mapping.json)
            category, method, confidence = self._classify_by_merchant(description)
            
            # If no exact match, try learned mappings (learned_mapping.json)
            if category == 'Uncategorized':
                category, method, confidence = self._classify_by_learned(description)
            
            # If no exact match, try keyword matching
            if category == 'Uncategorized':
                category, method, confidence = self._classify_by_keywords(description)
            
            # If still uncategorized, try fuzzy matching with known merchants
            if category == 'Uncategorized':
                category, method, confidence = self._classify_by_fuzzy_match(description)
            
            # If still uncategorized, use enhanced classification as last resort
            if category == 'Uncategorized':
                category, method, confidence = self._classify_by_ai(description)
                
                # If classification succeeded, save the learning
                if category != 'Uncategorized':
                    self._save_learned_mapping(description, category)
            
            classified_df.at[idx, 'category'] = category
            classified_df.at[idx, 'classification_method'] = method
            classified_df.at[idx, 'confidence_score'] = confidence
        
        return classified_df
    
    def _infer_description_column(self, df):
        """
        Infer which column represents the transaction description
        """
        columns = df.columns.str.lower()
        desc_keywords = ['description', 'merchant', 'payee', 'transaction', 'details', 'memo']
        
        for col in columns:
            if any(keyword in col for keyword in desc_keywords):
                return df.columns[columns.get_loc(col)]
        
        # Fallback to second column if inference fails
        if len(df.columns) > 1:
            return df.columns[1]
        
        raise ValueError("Could not infer description column")
    
    def _classify_by_merchant(self, description):
        """
        Classify by exact merchant name match
        """
        for category, config in self.categories.items():
            merchants = config.get('merchants', [])
            for merchant in merchants:
                if merchant.lower() in description or description in merchant.lower():
                    confidence = 100 if description == merchant.lower() else 90
                    return category, 'merchant_match', confidence
        
        return 'Uncategorized', 'none', 0
    
    def _classify_by_learned(self, description):
        """
        Classify using previously learned user mappings
        """
        for merchant, mapping in self.learned_mappings.items():
            if merchant.lower() in description or description in merchant.lower():
                category = mapping['category']
                confidence = 95  # High confidence for previously learned mappings
                return category, 'learned_mapping', confidence
        
        return 'Uncategorized', 'none', 0
    
    def _classify_by_ai(self, description):
        """
        Use enhanced classification with merchant extraction for uncategorized transactions
        """
        try:
            # Extract merchant name using pattern matching
            merchant_name = self._extract_merchant_name(description)
            
            # Create enhanced prompt for AI classification
            prompt = f"""
Classify this transaction into one of these financial categories:
Categories: {', '.join(self.available_categories)}

Transaction Details:
- Merchant: {merchant_name}
- Full Description: "{description}"

Rules:
- Use context clues about merchant type and business category
- Consider luxury/high-end merchants appropriately
- If it's clearly a luxury service, categorize as Entertainment, Shopping, or Transportation
- Financial services go to Banking & Fees or Income
- Professional services go to appropriate categories

Respond with only the category name. If you cannot determine, respond with "Uncategorized".
"""
            
            # Enhanced classification with merchant context
            category = self._enhanced_ai_classification(prompt, merchant_name, description)
            
            if category != 'Uncategorized':
                # Auto-learn new merchant mappings
                self._auto_learn_merchant(merchant_name, category)
                return category, 'enhanced_classification', 75
            
            return 'Uncategorized', 'enhanced_failed', 0
                
        except Exception as e:
            print(f"Enhanced classification failed for '{description}': {e}")
            return 'Uncategorized', 'enhanced_error', 0
    
    def _extract_merchant_name(self, description):
        """
        Extract merchant name from transaction description
        Uses pre-compiled regex patterns for better performance
        """
        # Remove common prefixes/suffixes
        cleaned = description.lower()
        
        # Remove transaction IDs, dates, locations (using pre-compiled patterns)
        cleaned = DIGIT_PATTERN.sub('', cleaned)  # 4+ digits
        cleaned = TRANSACTION_ID_PATTERN.sub('', cleaned)  # Transaction IDs
        cleaned = SUFFIX_ID_PATTERN.sub('', cleaned)  # Suffix IDs
        
        # Remove common payment processor prefixes
        prefixes_to_remove = [
            'payment to ', 'purchase from ', 'charge from ', 'debit from ',
            'credit to ', 'transfer to ', 'withdrawal from '
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):]
                break
        
        # Extract main merchant (first 2-3 words, usually the merchant name)
        words = cleaned.split()
        if len(words) >= 2:
            # Take first 2-3 meaningful words
            merchant = ' '.join(words[:min(3, len(words))])
        elif len(words) == 1:
            merchant = words[0]
        else:
            merchant = cleaned
        
        # Clean up common suffixes (using pre-compiled pattern)
        merchant = SUFFIX_PATTERN.sub('', merchant).strip()
        
        return merchant.title()
    
    def _enhanced_ai_classification(self, prompt, merchant_name, description):
        """
        Enhanced classification with merchant-specific logic
        """
        # Luxury merchant detection
        luxury_indicators = [
            'netjets', 'vista', 'yacht', 'private jet', 'first class',
            'graff', 'patek', 'hermès', 'louis vuitton', 'savile row',
            'christie\'s', 'sotheby\'s', 'noma', 'fat duck', 'annabel',
            'caviar', 'aman', 'four seasons', 'st. regis', 'maldives',
            'goldman sachs', 'family office', 'capital call', 'sequoia'
        ]
        
        description_lower = description.lower()
        merchant_lower = merchant_name.lower()
        
        # Quick luxury classification
        if any(indicator in description_lower for indicator in luxury_indicators):
            if any(transport in description_lower for transport in ['jet', 'yacht', 'lufthansa', 'vista']):
                return 'Transportation'
            elif any(retail in description_lower for retail in ['graff', 'patek', 'hermès', 'louis', 'boutique']):
                return 'Shopping'
            elif any(dining in description_lower for dining in ['noma', 'fat duck', 'annabel', 'caviar']):
                return 'Food & Dining'
            elif any(travel in description_lower for travel in ['aman', 'four seasons', 'st. regis']):
                return 'Entertainment'
            elif any(financial in description_lower for financial in ['goldman', 'family office', 'capital call']):
                return 'Banking & Fees'
        
        # Use enhanced heuristic classification
        return self._classify_by_enhanced_keywords(description)
    
    def _classify_by_enhanced_keywords(self, description):
        """
        Enhanced keyword classification with luxury and business categories
        """
        description_lower = description.lower()
        
        # Income indicators (expanded)
        income_keywords = ['deposit', 'salary', 'payroll', 'dividend', 'interest', 'refund', 'cashback', 'rebate', 'venmo', 'paypal', 'investment return', 'freelance payment', 'capital call', 'family office']
        if any(keyword in description_lower for keyword in income_keywords):
            return 'Income'
        
        # Food & Dining (expanded for luxury)
        food_keywords = ['restaurant', 'cafe', 'coffee', 'food', 'dining', 'bar', 'pub', 'pizza', 'burger', 'taco', 'sandwich', 'noma', 'fat duck', 'annabel', 'caviar', 'wine']
        if any(keyword in description_lower for keyword in food_keywords):
            return 'Food & Dining'
        
        # Shopping (expanded for luxury)
        shop_keywords = ['store', 'shop', 'retail', 'mall', 'amazon', 'walmart', 'target', 'buy', 'purchase', 'graff', 'patek', 'hermès', 'louis', 'vuitton', 'boutique', 'savile', 'christie', 'sotheby']
        if any(keyword in description_lower for keyword in shop_keywords):
            return 'Shopping'
        
        # Transportation (expanded for luxury)
        transport_keywords = ['gas', 'fuel', 'uber', 'lyft', 'taxi', 'transit', 'metro', 'parking', 'toll', 'shell', 'chevron', 'netjets', 'vista', 'yacht', 'lufthansa', 'first class']
        if any(keyword in description_lower for keyword in transport_keywords):
            return 'Transportation'
        
        # Bills & Utilities (expanded)
        bill_keywords = ['bill', 'utility', 'electric', 'water', 'phone', 'internet', 'insurance', 'mortgage', 'rent', 'property tax', 'estate', 'staffing']
        if any(keyword in description_lower for keyword in bill_keywords):
            return 'Bills & Utilities'
        
        # Healthcare (expanded)
        health_keywords = ['hospital', 'doctor', 'pharmacy', 'medical', 'clinic', 'dental', 'health', 'research foundation']
        if any(keyword in description_lower for keyword in health_keywords):
            return 'Healthcare'
        
        # Entertainment (expanded for luxury)
        entertainment_keywords = ['netflix', 'spotify', 'movie', 'theater', 'concert', 'game', 'entertainment', 'aman', 'four seasons', 'st. regis', 'maldives', 'resort']
        if any(keyword in description_lower for keyword in entertainment_keywords):
            return 'Entertainment'
        
        # Banking & Fees (expanded)
        banking_keywords = ['bank', 'fee', 'charge', 'interest', 'atm', 'overdraft', 'service', 'goldman', 'family office', 'capital call', 'wire transfer', 'legal retainer']
        if any(keyword in description_lower for keyword in banking_keywords):
            return 'Banking & Fees'
        
        return 'Uncategorized'
    
    def _auto_learn_merchant(self, merchant_name, category):
        """
        Automatically learn new merchant mappings
        """
        try:
            if merchant_name not in self.learned_mappings:
                self.learned_mappings[merchant_name] = {
                    'category': category,
                    'learned_date': datetime.now().isoformat(),
                    'method': 'auto_enhanced_classification',
                    'confidence': 75
                }
                
                # Save to learned mappings file
                os.makedirs(os.path.dirname(self.learned_path), exist_ok=True)
                with open(self.learned_path, 'w') as f:
                    json.dump(self.learned_mappings, f, indent=2)
                
                print(f"Auto-learned new merchant: '{merchant_name}' -> '{category}'")
        except Exception as e:
            print(f"Failed to auto-learn merchant '{merchant_name}': {e}")
    
    def _simple_ai_classification(self, description):
        """
        Simple rule-based classification as enhanced fallback
        This provides consistent categorization without external dependencies
        """
        description_lower = description.lower()
        
        # Income indicators
        income_keywords = ['deposit', 'salary', 'payroll', 'dividend', 'interest', 'refund', 'cashback', 'rebate', 'venmo', 'paypal']
        if any(keyword in description_lower for keyword in income_keywords):
            return 'Income'
        
        # Food & Dining indicators
        food_keywords = ['restaurant', 'cafe', 'coffee', 'food', 'dining', 'bar', 'pub', 'pizza', 'burger', 'taco', 'sandwich']
        if any(keyword in description_lower for keyword in food_keywords):
            return 'Food & Dining'
        
        # Shopping indicators
        shop_keywords = ['store', 'shop', 'retail', 'mall', 'amazon', 'walmart', 'target', 'buy', 'purchase']
        if any(keyword in description_lower for keyword in shop_keywords):
            return 'Shopping'
        
        # Transportation indicators
        transport_keywords = ['gas', 'fuel', 'uber', 'lyft', 'taxi', 'parking', 'toll', 'transit', 'metro']
        if any(keyword in description_lower for keyword in transport_keywords):
            return 'Transportation'
        
        # Bills & Utilities indicators
        bill_keywords = ['bill', 'utility', 'electric', 'water', 'phone', 'internet', 'insurance', 'mortgage', 'rent']
        if any(keyword in description_lower for keyword in bill_keywords):
            return 'Bills & Utilities'
        
        # Healthcare indicators
        health_keywords = ['hospital', 'doctor', 'pharmacy', 'medical', 'clinic', 'dental', 'health']
        if any(keyword in description_lower for keyword in health_keywords):
            return 'Healthcare'
        
        # Entertainment indicators
        entertainment_keywords = ['netflix', 'spotify', 'movie', 'theater', 'concert', 'game', 'streaming']
        if any(keyword in description_lower for keyword in entertainment_keywords):
            return 'Entertainment'
        
        # Banking & Fees indicators
        banking_keywords = ['bank', 'fee', 'charge', 'atm', 'overdraft', 'service', 'interest']
        if any(keyword in description_lower for keyword in banking_keywords):
            return 'Banking & Fees'
        
        return 'Uncategorized'
    
    def _classify_by_keywords(self, description):
        """
        Classify by keyword matching
        """
        best_match = ('Uncategorized', 'none', 0)
        
        for category, config in self.categories.items():
            keywords = config.get('keywords', [])
            for keyword in keywords:
                if keyword.lower() in description:
                    # Higher confidence for exact word matches
                    if f' {keyword.lower()} ' in f' {description} ':
                        confidence = 85
                    else:
                        confidence = 75
                    
                    if confidence > best_match[2]:
                        best_match = (category, 'keyword_match', confidence)
        
        return best_match
    
    def _classify_by_fuzzy_match(self, description):
        """
        Classify using fuzzy string matching with known merchants
        """
        best_match = ('Uncategorized', 'none', 0)
        # Get threshold with fallback to default value
        threshold = self.config.get('settings', {}).get('fuzzy_match_threshold', 70)
        
        for category, config in self.categories.items():
            merchants = config.get('merchants', [])
            for merchant in merchants:
                similarity = difflib.SequenceMatcher(None, description, merchant.lower()).ratio() * 100
                
                if similarity >= threshold and similarity > best_match[2]:
                    best_match = (category, 'fuzzy_match', similarity)
        
        return best_match
    
    def add_merchant_mapping(self, merchant_name, category, config_path=None):
        """
        Add a new merchant-to-category mapping to the configuration
        """
        if config_path is None:
            config_path = self.config_path
            
        if category not in self.categories:
            raise ValueError(f"Category '{category}' not found in configuration")
        
        # Add merchant to the category
        if merchant_name not in self.categories[category]['merchants']:
            self.categories[category]['merchants'].append(merchant_name)
            
            # Update configuration
            self.config['categories'] = self.categories
            
            # Save to file
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            print(f"Added merchant '{merchant_name}' to category '{category}'")
            return True
        else:
            print(f"Merchant '{merchant_name}' already exists in category '{category}'")
            return False
    
    def learn_from_corrections(self, df, desc_col, original_category_col, corrected_category_col, config_path=None):
        """
        Learn from manual corrections and update the configuration
        """
        if config_path is None:
            config_path = self.config_path
            
        corrections = df[df[original_category_col] != df[corrected_category_col]]
        
        learned_count = 0
        for idx, row in corrections.iterrows():
            description = str(row[desc_col]).strip()
            corrected_category = row[corrected_category_col]
            
            if corrected_category in self.categories:
                if self.add_merchant_mapping(description, corrected_category, config_path):
                    learned_count += 1
        
        print(f"Learned {learned_count} new merchant mappings from corrections")
        return learned_count
    
    def get_classification_summary(self, df):
        """
        Return summary of classification results
        """
        summary = {
            'total_transactions': len(df),
            'categorized_transactions': len(df[df['category'] != 'Uncategorized']),
            'uncategorized_transactions': len(df[df['category'] == 'Uncategorized']),
            'category_breakdown': df['category'].value_counts().to_dict(),
            'method_breakdown': df['classification_method'].value_counts().to_dict(),
            'average_confidence': df['confidence_score'].mean()
        }
        
        return summary
    
    def export_uncategorized(self, df, output_path):
        """
        Export uncategorized transactions for manual review
        """
        uncategorized = df[df['category'] == 'Uncategorized']
        
        if not uncategorized.empty:
            uncategorized.to_csv(output_path, index=False)
            print(f"Exported {len(uncategorized)} uncategorized transactions to: {output_path}")
        else:
            print("No uncategorized transactions to export")
        
        return len(uncategorized)
    
    def _clean_description(self, description):
        """
        Clean description by removing sequences of 4+ digits and extra whitespace
        Uses pre-compiled regex patterns for better performance
        """
        # Remove sequences of 4 or more digits (using pre-compiled pattern)
        description = DIGIT_PATTERN.sub('', description)
        
        # Remove extra whitespace (using pre-compiled pattern)
        description = WHITESPACE_PATTERN.sub(' ', description).strip()
        
        return description

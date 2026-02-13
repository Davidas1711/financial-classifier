import pandas as pd
import json
from thefuzz import fuzz
import os
import requests
from datetime import datetime
import re


class TransactionClassifier:
    def __init__(self, config_path="../config/mapping.json", learned_path="../config/learned_mapping.json"):
        self.config = self._load_config(config_path)
        self.categories = self.config['categories']
        self.learned_path = learned_path
        self.learned_mappings = self._load_learned_mappings()
        
        # Available categories for AI classification
        self.available_categories = [
            "Income", "Food & Dining", "Shopping", "Bills & Utilities", 
            "Healthcare", "Entertainment", "Transportation", "Banking & Fees"
        ]
        
    def _load_learned_mappings(self):
        """
        Load learned merchant mappings from previous AI classifications
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
        Save a new learned mapping to persist AI classifications
        """
        try:
            self.learned_mappings[merchant] = {
                'category': category,
                'learned_date': datetime.now().isoformat(),
                'method': 'ai_classification'
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
            description = str(row[desc_col]).lower().strip()
            
            if description == 'nan' or not description:
                continue
            
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
            
            # If still uncategorized, use AI classification as last resort
            if category == 'Uncategorized':
                category, method, confidence = self._classify_by_ai(description)
                
                # If AI successfully classified, save the learning
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
        Classify using previously learned AI mappings
        """
        for merchant, mapping in self.learned_mappings.items():
            if merchant.lower() in description or description in merchant.lower():
                category = mapping['category']
                confidence = 95  # High confidence for previously learned mappings
                return category, 'learned_mapping', confidence
        
        return 'Uncategorized', 'none', 0
    
    def _classify_by_ai(self, description):
        """
        Use AI to classify uncategorized transactions
        """
        try:
            # Create prompt for AI
            prompt = f"""
Classify this merchant name into one of these financial categories:
Categories: {', '.join(self.available_categories)}

Merchant Name: "{description}"

Respond with only the category name. If you cannot determine the category, respond with "Uncategorized".
"""
            
            # Note: This is a placeholder for AI integration
            # You would replace this with your preferred LLM API call
            # For now, we'll use a simple rule-based approach as fallback
            
            # Simple heuristic-based AI fallback
            category = self._simple_ai_classification(description)
            
            if category != 'Uncategorized':
                return category, 'ai_classification', 70
            else:
                return 'Uncategorized', 'ai_failed', 0
                
        except Exception as e:
            print(f"AI classification failed for '{description}': {e}")
            return 'Uncategorized', 'ai_error', 0
    
    def _simple_ai_classification(self, description):
        """
        Simple rule-based classification as AI fallback
        This can be replaced with actual LLM API calls
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
        threshold = self.config['settings']['fuzzy_match_threshold']
        
        for category, config in self.categories.items():
            merchants = config.get('merchants', [])
            for merchant in merchants:
                similarity = fuzz.ratio(description, merchant.lower())
                
                if similarity >= threshold and similarity > best_match[2]:
                    best_match = (category, 'fuzzy_match', similarity)
        
        return best_match
    
    def add_merchant_mapping(self, merchant_name, category, config_path="../config/mapping.json"):
        """
        Add a new merchant-to-category mapping to the configuration
        """
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
    
    def learn_from_corrections(self, df, desc_col, original_category_col, corrected_category_col, config_path="../config/mapping.json"):
        """
        Learn from manual corrections and update the configuration
        """
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
        """
        # Remove sequences of 4 or more digits
        description = re.sub(r'\d{4,}', '', description)
        
        # Remove extra whitespace
        description = re.sub(r'\s+', ' ', description).strip()
        
        return description

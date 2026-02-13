import pandas as pd
import json
from thefuzz import fuzz
import os


class TransactionClassifier:
    def __init__(self, config_path="../config/mapping.json"):
        self.config = self._load_config(config_path)
        self.categories = self.config['categories']
        
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
            
            # Try exact merchant match first
            category, method, confidence = self._classify_by_merchant(description)
            
            # If no exact match, try keyword matching
            if category == 'Uncategorized':
                category, method, confidence = self._classify_by_keywords(description)
            
            # If still uncategorized, try fuzzy matching with known merchants
            if category == 'Uncategorized':
                category, method, confidence = self._classify_by_fuzzy_match(description)
            
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

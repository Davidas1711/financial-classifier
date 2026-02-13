import pandas as pd
from datetime import datetime, timedelta
import json
import os


class DataValidator:
    def __init__(self, config_path="../config/mapping.json"):
        self.config = self._load_config(config_path)
        self.validation_errors = []
        
    def _load_config(self, config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    def validate_data(self, df, date_col=None, desc_col=None, amount_col=None):
        """
        Validate transaction data and return cleaned DataFrame with errors flagged
        """
        validated_df = df.copy()
        
        # Try to infer column names if not provided
        if not all([date_col, desc_col, amount_col]):
            date_col, desc_col, amount_col = self._infer_columns(df)
        
        # Initialize validation columns
        validated_df['validation_error'] = ''
        validated_df['error_type'] = ''
        
        for idx, row in df.iterrows():
            errors = []
            error_types = []
            
            # Check for missing values
            if pd.isna(row.get(date_col)) or str(row.get(date_col)).strip() == '':
                errors.append(f"Missing {date_col}")
                error_types.append("missing_date")
            
            if pd.isna(row.get(desc_col)) or str(row.get(desc_col)).strip() == '':
                errors.append(f"Missing {desc_col}")
                error_types.append("missing_description")
            
            if pd.isna(row.get(amount_col)):
                errors.append(f"Missing {amount_col}")
                error_types.append("missing_amount")
            
            # Check amount validity
            try:
                amount = float(row.get(amount_col, 0))
                if amount == 0:
                    errors.append("Amount is $0")
                    error_types.append("zero_amount")
                elif amount > self.config['settings']['max_amount_threshold']:
                    errors.append(f"Amount exceeds ${self.config['settings']['max_amount_threshold']:,}")
                    error_types.append("excessive_amount")
                elif amount < self.config['settings']['min_amount_threshold']:
                    errors.append(f"Amount below ${self.config['settings']['min_amount_threshold']}")
                    error_types.append("negative_amount")
            except (ValueError, TypeError):
                errors.append("Invalid amount format")
                error_types.append("invalid_amount")
            
            # Check date validity
            try:
                date_val = pd.to_datetime(row.get(date_col))
                today = datetime.now()
                min_date = today - timedelta(days=self.config['settings']['date_range_years'] * 365)
                
                if date_val > today:
                    errors.append("Future date")
                    error_types.append("future_date")
                elif date_val < min_date:
                    errors.append(f"Date older than {self.config['settings']['date_range_years']} years")
                    error_types.append("ancient_date")
            except (ValueError, TypeError):
                errors.append("Invalid date format")
                error_types.append("invalid_date")
            
            # Store errors
            if errors:
                validated_df.at[idx, 'validation_error'] = '; '.join(errors)
                validated_df.at[idx, 'error_type'] = '; '.join(error_types)
                self.validation_errors.append({
                    'row_index': idx,
                    'errors': errors,
                    'error_types': error_types,
                    'data': row.to_dict()
                })
        
        return validated_df
    
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
    
    def get_validation_summary(self):
        """
        Return summary of validation errors
        """
        if not self.validation_errors:
            return {"total_errors": 0, "error_types": {}}
        
        error_counts = {}
        for error in self.validation_errors:
            for error_type in error['error_types']:
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        return {
            "total_errors": len(self.validation_errors),
            "error_types": error_counts,
            "errors": self.validation_errors
        }
    
    def save_validation_errors(self, output_path):
        """
        Save validation errors to CSV
        """
        if self.validation_errors:
            error_df = pd.DataFrame(self.validation_errors)
            error_df.to_csv(output_path, index=False)
            print(f"Validation errors saved to: {output_path}")
        else:
            print("No validation errors to save.")

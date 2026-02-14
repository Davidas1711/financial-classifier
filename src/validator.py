import pandas as pd
from datetime import datetime, timedelta
import json
import os


class DataValidator:
    def __init__(self, mapping_path="../config/mapping.json", settings_path="../config/settings.json", validation_path="../config/validation_rules.json"):
        self.mapping_config = self._load_config(mapping_path)
        self.settings_config = self._load_config(settings_path)
        self.validation_config = self._load_config(validation_path)
        self.validation_errors = []
        
    def _load_config(self, config_path):
        try:
            if not os.path.exists(config_path):
                # Use logging instead of print for better CLI integration
                import logging
                logging.getLogger(__name__).warning(f"Config file not found: {config_path}")
                return {}
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error loading config {config_path}: {e}")
            return {}
    
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
            
            # Check amount validity using 3-tier validation
            try:
                amount = float(row.get(amount_col, 0))
                description = str(row.get(desc_col, '')).lower().strip()
                
                # Tier 1: Merchant-specific validation
                merchant_violation = self._validate_merchant_range(description, amount)
                if merchant_violation:
                    errors.append(merchant_violation)
                    error_types.append("merchant_range_violation")
                
                # Tier 2: Category threshold validation
                category_violation = self._validate_category_threshold(description, amount)
                if category_violation:
                    errors.append(category_violation)
                    error_types.append("category_threshold_violation")
                
                # Tier 3: Global limits validation
                global_violation = self._validate_global_limits(amount)
                if global_violation:
                    errors.append(global_violation)
                    error_types.append("global_limit_violation")
                
                # Tier 4: AI sanity check for outliers
                ai_config = self.settings_config.get('ai_sanction_check', {})
                if ai_config.get('enabled', False):
                    ai_violation = self._ai_sanity_check(description, amount, row.get('category', ''))
                    if ai_violation:
                        errors.append(ai_violation)
                        error_types.append("ai_outlier_flag")
                        
            except (ValueError, TypeError):
                errors.append("Invalid amount format")
                error_types.append("invalid_amount")
            
            # Check date validity
            try:
                date_val = pd.to_datetime(row.get(date_col))
                today = datetime.now()
                date_range = self.settings_config.get('global_limits', {}).get('date_range_years', 5)
                min_date = today - timedelta(days=date_range * 365)
                
                if date_val > today:
                    errors.append("Future date")
                    error_types.append("future_date")
                elif date_val < min_date:
                    errors.append(f"Date older than {date_range} years")
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
    
    def _validate_merchant_range(self, description, amount):
        """
        Tier 1: Validate against merchant-specific price ranges
        """
        merchant_ranges = self.validation_config.get('merchant_ranges', {})
        
        for merchant, rules in merchant_ranges.items():
            if merchant.lower() in description or description in merchant.lower():
                min_amount = rules.get('min_amount', 0)
                max_amount = rules.get('max_amount', float('inf'))
                
                if amount < min_amount:
                    return f"Amount ${amount:.2f} below minimum for {merchant} (${min_amount:.2f})"
                elif amount > max_amount:
                    return f"Amount ${amount:.2f} above maximum for {merchant} (${max_amount:.2f})"
        
        return None
    
    def _validate_category_threshold(self, description, amount):
        """
        Tier 2: Validate against category thresholds
        """
        category_thresholds = self.settings_config.get('category_thresholds', {})
        
        # Try to determine category from merchant mapping
        category = self._get_category_for_merchant(description)
        
        if category and category in category_thresholds:
            threshold = category_thresholds[category]
            min_amount = threshold.get('min_amount', 0)
            max_amount = threshold.get('max_amount', float('inf'))
            
            if amount < min_amount:
                return f"Amount ${amount:.2f} below {category} minimum (${min_amount:.2f})"
            elif amount > max_amount:
                return f"Amount ${amount:.2f} above {category} maximum (${max_amount:.2f})"
        
        return None
    
    def _validate_global_limits(self, amount):
        """
        Tier 3: Validate against global limits with dynamic thresholds
        """
        global_limits = self.settings_config.get('global_limits', {})
        
        min_threshold = global_limits.get('min_amount_threshold', 0)
        max_threshold = global_limits.get('max_amount_threshold', 10000)
        zero_flag = global_limits.get('zero_amount_flag', True)
        
        # Dynamic threshold adjustment for large transactions
        # Real estate, business investments, etc. can be very large
        if amount > 100000:  # $100k+ transactions
            # Allow very large amounts but still flag extreme outliers
            max_threshold = max(max_threshold, 10000000)  # $10M max
        elif amount > 50000:  # $50k+ transactions
            max_threshold = max(max_threshold, 1000000)   # $1M max
        elif amount > 10000:  # $10k+ transactions
            max_threshold = max(max_threshold, 100000)    # $100k max
        
        if zero_flag and amount == 0:
            return "Amount is $0"
        elif amount < min_threshold:
            return f"Amount ${amount:.2f} below global minimum (${min_threshold:.2f})"
        elif amount > max_threshold:
            return f"Amount ${amount:.2f} exceeds global maximum (${max_threshold:.2f})"
        
        return None
    
    def _ai_sanity_check(self, description, amount, category):
        """
        Tier 4: AI sanity check for outliers using LLM
        Handles both monthly and yearly subscriptions
        """
        ai_config = self.validation_config.get('ai_sanity_check', {})
        
        if not ai_config.get('enabled', False):
            return self._fallback_sanity_check(description, amount, category)
        
        # Check if amount is outside normal merchant range
        merchant_rule = self._get_merchant_rule(description)
        if merchant_rule:
            min_amount = merchant_rule.get('min_amount', 0)
            max_amount = merchant_rule.get('max_amount', float('inf'))
            billing_cycles = merchant_rule.get('billing_cycles', ['monthly'])
            
            # Handle yearly subscriptions
            outlier_multiplier = ai_config.get('outlier_multiplier', 3.0)
            yearly_multiplier = ai_config.get('yearly_multiplier', 12.0)
            
            # Check if this might be a yearly subscription
            if 'yearly' in billing_cycles:
                yearly_max = max_amount * yearly_multiplier
                if amount <= yearly_max:
                    # This is likely a valid yearly subscription
                    return None
                elif amount > yearly_max * outlier_multiplier:
                    return self._llm_anomaly_check(description, amount, merchant_rule, yearly_max, "yearly")
            
            # Check monthly anomalies
            if amount > max_amount * outlier_multiplier:
                return self._llm_anomaly_check(description, amount, merchant_rule, max_amount, "monthly")
            elif amount < min_amount / outlier_multiplier and min_amount > 0:
                return self._llm_anomaly_check(description, amount, merchant_rule, min_amount, "monthly")
        
        # Check category-level anomalies
        category_rule = self.validation_config.get('category_thresholds', {}).get(category, {})
        if category_rule:
            cat_max = category_rule.get('max_amount', float('inf'))
            if amount > cat_max * outlier_multiplier:
                return self._llm_anomaly_check(description, amount, category_rule, cat_max, "category")
        
        return None
    
    def _llm_anomaly_check(self, description, amount, rule, expected_max, billing_type="monthly"):
        """
        Use LLM to perform sanity check on anomalous amounts
        """
        try:
            # This is a placeholder for actual LLM integration
            # Replace with your preferred LLM API (OpenAI, Claude, etc.)
            
            merchant_name = rule.get('description', description)
            typical_range = rule.get('typical_range', 'unknown')
            
            # Simulate LLM response for demonstration
            if billing_type == "yearly":
                if amount > expected_max * 5:
                    return f"AI: Anomalous Yearly Amount - ${amount:.2f} for {merchant_name} (typical yearly: {typical_range})"
                elif amount > expected_max * 3:
                    return f"AI: Suspicious Yearly Amount - ${amount:.2f} for {merchant_name} (typical yearly: {typical_range})"
            else:
                if amount > expected_max * 5:
                    return f"AI: Anomalous Amount for Merchant - ${amount:.2f} for {merchant_name} (typical: {typical_range})"
                elif amount > expected_max * 3:
                    return f"AI: Suspicious Amount for Merchant - ${amount:.2f} for {merchant_name} (typical: {typical_range})"
            
            return None
                
        except Exception as e:
            print(f"LLM sanity check failed: {e}")
            return f"AI Sanity Check Failed - Amount ${amount:.2f} for {description}"
    
    def _fallback_sanity_check(self, description, amount, category):
        """
        Fallback heuristic-based sanity check when AI is disabled
        """
        # Check for unusually high amounts for common merchants
        high_value_merchants = ['starbucks', 'mcdonalds', 'subway', 'taco bell', 'spotify', 'netflix']
        if any(merchant in description for merchant in high_value_merchants) and amount > 100:
            return f"Unusually high amount ${amount:.2f} for {description}"
        
        # Check for round numbers that might indicate errors
        if amount > 1000 and amount == round(amount):
            return f"Large round number ${amount:.2f} may indicate error"
        
        return None
    
    def _get_merchant_rule(self, description):
        """
        Get merchant-specific rule for validation
        """
        merchant_ranges = self.validation_config.get('merchant_ranges', {})
        
        for merchant, rule in merchant_ranges.items():
            if merchant.lower() in description or description in merchant.lower():
                return rule
        
        return None
    
    def _get_category_for_merchant(self, description):
        """
        Helper method to determine category for a merchant
        """
        merchant_ranges = self.validation_config.get('merchant_ranges', {})
        
        for merchant, rules in merchant_ranges.items():
            if merchant.lower() in description or description in merchant.lower():
                return rules.get('category')
        
        return None
